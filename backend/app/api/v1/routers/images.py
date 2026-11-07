"""Product photos: staff and admin."""

from typing import Annotated

from fastapi import APIRouter, Depends, File, Request, UploadFile, status

from app.api.deps import CurrentEmployee, SessionDep, get_current_employee
from app.schemas.product import ImageRead, ImageUpdate
from app.services import images as service

router = APIRouter(
    prefix="/products/{product_id}/images",
    tags=["images"],
    dependencies=[Depends(get_current_employee)],
)


@router.post("", status_code=status.HTTP_201_CREATED)
async def upload_images(
    request: Request,
    product_id: int,
    session: SessionDep,
    employee: CurrentEmployee,
    files: Annotated[list[UploadFile], File(description="JPEG, PNG or WebP, up to 5 MB each")],
) -> list[ImageRead]:
    return await service.upload_images(session, product_id, files, employee, request)


@router.patch("/{image_id}")
async def update_image(
    request: Request,
    product_id: int,
    image_id: int,
    data: ImageUpdate,
    session: SessionDep,
    employee: CurrentEmployee,
) -> ImageRead:
    return await service.update_image(session, product_id, image_id, data, employee, request)


@router.delete("/{image_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_image(
    request: Request,
    product_id: int,
    image_id: int,
    session: SessionDep,
    employee: CurrentEmployee,
) -> None:
    await service.delete_image(session, product_id, image_id, employee, request)
