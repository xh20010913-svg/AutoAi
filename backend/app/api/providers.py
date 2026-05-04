from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_session
from app.models.provider import Model, Provider
from app.schemas.provider import (
    ModelCreate,
    ModelResponse,
    ProviderCreate,
    ProviderResponse,
    ProviderUpdate,
)

router = APIRouter(prefix="/providers", tags=["providers"])


# ── Provider CRUD ───────────────────────────────────────────────────────

@router.get("", response_model=list[ProviderResponse])
async def list_providers(session: AsyncSession = Depends(get_session)):
    result = await session.execute(select(Provider).order_by(Provider.name))
    return result.scalars().all()


@router.post("", response_model=ProviderResponse, status_code=201)
async def create_provider(body: ProviderCreate, session: AsyncSession = Depends(get_session)):
    provider = Provider(**body.model_dump())
    session.add(provider)
    await session.commit()
    await session.refresh(provider)
    return provider


@router.get("/{provider_id}", response_model=ProviderResponse)
async def get_provider(provider_id: str, session: AsyncSession = Depends(get_session)):
    provider = await session.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    return provider


@router.put("/{provider_id}", response_model=ProviderResponse)
async def update_provider(
    provider_id: str, body: ProviderUpdate, session: AsyncSession = Depends(get_session)
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
async def delete_provider(provider_id: str, session: AsyncSession = Depends(get_session)):
    provider = await session.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    await session.delete(provider)
    await session.commit()


# ── Model CRUD (nested under Provider) ──────────────────────────────────

@router.get("/{provider_id}/models", response_model=list[ModelResponse])
async def list_models(provider_id: str, session: AsyncSession = Depends(get_session)):
    provider = await session.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    result = await session.execute(
        select(Model).where(Model.provider_id == provider_id).order_by(Model.name)
    )
    return result.scalars().all()


@router.post("/{provider_id}/models", response_model=ModelResponse, status_code=201)
async def create_model(
    provider_id: str, body: ModelCreate, session: AsyncSession = Depends(get_session)
):
    provider = await session.get(Provider, provider_id)
    if not provider:
        raise HTTPException(status_code=404, detail="Provider not found")
    model = Model(provider_id=provider_id, **body.model_dump())
    session.add(model)
    await session.commit()
    await session.refresh(model)
    return model


@router.delete("/{provider_id}/models/{model_id}", status_code=204)
async def delete_model(
    provider_id: str, model_id: str, session: AsyncSession = Depends(get_session)
):
    model = await session.get(Model, model_id)
    if not model or model.provider_id != provider_id:
        raise HTTPException(status_code=404, detail="Model not found")
    await session.delete(model)
    await session.commit()
