"""Audit log: admin only, read only (no PUT / PATCH / DELETE)."""

from datetime import UTC, date, datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Path, Query, Response
from pydantic import AwareDatetime

from app.api.deps import SessionDep, require_admin
from app.models import AuditAction
from app.schemas.audit import AuditRead
from app.schemas.common import Page, PageNumber, PageSize
from app.services import audit_query as service
from app.services.audit_query import AuditFilters

router = APIRouter(prefix="/audit", tags=["audit"], dependencies=[Depends(require_admin)])

DateFilter = Annotated[
    AwareDatetime | date | None,
    Query(description="A date (whole day, UTC) or a date-time with a time zone"),
]


def _filters(
    employee_id: int | None = None,
    action: AuditAction | None = None,
    entity_type: Annotated[str | None, Query(max_length=50)] = None,
    entity_id: Annotated[str | None, Query(max_length=64)] = None,
    date_from: DateFilter = None,
    date_to: DateFilter = None,
    q: Annotated[str | None, Query(max_length=100, description="Search by employee name")] = None,
) -> AuditFilters:
    return AuditFilters(
        employee_id=employee_id,
        action=action,
        entity_type=entity_type,
        entity_id=entity_id,
        date_from=date_from,
        date_to=date_to,
        q=q,
    )


FiltersDep = Annotated[AuditFilters, Depends(_filters)]


@router.get("")
async def list_audit(
    session: SessionDep, filters: FiltersDep, page: PageNumber = 1, page_size: PageSize = 20
) -> Page[AuditRead]:
    items, total = await service.list_entries(session, filters, page, page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)


@router.get("/export.csv", response_class=Response)
async def export_audit_csv(session: SessionDep, filters: FiltersDep) -> Response:
    content = await service.export_csv(session, filters)
    filename = f"audit-{datetime.now(UTC):%Y%m%d-%H%M%S}.csv"
    return Response(
        content=content.encode("utf-8"),
        media_type="text/csv; charset=utf-8",
        headers={"Content-Disposition": f'attachment; filename="{filename}"'},
    )


@router.get("/entity/{entity_type}/{entity_id}")
async def entity_history(
    session: SessionDep,
    entity_type: Annotated[str, Path(max_length=50)],
    entity_id: Annotated[str, Path(max_length=64)],
    page: PageNumber = 1,
    page_size: PageSize = 50,
) -> Page[AuditRead]:
    filters = AuditFilters(entity_type=entity_type, entity_id=entity_id)
    items, total = await service.list_entries(session, filters, page, page_size)
    return Page(items=items, total=total, page=page, page_size=page_size)
