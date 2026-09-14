from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from .database import engine, Base
from .routers import auth, frequencias, websockets, paginas

app = FastAPI(title="Sistema de Controle de Frequência Escolar")

app.mount("/static", StaticFiles(directory="app/static"), name="static")


@app.on_event("startup")
async def criar_tabelas():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


app.include_router(paginas.router)
app.include_router(auth.router)
app.include_router(frequencias.router)
app.include_router(websockets.router)
