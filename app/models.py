from sqlalchemy import Column, Integer, String, Date, DateTime, ForeignKey, Enum as SAEnum, UniqueConstraint, func
from .database import Base
import enum


class StatusFrequencia(str, enum.Enum):
    PRESENTE = "PRESENTE"
    FALTA = "FALTA"
    FALTA_JUSTIFICADA = "FALTA_JUSTIFICADA"


class Perfil(str, enum.Enum):
    PROFESSOR = "PROFESSOR"
    SECRETARIA = "SECRETARIA"
    GESTOR_REDE = "GESTOR_REDE"


class Escola(Base):
    __tablename__ = "escolas"
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    endereco = Column(String)
    rede_id = Column(Integer, index=True)


class Turma(Base):
    __tablename__ = "turmas"
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    ano_letivo = Column(Integer, nullable=False)
    escola_id = Column(Integer, ForeignKey("escolas.id"), index=True)


class Aluno(Base):
    __tablename__ = "alunos"
    id = Column(Integer, primary_key=True)
    nome = Column(String, nullable=False)
    matricula = Column(String, unique=True, nullable=False)
    turma_id = Column(Integer, ForeignKey("turmas.id"), index=True)
    status = Column(String, default="ATIVO")


class Frequencia(Base):
    __tablename__ = "frequencias"
    id = Column(Integer, primary_key=True)
    aluno_id = Column(Integer, ForeignKey("alunos.id"), nullable=False, index=True)
    data = Column(Date, nullable=False, index=True)
    status = Column(SAEnum(StatusFrequencia), nullable=False, default=StatusFrequencia.PRESENTE)
    registrado_por = Column(String, nullable=False)
    atualizado_em = Column(DateTime, server_default=func.now(), onupdate=func.now())
    versao = Column(Integer, nullable=False, default=1)

    __table_args__ = (
        UniqueConstraint("aluno_id", "data", name="uq_frequencia_aluno_data"),
    )


class FrequenciaAuditoria(Base):
    __tablename__ = "frequencia_auditoria"
    id = Column(Integer, primary_key=True)
    frequencia_id = Column(Integer, ForeignKey("frequencias.id"), index=True)
    usuario_id = Column(String, nullable=False)
    campo_alterado = Column(String, nullable=False)
    valor_antigo = Column(String)
    valor_novo = Column(String)
    data_alteracao = Column(DateTime, server_default=func.now())


class Usuario(Base):
    __tablename__ = "usuarios"
    id = Column(Integer, primary_key=True)
    username = Column(String, unique=True, nullable=False)
    nome = Column(String, nullable=False)
    senha_hash = Column(String, nullable=False)
    perfil = Column(SAEnum(Perfil), nullable=False)
    escola_id = Column(Integer, ForeignKey("escolas.id"), nullable=True)  # nulo para GESTOR_REDE


class ProfessorTurma(Base):
    __tablename__ = "professor_turma"
    id = Column(Integer, primary_key=True)
    usuario_id = Column(Integer, ForeignKey("usuarios.id"), index=True)
    turma_id = Column(Integer, ForeignKey("turmas.id"), index=True)

    __table_args__ = (
        UniqueConstraint("usuario_id", "turma_id", name="uq_professor_turma"),
    )
