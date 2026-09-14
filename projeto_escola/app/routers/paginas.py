from fastapi import APIRouter, Depends, Request
from fastapi.templating import Jinja2Templates
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date as date_type

from .. import models
from ..database import get_db
from ..dependencies import get_current_user_pagina, exigir_acesso_escola
from ..services import garantir_frequencias_do_dia

templates = Jinja2Templates(directory="app/templates")
router = APIRouter()


@router.get("/")
async def pagina_login(request: Request):
    return templates.TemplateResponse("login.html", {"request": request})


@router.get("/turmas")
async def pagina_turmas(
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user_pagina),
):
    contagem = (
        select(models.Aluno.turma_id, func.count(models.Aluno.id).label("total"))
        .group_by(models.Aluno.turma_id)
        .subquery()
    )

    resultado = await db.execute(
        select(models.Turma, models.Escola, contagem.c.total)
        .join(models.ProfessorTurma, models.ProfessorTurma.turma_id == models.Turma.id)
        .join(models.Escola, models.Escola.id == models.Turma.escola_id)
        .outerjoin(contagem, contagem.c.turma_id == models.Turma.id)
        .where(models.ProfessorTurma.usuario_id == usuario.id)
        .order_by(models.Turma.nome)
    )
    turmas = resultado.all()

    return templates.TemplateResponse("turmas.html", {
        "request": request, "usuario": usuario, "turmas": turmas,
    })


@router.get("/painel/{turma_id}")
async def pagina_painel(
    turma_id: int,
    request: Request,
    db: AsyncSession = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user_pagina),
):
    turma = await db.get(models.Turma, turma_id)
    exigir_acesso_escola(usuario, turma.escola_id)

    hoje = date_type.today()
    await garantir_frequencias_do_dia(db, turma_id, hoje, usuario)

    resultado = await db.execute(
        select(models.Frequencia, models.Aluno)
        .join(models.Aluno)
        .where(models.Aluno.turma_id == turma_id, models.Frequencia.data == hoje)
        .order_by(models.Aluno.nome)
    )
    linhas = resultado.all()

    return templates.TemplateResponse("painel_prof.html", {
        "request": request, "usuario": usuario, "turma": turma,
        "linhas": linhas, "hoje": hoje,
    })
