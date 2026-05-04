import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.project import Provider
from app.schemas.provider import (
    HealthCheckResponse,
    ProviderCreate,
    ProviderResponse,
    ProviderUpdate,
)

router = APIRouter(prefix="/providers", tags=["providers"])


@router.get("", response_model=list[ProviderResponse])
async def list_providers(
    session: AsyncSession = Depends(get_session),
):
    result = await session.execute(select(Provider).order_by(Provider.created_at))
    return result.scalars().all()


@router.post("", response_model=ProviderResponse, status_code=201)
async def create_provider(
    body: ProviderCreate,
    session: AsyncSession = Depends(get_session),
):
    provider = Provider(**body.model_dump())
    session.add(provider)
    await session.commit()
    await session.refresh(provider)
    return provider


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(
    provider_id: str,
    session: AsyncSession = Depends(get_session),
):
    provider = await session.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: str,
    body: ProviderUpdate,
    session: AsyncSession = Depends(get_session),
):
    provider = await session.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    for field, value in body.model_dump(exclude_unset=True).items():
        setattr(provider, field, value)
    await session.commit()
    await session.refresh(provider)
    return provider


@router.delete("/{provider_id}", status_code=204)
async def delete_provider(
    provider_id: str,
    session: AsyncSession = Depends(get_session),
):
    provider = await session.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    await session.delete(provider)
    await session.commit()


@router.post("/{provider_id}/health-check", response_model=HealthCheckResponse)
async def provider_health_check(
    provider_id: str,
    session: AsyncSession = Depends(get_session),
):
    provider = await session.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")

    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            resp = await client.get(provider.base_url)
            if resp.status_code < 500:
                return HealthCheckResponse(
                    provider_id=provider.id,
                    provider_name=provider.name,
                    status="healthy",
                    detail=f"HTTP {resp.status_code}",
                )
            return HealthCheckResponse(
                provider_id=provider.id,
                provider_name=provider.name,
                status="unhealthy",
                detail=f"HTTP {resp.status_code}",
            )
    except httpx.TimeoutException:
        return HealthCheckResponse(
            provider_id=provider.id,
            provider_name=provider.name,
            status="unhealthy",
            detail="Connection timed out",
        )
    except httpx.RequestError as exc:
        return HealthCheckResponse(
            provider_id=provider.id,
            provider_name=provider.name,
            status="unhealthy",
            detail=str(exc),
        )
