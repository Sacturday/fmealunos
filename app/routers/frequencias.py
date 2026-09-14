from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date as date_type

from .. import models, schemas
from ..database import get_db
from ..dependencies import get_current_user, exigir_acesso_escola
from ..services import garantir_frequencias_do_dia
from .websockets import websocket_manager

router = APIRouter(prefix="/api/frequencias", tags=["frequencias"])


@router.get("/")
async def listar_frequencias(
    escola_id: int, turma_id: int, data: date_type,
    db: AsyncSession = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    exigir_acesso_escola(usuario, escola_id)
    await garantir_frequencias_do_dia(db, turma_id, data, usuario)

    resultado = await db.execute(
        select(models.Frequencia).join(models.Aluno)
        .where(models.Aluno.turma_id == turma_id, models.Frequencia.data == data)
    )
    return resultado.scalars().all()


@router.post("/confirmar")
async def confirmar_frequencias(
    dados: schemas.ConfirmarFrequenciasRequest,
    db: AsyncSession = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    """Confirmação em lote da chamada do dia (fluxo do painel do professor):
    o professor marca todos os alunos localmente e envia tudo de uma vez aqui.
    Tudo ou nada: se qualquer registro estiver em conflito, a lista inteira é revertida
    para o professor revisar antes de tentar de novo."""
    conflitos = []
    atualizados = []
    escola_id_afetada = None

    for lancamento in dados.lancamentos:
        frequencia = (await db.execute(
            select(models.Frequencia).where(models.Frequencia.id == lancamento.frequencia_id).with_for_update()
        )).scalar_one_or_none()

        if not frequencia:
            conflitos.append({"frequencia_id": lancamento.frequencia_id, "motivo": "não encontrado"})
            continue

        aluno = await db.get(models.Aluno, frequencia.aluno_id)
        turma = await db.get(models.Turma, aluno.turma_id)
        exigir_acesso_escola(usuario, turma.escola_id)
        escola_id_afetada = turma.escola_id

        if frequencia.versao != lancamento.versao:
            conflitos.append({"frequencia_id": lancamento.frequencia_id, "motivo": "versão desatualizada"})
            continue

        valor_antigo = frequencia.status.value
        frequencia.status = lancamento.status
        frequencia.versao += 1

        db.add(models.FrequenciaAuditoria(
            frequencia_id=frequencia.id,
            usuario_id=usuario.username,
            campo_alterado="status",
            valor_antigo=valor_antigo,
            valor_novo=lancamento.status.value,
        ))
        atualizados.append(frequencia.id)

    if conflitos:
        await db.rollback()
        raise HTTPException(status_code=409, detail={"conflitos": conflitos})

    await db.commit()

    if escola_id_afetada is not None:
        await websocket_manager.broadcast_to_escola(
            escola_id_afetada, "<div id='estatisticas-rede'>Atualizado</div>"
        )

    return {"status": "ok", "atualizados": atualizados}


@router.patch("/{frequencia_id}")
async def atualizar_frequencia(
    frequencia_id: int,
    dados: schemas.FrequenciaUpdate,
    db: AsyncSession = Depends(get_db),
    usuario: models.Usuario = Depends(get_current_user),
):
    """Correção pontual de um registro já existente (ex.: secretaria lançando uma
    falta justificada depois de receber o atestado) — fora do fluxo de chamada em lote."""
    frequencia = (await db.execute(
        select(models.Frequencia).where(models.Frequencia.id == frequencia_id).with_for_update()
    )).scalar_one_or_none()

    if not frequencia:
        raise HTTPException(status_code=404, detail="Registro não encontrado")

    aluno = await db.get(models.Aluno, frequencia.aluno_id)
    turma = await db.get(models.Turma, aluno.turma_id)
    exigir_acesso_escola(usuario, turma.escola_id)

    if frequencia.versao != dados.versao:
        raise HTTPException(status_code=409, detail="Conflito: registro modificado por outro usuário")

    valor_antigo = frequencia.status.value
    frequencia.status = dados.status
    frequencia.versao += 1

    db.add(models.FrequenciaAuditoria(
        frequencia_id=frequencia.id,
        usuario_id=usuario.username,
        campo_alterado="status",
        valor_antigo=valor_antigo,
        valor_novo=dados.status.value,
    ))

    await db.commit()
    await db.refresh(frequencia)

    await websocket_manager.broadcast_to_escola(
        turma.escola_id, "<div id='estatisticas-rede'>Atualizado</div>"
    )
    return frequencia
