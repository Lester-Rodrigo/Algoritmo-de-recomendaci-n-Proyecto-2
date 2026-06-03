import sqlite3
from pathlib import Path
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse

from data_base import SteamGraphDB


BASE_DIR       = Path(__file__).parent
NEO4J_URI      = "bolt://localhost:7687"
NEO4J_USER     = "neo4j"
NEO4J_PASSWORD = "qwertyui"
SQLITE_PATH    = BASE_DIR.parent / "data" / "users.db"
STEAM_CSV      = BASE_DIR.parent / "data" / "steam.csv"
IMPORT_LIMIT  = 100   
FORCE_IMPORT  = False #SSOLO CAMBIAR A TRUE SI SE QUIERE REIMPORTAR DESDE EL CSV, 
FRONTEND_DIR    = BASE_DIR.parent.parent / "Frontend" / "html"

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


graph = SteamGraphDB(NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD)


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_sqlite()
    graph.create_constraints()

    # importa csv 
    with graph.driver.session() as s:
        count = s.run("MATCH (g:Game) RETURN count(g) AS c").single()["c"]

    if count == 0 or FORCE_IMPORT:
        if STEAM_CSV.exists():
            print(f"Importing games from {STEAM_CSV}...")
            graph.import_games_csv(str(STEAM_CSV))
            print("Calculating similarities...")
            graph.calculate_similarity()
        else:
            print(f"Warning: {STEAM_CSV} not found. Add it and restart.")

    # ve que cada usuario de SQLite tenga su nodo en Neo4j, por si se crearon antes de que el grafo estuviera listo
    
    rows = sqlite_conn.execute("SELECT username FROM users").fetchall()
    for row in rows:
        if not graph.user_exists_in_graph(row["username"]):
            graph.create_user(row["username"])
            print(f"  Repaired missing graph node for user: {row['username']}")

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

app.mount("/static", StaticFiles(directory=BASE_DIR.parent.parent / "Frontend"), name="static")

@app.get("/")
def root():
    return FileResponse(BASE_DIR.parent.parent / "Frontend" / "html" / "login.html")


def get_user(username: str):
    """Return the SQLite user row, or 404 if not found."""
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
    score: float  # 1–10
    
class UserGenresBody(BaseModel):
    username: str
    genres: list[str]


#Autenticacion ///////////////////////////////
@app.post("/api/register")
def register(body: RegisterBody):


    #inserta credencailes en SQLite. Si el username ya existe, lanza error 409 Conflict
    #crea nodo de usuario en Neo4j. Este nodo es el que luego acumula las relaciones RATED.
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
    #verifica credenciales y retorna 200 OK si son correctas, 401 si no
    row = sqlite_conn.execute(
        "SELECT * FROM users WHERE username = ? AND password = ?",
        (body.username, body.password),
    ).fetchone()
    if not row:
        raise HTTPException(401, "Wrong username or password")
    return {"ok": True, "username": body.username}

@app.post("/api/user/genres")
def save_user_genres(body: UserGenresBody):

    get_user(body.username)

    graph.add_user_genres(
        body.username,
        body.genres
    )

    return {"ok": True}




@app.get("/api/games/search")
def search_games(q: str, limit: int = 20):
    return graph.search_games(q, limit=limit)


@app.get("/api/games")
def list_games(limit: int = 50, offset: int = 0):
    return graph.get_all_games(limit=limit, offset=offset)


@app.get("/api/games/{appid}")
def get_game(appid: int):
    game = graph.get_game(appid)
    if not game:
        raise HTTPException(404, "Game not found")
    return game


# (:User {name})-[:RATED {score}]->(:Game {appid})
#ratings se guardan como relaciones en el grafo  

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


@app.get("/api/recommendations/content/{username}")
def content_recs(username: str):
    #sigue aristas similares
    get_user(username)
    return graph.content_based_recommendations(username)


@app.get("/api/recommendations/collaborative/{username}")
def collab_recs(username: str):
    #juegos que les gustaron a usuarios con gustos similares que hayan calificado los mismos juegos
    get_user(username)
    return graph.collaborative_filtering(username)


@app.get("/api/recommendations/hybrid/{username}")
def hybrid_recs(username: str):

    get_user(username)
    return graph.hybrid_recommendations(username)

@app.get("/api/recommendations/genres/{username}")
def genre_recommendations(username: str):

    return graph.expanded_recommendations(username)


if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)