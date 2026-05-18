from neo4j import GraphDatabase
import pandas as pd
from itertools import combinations

if __name__ == "__main__":

    db = SteamGraphDB(
        "bolt://localhost:7687",
        "neo4j",
        "password"
    )

    db.create_constraints()

    # IMPORT STEAM DATASET
    db.import_games_csv("steam.csv")

    # CREATE SIMILARITY GRAPH
    db.calculate_jaccard_similarity()

    # DEMO USERS
    db.create_user("Carlos")
    db.create_user("Ana")

    # USER RATINGS
    db.add_user_rating("Carlos", 570, 5)
    db.add_user_rating("Carlos", 730, 4)

    db.add_user_rating("Ana", 570, 5)
    db.add_user_rating("Ana", 578080, 5)

    # CONTENT BASED
    print("\nCONTENT BASED:")
    print(
        db.content_based_recommendations("Carlos")
    )

    # COLLABORATIVE FILTERING
    print("\nCOLLABORATIVE:")
    print(
        db.collaborative_filtering("Carlos")
    )

    db.close()