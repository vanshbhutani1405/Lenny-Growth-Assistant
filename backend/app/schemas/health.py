from typing import Literal

from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: Literal["ok"]
    environment: str
    provider: str
    model: str


class DatabaseHealthResponse(BaseModel):
    status: Literal["ok"]
    database: Literal["reachable"]
