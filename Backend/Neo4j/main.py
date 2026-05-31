
import sqlite3
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from data_base import SteamGraphDB


NEO4J_URI      = "bolt://localhost:7687"
NEO4J_USER     = "videojuegos"
NEO4J_PASSWORD = "qwertyui"
SQLITE_PATH    = "users.db"
STEAM_CSV      = "steam.csv"


sqlite_conn = sqlite3.connect(SQLITE_PATH, check_same_thread=False)
sqlite_conn.row_factory = sqlite3.Row

def init_sqlite():
    sqlite_conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
    sqlite_conn.commit()

graph = SteamGraphDB(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Set up SQLite Neo4j 
    init_sqlite()
    graph.create_constraints()

    with graph.driver.session() as s:
        count = s.run("MATCH (g:Game) RETURN count(g) AS c").single()["c"]

    if count == 0:
        if Path(STEAM_CSV).exists():
            print(f"Importing games from {STEAM_CSV}...")
            graph.import_games_csv(STEAM_CSV)
            print("Calculating similarities (this takes a while the first time)...")
            graph.calculate_jaccard_similarity()
        else:
            print(f"Warning: {STEAM_CSV} not found. Add it and restart.")

    yield  

    graph.close()
    sqlite_conn.close()


app = FastAPI(title="Steam Recommender", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_user(username: str):
    
    row = sqlite_conn.execute(
        "SELECT * FROM users WHERE username = ?", (username,)
    ).fetchone()
    if not row:
        raise HTTPException(404, f"User '{username}' not found")
    return row


class RegisterBody(BaseModel):
    username: str
    password: str

class LoginBody(BaseModel):
    username: str
    password: str

class RatingBody(BaseModel):
    username: str
    appid: int
    score: float   # 1 – 10

# Auth routes
@app.post("/api/register")
def register(body: RegisterBody):
    
    try:
        sqlite_conn.execute(
            "INSERT INTO users (username, password) VALUES (?, ?)",
            (body.username, body.password),
        )
        sqlite_conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(409, "Username already taken")

    graph.create_user(body.username)
    return {"ok": True, "username": body.username}


@app.post("/api/login")
def login(body: LoginBody):

    row = sqlite_conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (body.username, body.password),
    ).fetchone()
    if not row:
        raise HTTPException(401, "Wrong username or password")
    return {"ok": True, "username": body.username}

#game routes

@app.get("/api/games")
def list_games(limit: int = 50, offset: int = 0):
    
    return graph.get_all_games(limit=limit, offset=offset)


@app.get("/api/games/search")
def search_games(q: str, limit: int = 20):
    
    return graph.search_games(q, limit=limit)


@app.get("/api/games/{appid}")
def get_game(appid: int):
    
    game = graph.get_game(appid)
    if not game:
        raise HTTPException(404, "Game not found")
    return game

#rating routess

@app.post("/api/ratings")
def rate_game(body: RatingBody):
    
    get_user(body.username)   # ussuario existe 
    if not (1 <= body.score <= 10):
        raise HTTPException(400, "Score must be between 1 and 10")
    graph.add_user_rating(body.username, body.appid, body.score)
    return {"ok": True}


@app.delete("/api/ratings/{appid}")
def delete_rating(appid: int, username: str):

    get_user(username)
    graph.remove_user_rating(username, appid)
    return {"ok": True}


@app.get("/api/ratings/{username}")
def get_ratings(username: str):
    
    get_user(username)
    return graph.get_user_ratings(username)

#recommendation routes

@app.get("/api/recommendations/content/{username}")
def content_recs(username: str):
    
    get_user(username)
    return graph.content_based_recommendations(username)


@app.get("/api/recommendations/collaborative/{username}")
def collab_recs(username: str):
    
    get_user(username)
    return graph.collaborative_filtering(username)


@app.get("/api/recommendations/hybrid/{username}")
def hybrid_recs(username: str):
    
    get_user(username)
    return graph.hybrid_recommendations(username)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="localhost", port=8000, reload=True)