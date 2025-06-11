from fastapi import FastAPI, HTTPException, Path
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import aiosqlite

app = FastAPI()

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

DATABASE = "agendamentos.db"


# Models
class Usuario(BaseModel):
    nome: str
    email: str


class Agendamento(BaseModel):
    data: str
    hora: str
    status: str
    usuarioId: int


# Seed
async def seed_if_needed():
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS usuarios (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nome TEXT NOT NULL,
                email TEXT NOT NULL
            );
        """
        )
        await db.execute(
            """
            CREATE TABLE IF NOT EXISTS agendamentos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                data TEXT NOT NULL,
                hora TEXT NOT NULL,
                status TEXT NOT NULL,
                usuarioId INTEGER NOT NULL
            );
        """
        )
        await db.commit()

        async with db.execute("SELECT COUNT(*) FROM usuarios") as cursor:
            count = (await cursor.fetchone())[0]
        if count == 0:
            await db.executemany(
                "INSERT INTO usuarios (nome, email) VALUES (?, ?)",
                [
                    ("Fulano", "fulano@gmail.com"),
                    ("Beltrano", "beltrano@gmail.com"),
                    ("Sicrano", "sicrano@gmail.com"),
                ],
            )
            await db.executemany(
                "INSERT INTO agendamentos (data, hora, status, usuarioId) VALUES (?, ?, ?, ?)",
                [
                    ("2023-11-10", "14:00", "ativo", 1),
                    ("2023-11-12", "09:00", "concluido", 2),
                    ("2023-11-15", "16:30", "ativo", 3),
                ],
            )
            await db.commit()


@app.on_event("startup")
async def startup_event():
    await seed_if_needed()


# Rotas usuários
@app.get("/usuarios")
async def get_usuarios():
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM usuarios")
        return await cursor.fetchall()


@app.post("/usuarios")
async def create_usuario(usuario: Usuario):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            "INSERT INTO usuarios (nome, email) VALUES (?, ?)",
            (usuario.nome, usuario.email),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM usuarios ORDER BY id DESC LIMIT 1")
        return await cursor.fetchone()


@app.put("/usuarios/{id}")
async def update_usuario(id: int, usuario: Usuario):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            "UPDATE usuarios SET nome = ?, email = ? WHERE id = ?",
            (usuario.nome, usuario.email, id),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM usuarios WHERE id = ?", (id,))
        user = await cursor.fetchone()
        if not user:
            raise HTTPException(status_code=404, detail="Usuário não encontrado")
        return user


@app.delete("/usuarios/{id}")
async def delete_usuario(id: int):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("DELETE FROM agendamentos WHERE usuarioId = ?", (id,))
        await db.execute("DELETE FROM usuarios WHERE id = ?", (id,))
        await db.commit()
    return {"ok": True}


# Rotas agendamentos
@app.get("/agendamentos")
async def get_agendamentos():
    async with aiosqlite.connect(DATABASE) as db:
        db.row_factory = aiosqlite.Row
        cursor = await db.execute("SELECT * FROM agendamentos")
        return await cursor.fetchall()


@app.post("/agendamentos")
async def create_agendamento(agendamento: Agendamento):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            "INSERT INTO agendamentos (data, hora, status, usuarioId) VALUES (?, ?, ?, ?)",
            (
                agendamento.data,
                agendamento.hora,
                agendamento.status,
                agendamento.usuarioId,
            ),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM agendamentos ORDER BY id DESC LIMIT 1")
        return await cursor.fetchone()


@app.put("/agendamentos/{id}")
async def update_agendamento(id: int, agendamento: Agendamento):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute(
            "UPDATE agendamentos SET data = ?, hora = ?, status = ?, usuarioId = ? WHERE id = ?",
            (
                agendamento.data,
                agendamento.hora,
                agendamento.status,
                agendamento.usuarioId,
                id,
            ),
        )
        await db.commit()
        cursor = await db.execute("SELECT * FROM agendamentos WHERE id = ?", (id,))
        a = await cursor.fetchone()
        if not a:
            raise HTTPException(status_code=404, detail="Agendamento não encontrado")
        return a


@app.delete("/agendamentos/{id}")
async def delete_agendamento(id: int):
    async with aiosqlite.connect(DATABASE) as db:
        await db.execute("DELETE FROM agendamentos WHERE id = ?", (id,))
        await db.commit()
    return {"ok": True}
