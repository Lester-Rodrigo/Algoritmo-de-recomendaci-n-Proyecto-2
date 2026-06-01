from data_base import GrafoDB
from dotenv import load_dotenv
import os

Users = ["Alice", "Bob", "Charlie", "David", "Eve"]
Vertices = ["Halo", 700, "God of War", 650, "Plants vs. Zombies", 300, 
            "Call of Duty", 800, "Devil May Cry", 400]

def test_user_game_db():

    load_dotenv()

    db = GrafoDB(
        os.getenv("NEO4J_URI"),
        os.getenv("NEO4J_USER"),
        os.getenv("NEO4J_PASSWORD")
    )

    # Limpiar base de datos antes del test
    with db.driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

    # Crear vértices de juegos
    for i in range(0, len(Vertices), 2):
        db.create_vertex_game(Vertices[i], Vertices[i+1])

    # Crear vértices de usuarios
    for user in Users:
        db.create_vertex_user(user)
    
    # Crear relaciones entre usuarios y juegos
    db.create_user_vertex_edge("Alice", "Halo")
    db.create_user_vertex_edge("Alice", "God of War")
    db.create_user_vertex_edge("Bob", "Call of Duty")
    db.create_user_vertex_edge("Charlie", "Plants vs. Zombies")
    db.create_user_vertex_edge("David", "Call of Duty")
    db.create_user_vertex_edge("Eve", "Devil May Cry")  
    # Obtener intereses de Alice
    intereses_alice = db.get_user_interests("Alice")
    assert set(intereses_alice) == {
        "Alice is interested in Halo (price: 700)",
        "Alice is interested in God of War (price: 650)"
    }

    db.close()
    
def test_game_game_db():
    load_dotenv()

    db = GrafoDB(
        os.getenv("NEO4J_URI"),
        os.getenv("NEO4J_USER"),
        os.getenv("NEO4J_PASSWORD")
    )

    # Limpiar base de datos antes del test
    with db.driver.session() as session:
        session.run("MATCH (n) DETACH DELETE n")

    # Crear vértices de juegos
    for i in range(0, len(Vertices), 2):
        db.create_vertex_game(Vertices[i], Vertices[i+1])

    # Crear vértices de usuarios
    for user in Users:
        db.create_vertex_user(user)

    # Crear relaciones entre juegos
    db.create_vertex_vertex_edge("Halo", "Call of Duty")
    db.create_vertex_vertex_edge("God of War", "Devil May Cry")
    
    # Crear relaciones entre usuarios y juegos
    db.create_user_vertex_edge("Alice", "Halo")
    db.create_user_vertex_edge("Alice", "God of War")
    db.create_user_vertex_edge("Bob", "Call of Duty")
    db.create_user_vertex_edge("Charlie", "Plants vs. Zombies")
    db.create_user_vertex_edge("David", "Call of Duty")
    db.create_user_vertex_edge("Eve", "Devil May Cry")
    
    # Obtener recomendaciones para Alice
    recomendaciones_alice = db.get_possible_recommendations("Alice")
    assert set(recomendaciones_alice) == {
        "Alice might also like Call of Duty (price: 800)",
        "Alice might also like Devil May Cry (price: 400)"
    }

    db.close()