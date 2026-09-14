from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from datetime import date as date_type

from . import models


async def garantir_frequencias_do_dia(db: AsyncSession, turma_id: int, data: date_type, usuario: models.Usuario):
    """Upsert idempotente: garante que cada aluno da turma tenha um registro de frequência
    no dia informado (default PRESENTE), sem sobrescrever o que já existir."""
    alunos = (await db.execute(
        select(models.Aluno).where(models.Aluno.turma_id == turma_id)
    )).scalars().all()

    for aluno in alunos:
        stmt = pg_insert(models.Frequencia).values(
            aluno_id=aluno.id, data=data, status="PRESENTE",
            registrado_por=usuario.username, versao=1,
        ).on_conflict_do_nothing(index_elements=["aluno_id", "data"])
        await db.execute(stmt)
    await db.commit()
