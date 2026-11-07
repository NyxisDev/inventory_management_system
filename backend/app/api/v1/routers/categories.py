"""Categories: read and write for staff and admin."""

from fastapi import APIRouter, Depends, Request, status

from app.api.deps import CurrentEmployee, SessionDep, get_current_employee
from app.schemas.category import CategoryCreate, CategoryRead, CategoryTreeNode, CategoryUpdate
from app.services import categories as service

router = APIRouter(
    prefix="/categories", tags=["categories"], dependencies=[Depends(get_current_employee)]
)


@router.get("")
async def list_categories(session: SessionDep) -> list[CategoryRead]:
    return [CategoryRead.model_validate(c) for c in await service.list_categories(session)]


@router.get("/tree")
async def category_tree(session: SessionDep) -> list[CategoryTreeNode]:
    return service.build_tree(await service.list_categories(session))


@router.get("/{category_id}")
async def get_category(category_id: int, session: SessionDep) -> CategoryRead:
    return CategoryRead.model_validate(await service.get_category(session, category_id))


@router.post("", status_code=status.HTTP_201_CREATED)
async def create_category(
    request: Request, data: CategoryCreate, session: SessionDep, employee: CurrentEmployee
) -> CategoryRead:
    category = await service.create_category(session, data, employee, request)
    return CategoryRead.model_validate(category)


@router.patch("/{category_id}")
async def update_category(
    request: Request,
    category_id: int,
    data: CategoryUpdate,
    session: SessionDep,
    employee: CurrentEmployee,
) -> CategoryRead:
    category = await service.update_category(session, category_id, data, employee, request)
    return CategoryRead.model_validate(category)


@router.delete("/{category_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_category(
    request: Request, category_id: int, session: SessionDep, employee: CurrentEmployee
) -> None:
    await service.delete_category(session, category_id, employee, request)
