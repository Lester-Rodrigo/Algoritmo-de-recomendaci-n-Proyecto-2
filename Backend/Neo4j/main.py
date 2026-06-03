import os
import sqlite3
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from data_base import SteamGraphDB
from dotenv import load_dotenv
# CONF


BASE_DIR       = Path(__file__).parent
load_dotenv(BASE_DIR / ".env")
NEO4J_URI      = os.getenv("NEO4J_URI",      "bolt://localhost:7687")
NEO4J_USER     = os.getenv("NEO4J_USER",     "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
SQLITE_PATH    = BASE_DIR / os.getenv("SQLITE_PATH", "../data/users.db")
STEAM_CSV      = BASE_DIR / os.getenv("STEAM_CSV",   "../data/steam.csv")
MEDIA_CSV      = BASE_DIR / os.getenv("MEDIA_CSV",   "../data/steam_media_data.csv")
DESC_CSV       = BASE_DIR / os.getenv("DESC_CSV",    "../data/steam_description_data.csv")
IMPORT_LIMIT   = int(os.getenv("IMPORT_LIMIT", "100"))
FORCE_IMPORT   = os.getenv("FORCE_IMPORT", "False") == "True"

# SQLITE

sqlite_conn = sqlite3.connect(str(SQLITE_PATH), check_same_thread=False)
sqlite_conn.row_factory = sqlite3.Row

def init_sqlite():
    sqlite_conn.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL
        )
    """)
    sqlite_conn.commit()

# GRAFO

graph = SteamGraphDB(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)

# STARTUP

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_sqlite()
    graph.create_constraints()
    graph.load_media(str(MEDIA_CSV), str(DESC_CSV))

    with graph.driver.session() as s:
        count = s.run("MATCH (g:Game) RETURN count(g) AS c").single()["c"]

    if count == 0 or FORCE_IMPORT:
        if STEAM_CSV.exists():
            print(f"Importing games from {STEAM_CSV}...")
            graph.import_games_csv(str(STEAM_CSV), limit=IMPORT_LIMIT)
            print("Calculating similarities...")
            graph.calculate_similarity()
        else:
            print(f"Warning: {STEAM_CSV} not found.")

    rows = sqlite_conn.execute("SELECT username FROM users").fetchall()
    for row in rows:
        if not graph.user_exists_in_graph(row["username"]):
            graph.create_user(row["username"])
            print(f"  Repaired graph node for: {row['username']}")

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

FRONTEND = BASE_DIR.parent.parent / "Frontend"
app.mount("/static", StaticFiles(directory=FRONTEND), name="static")

@app.get("/")
def root():
    return FileResponse(FRONTEND / "html" / "login.html")


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
    score: float

class UserGenresBody(BaseModel):
    username: str
    genres: list[str]

class ReactionBody(BaseModel):
    username: str
    appid: int

class WishlistBody(BaseModel):
    username: str
    appid: int

# AUTENTICACION

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

# GENEROS ////////////////////////////

@app.get("/api/genres")
def list_genres():
    return graph.get_all_genres()


@app.post("/api/user/genres")
def save_user_genres(body: UserGenresBody):
    get_user(body.username)
    graph.add_user_genres(body.username, body.genres)
    return {"ok": True}


@app.get("/api/user/genres/{username}")
def get_user_genres(username: str):
    get_user(username)
    return graph.get_user_genres(username)

# GAMES //////////////////////////////////////////////////////

@app.get("/api/games/search")
def search_games(q: str, limit: int = 20):
    return graph.search_games(q, limit=limit)


@app.get("/api/games/genre/{genre}")
def games_by_genre(genre: str, limit: int = 50):
    return graph.get_games_by_genre(genre, limit=limit)


@app.get("/api/games")
def list_games(limit: int = 50, offset: int = 0):
    return graph.get_all_games(limit=limit, offset=offset)


@app.get("/api/games/{appid}/media")
def get_game_media(appid: int):
    return graph.get_game_media(appid)


@app.get("/api/games/{appid}")
def get_game(appid: int):
    game = graph.get_game(appid)
    if not game:
        raise HTTPException(404, "Game not found")
    return game

# RATINGGS ////////////////////////////////////////////////////

@app.post("/api/ratings")
def rate_game(body: RatingBody):
    get_user(body.username)
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

# LIKES/DISLIKES //////////////////////////////////////////////////

@app.post("/api/reactions/like")
def like_game(body: ReactionBody):
    get_user(body.username)
    graph.like_game(body.username, body.appid)
    return {"ok": True}


@app.post("/api/reactions/dislike")
def dislike_game(body: ReactionBody):
    get_user(body.username)
    graph.dislike_game(body.username, body.appid)
    return {"ok": True}


@app.delete("/api/reactions/{appid}")
def remove_reaction(appid: int, username: str):
    get_user(username)
    graph.remove_reaction(username, appid)
    return {"ok": True}


@app.get("/api/reactions/{username}")
def get_reactions(username: str):
    get_user(username)
    return graph.get_user_reactions(username)


@app.get("/api/reactions/{username}/{appid}")
def get_game_reaction(username: str, appid: int):
    get_user(username)
    return {"reaction": graph.get_game_reaction(username, appid)}

# WISHLIST ///////////////////////////////////////////////////

@app.post("/api/wishlist")
def add_to_wishlist(body: WishlistBody):
    get_user(body.username)
    graph.add_to_wishlist(body.username, body.appid)
    return {"ok": True}


@app.delete("/api/wishlist/{appid}")
def remove_from_wishlist(appid: int, username: str):
    get_user(username)
    graph.remove_from_wishlist(username, appid)
    return {"ok": True}


@app.get("/api/wishlist/{username}")
def get_wishlist(username: str):
    get_user(username)
    return graph.get_wishlist(username)

# RECOMENDACIONES /////////////////////////////////////////////

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


@app.get("/api/recommendations/genres/{username}")
def genre_recs(username: str):
    get_user(username)
    return graph.expanded_recommendations(username)

# MIAN ///////////////////////////////////////////////////////

if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)