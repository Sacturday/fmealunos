from pydantic import BaseModel, ConfigDict
from datetime import date, datetime
from enum import Enum


class StatusFrequencia(str, Enum):
    PRESENTE = "PRESENTE"
    FALTA = "FALTA"
    FALTA_JUSTIFICADA = "FALTA_JUSTIFICADA"


class FrequenciaUpdate(BaseModel):
    status: StatusFrequencia
    versao: int  # controle de concorrência otimista


class Frequencia(BaseModel):
    id: int
    aluno_id: int
    data: date
    status: StatusFrequencia
    registrado_por: str
    atualizado_em: datetime
    versao: int

    model_config = ConfigDict(from_attributes=True)


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class LancamentoFrequencia(BaseModel):
    frequencia_id: int
    versao: int
    status: StatusFrequencia


class ConfirmarFrequenciasRequest(BaseModel):
    lancamentos: list[LancamentoFrequencia]
