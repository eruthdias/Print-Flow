from datetime import date

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import get_current_user
from app.schemas.dashboard import DashboardResponse
from app.services import dashboard_service

router = APIRouter(dependencies=[Depends(get_current_user)])


@router.get("/dashboard", response_model=DashboardResponse)
async def obter_dashboard(
    data_inicio: date | None = None,
    data_fim: date | None = None,
    db: AsyncSession = Depends(get_db),
):
    return await dashboard_service.montar_dashboard(db, data_inicio, data_fim)
