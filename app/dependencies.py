from fastapi import Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from . import models
from .database import get_db
from .security import decodificar_token


async def get_current_user(request: Request, db: AsyncSession = Depends(get_db)) -> models.Usuario:
    erro = HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Não autenticado")

    token = request.cookies.get("access_token")
    if not token:
        raise erro

    payload = decodificar_token(token)
    if payload is None or "sub" not in payload:
        raise erro

    usuario = (await db.execute(
        select(models.Usuario).where(models.Usuario.username == payload["sub"])
    )).scalar_one_or_none()

    if usuario is None:
        raise erro
    return usuario


async def get_current_user_pagina(request: Request, db: AsyncSession = Depends(get_db)) -> models.Usuario:
    """Igual a get_current_user, mas redireciona para o login em vez de devolver 401 JSON —
    usada nas rotas que renderizam páginas HTML."""
    redireciona = HTTPException(status_code=303, headers={"Location": "/"})

    token = request.cookies.get("access_token")
    if not token:
        raise redireciona

    payload = decodificar_token(token)
    if payload is None or "sub" not in payload:
        raise redireciona

    usuario = (await db.execute(
        select(models.Usuario).where(models.Usuario.username == payload["sub"])
    )).scalar_one_or_none()

    if usuario is None:
        raise redireciona
    return usuario


def exigir_acesso_escola(usuario: models.Usuario, escola_id: int):
    if usuario.perfil == models.Perfil.GESTOR_REDE:
        return
    if usuario.escola_id != escola_id:
        raise HTTPException(status_code=403, detail="Sem permissão para esta escola")
