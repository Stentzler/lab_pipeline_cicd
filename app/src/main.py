from fastapi import FastAPI
from pydantic import BaseModel

from src.service import sum_numbers

app = FastAPI()


class SumRequest(BaseModel):
    a: int
    b: int


@app.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/hello")
def hello() -> dict[str, str]:
    return {"message": "hello from study api"}


@app.post("/sum")
def calculate_sum(payload: SumRequest) -> dict[str, int]:
    return {"result": sum_numbers(payload.a, payload.b)}
