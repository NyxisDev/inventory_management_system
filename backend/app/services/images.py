"""Product photos: upload, choose the main one, reorder, delete."""

from fastapi import Request, UploadFile
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from starlette.concurrency import run_in_threadpool

from app.models import AuditAction, Employee, Product, ProductImage
from app.schemas.product import ImageRead, ImageUpdate
from app.services import media
from app.services.audit import IMAGE_FIELDS, log_action, snapshot
from app.services.errors import BadRequestError, ConflictError, NotFoundError
from app.services.products import image_read


async def _get_product(session: AsyncSession, product_id: int) -> Product:
    product = await session.get(Product, product_id, with_for_update=True)
    if product is None:
        raise NotFoundError("Product not found")
    return product


async def _read_limited(upload: UploadFile) -> bytes:
    data = await upload.read(media.MAX_UPLOAD_BYTES + 1)
    if len(data) > media.MAX_UPLOAD_BYTES:
        raise BadRequestError("Each image must be at most 5 MB")
    if not data:
        raise BadRequestError("Empty file")
    return data


async def upload_images(
    session: AsyncSession,
    product_id: int,
    files: list[UploadFile],
    actor: Employee,
    request: Request,
) -> list[ImageRead]:
    if not files:
        raise BadRequestError("No files uploaded")
    if len(files) > media.MAX_FILES_PER_REQUEST:
        raise BadRequestError(f"At most {media.MAX_FILES_PER_REQUEST} files per upload")

    # Lock the product row so parallel uploads do not both pick "the first image"
    product = await _get_product(session, product_id)
    existing = (
        await session.scalar(select(func.count()).where(ProductImage.product_id == product.id)) or 0
    )
    if existing + len(files) > media.MAX_IMAGES_PER_PRODUCT:
        raise ConflictError(f"A product can have at most {media.MAX_IMAGES_PER_PRODUCT} images")
    has_main = await session.scalar(
        select(func.count()).where(ProductImage.product_id == product.id, ProductImage.is_main)
    )
    next_order = (
        await session.scalar(
            select(func.max(ProductImage.sort_order)).where(ProductImage.product_id == product.id)
        )
        or 0
    ) + (1 if existing else 0)

    # Validate and convert everything first: nothing is saved if one file is bad
    processed = []
    for upload in files:
        data = await _read_limited(upload)
        processed.append(await run_in_threadpool(media.process_image, data))

    written: list[str] = []
    new_images: list[ProductImage] = []
    try:
        for index, image in enumerate(processed):
            file_path = media.new_file_path(product.id)
            await run_in_threadpool(media.write_image, file_path, image)
            written.append(file_path)
            row = ProductImage(
                product_id=product.id,
                file_path=file_path,
                is_main=not has_main and index == 0,  # the first photo becomes the main one
                sort_order=next_order + index,
            )
            session.add(row)
            new_images.append(row)
        await session.flush()
        for row in new_images:
            await log_action(
                session,
                employee=actor,
                action=AuditAction.create,
                entity_type="product_image",
                entity_id=row.id,
                new_data=snapshot(row, IMAGE_FIELDS),
                label=f"photo of {product.name}",
                request=request,
            )
        await session.commit()
    except Exception:
        await session.rollback()
        for file_path in written:
            await run_in_threadpool(media.delete_image_files, file_path)
        raise
    return [image_read(row) for row in new_images]


async def _get_image(session: AsyncSession, product_id: int, image_id: int) -> ProductImage:
    image = await session.scalar(
        select(ProductImage).where(
            ProductImage.id == image_id, ProductImage.product_id == product_id
        )
    )
    if image is None:
        raise NotFoundError("Image not found")
    return image


async def update_image(
    session: AsyncSession,
    product_id: int,
    image_id: int,
    data: ImageUpdate,
    actor: Employee,
    request: Request,
) -> ImageRead:
    product = await _get_product(session, product_id)
    image = await _get_image(session, product_id, image_id)
    before = snapshot(image, IMAGE_FIELDS)
    if data.is_main and not image.is_main:
        # Unset the old main image first: the partial unique index allows only one
        await session.execute(
            update(ProductImage)
            .where(ProductImage.product_id == product_id, ProductImage.is_main)
            .values(is_main=False)
        )
        await session.flush()
        image.is_main = True
    if data.sort_order is not None:
        image.sort_order = data.sort_order
    await log_action(
        session,
        employee=actor,
        action=AuditAction.update,
        entity_type="product_image",
        entity_id=image.id,
        old_data=before,
        new_data=snapshot(image, IMAGE_FIELDS),
        label=f"photo of {product.name}",
        request=request,
    )
    await session.commit()
    await session.refresh(image)
    return image_read(image)


async def delete_image(
    session: AsyncSession, product_id: int, image_id: int, actor: Employee, request: Request
) -> None:
    product = await _get_product(session, product_id)
    image = await _get_image(session, product_id, image_id)
    file_path = image.file_path
    was_main = image.is_main
    await log_action(
        session,
        employee=actor,
        action=AuditAction.delete,
        entity_type="product_image",
        entity_id=image.id,
        old_data=snapshot(image, IMAGE_FIELDS),
        label=f"photo of {product.name}",
        request=request,
    )
    await session.delete(image)
    await session.flush()
    if was_main:
        # Promote the next photo so the product keeps a main image
        next_image = await session.scalar(
            select(ProductImage)
            .where(ProductImage.product_id == product_id)
            .order_by(ProductImage.sort_order, ProductImage.id)
            .limit(1)
        )
        if next_image is not None:
            next_image.is_main = True
    await session.commit()
    await run_in_threadpool(media.delete_image_files, file_path)
