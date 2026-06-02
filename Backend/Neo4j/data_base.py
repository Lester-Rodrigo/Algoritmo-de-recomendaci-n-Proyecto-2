from neo4j import GraphDatabase
import pandas as pd
from itertools import combinations


class SteamGraphDB:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_constraints(self):
        with self.driver.session() as session:
            session.run("""
                CREATE CONSTRAINT game_appid IF NOT EXISTS
                FOR (g:Game) REQUIRE g.appid IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT user_name IF NOT EXISTS
                FOR (u:User) REQUIRE u.name IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT genre_name IF NOT EXISTS
                FOR (g:Genre) REQUIRE g.name IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT tag_name IF NOT EXISTS
                FOR (t:Tag) REQUIRE t.name IS UNIQUE
            """)
            session.run("""
                CREATE CONSTRAINT developer_name IF NOT EXISTS
                FOR (d:Developer) REQUIRE d.name IS UNIQUE
            """)

    
    def create_game(self, row):
        try:
            price = float(row["price"])
        except (ValueError, TypeError):
            price = 0.0

        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    MERGE (g:Game {appid: $appid})
                    SET g.name             = $name,
                        g.release_date     = $release_date,
                        g.price            = $price,
                        g.positive_ratings = $positive_ratings,
                        g.negative_ratings = $negative_ratings,
                        g.average_playtime = $average_playtime
                """,
                appid=int(row["appid"]),
                name=str(row["name"]),
                release_date=str(row["release_date"]),
                price=price,
                positive_ratings=int(row["positive_ratings"]),
                negative_ratings=int(row["negative_ratings"]),
                average_playtime=int(row["average_playtime"]),
                )
            )

    def add_genres(self, appid, genres):
        if pd.isna(genres):
            return
        genre_list = [g.strip() for g in str(genres).split(";") if g.strip()]
        with self.driver.session() as session:
            for genre in genre_list:
                session.execute_write(
                    lambda tx, g=genre: tx.run("""
                        MATCH (game:Game {appid: $appid})
                        MERGE (ge:Genre {name: $genre})
                        MERGE (game)-[:HAS_GENRE]->(ge)
                    """, appid=int(appid), genre=g)
                )

    def add_tags(self, appid, tags):
        if pd.isna(tags):
            return
        tag_list = [t.strip() for t in str(tags).split(";") if t.strip()]
        with self.driver.session() as session:
            for tag in tag_list:
                session.execute_write(
                    lambda tx, t=tag: tx.run("""
                        MATCH (game:Game {appid: $appid})
                        MERGE (tg:Tag {name: $tag})
                        MERGE (game)-[:HAS_TAG]->(tg)
                    """, appid=int(appid), tag=t)
                )

    def add_developer(self, appid, developer):
        if pd.isna(developer):
            return
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    MATCH (game:Game {appid: $appid})
                    MERGE (d:Developer {name: $developer})
                    MERGE (game)-[:DEVELOPED_BY]->(d)
                """, appid=int(appid), developer=str(developer))
            )

    def get_all_games(self, limit: int = 100, offset: int = 0):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:Game)
                RETURN g.appid AS appid, g.name AS name,
                       g.price AS price, g.release_date AS release_date,
                       g.positive_ratings AS positive_ratings,
                       g.negative_ratings AS negative_ratings,
                       g.average_playtime AS average_playtime
                ORDER BY g.name
                SKIP $offset LIMIT $limit
            """, limit=limit, offset=offset)
            return [dict(r) for r in result]

    def get_game(self, appid: int):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:Game {appid: $appid})
                OPTIONAL MATCH (g)-[:HAS_GENRE]->(ge:Genre)
                OPTIONAL MATCH (g)-[:HAS_TAG]->(t:Tag)
                OPTIONAL MATCH (g)-[:DEVELOPED_BY]->(d:Developer)
                RETURN g.appid AS appid, g.name AS name,
                       g.price AS price, g.release_date AS release_date,
                       g.positive_ratings AS positive_ratings,
                       g.negative_ratings AS negative_ratings,
                       g.average_playtime AS average_playtime,
                       collect(DISTINCT ge.name) AS genres,
                       collect(DISTINCT t.name)  AS tags,
                       collect(DISTINCT d.name)  AS developers
            """, appid=appid).single()
            return dict(result) if result else None

    def search_games(self, query: str, limit: int = 20):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (g:Game)
                WHERE toLower(g.name) CONTAINS toLower($query)
                RETURN g.appid AS appid, g.name AS name,
                       g.price AS price, g.release_date AS release_date,
                       g.positive_ratings AS positive_ratings,
                       g.negative_ratings AS negative_ratings
                ORDER BY g.positive_ratings DESC
                LIMIT $limit
            """, query=query, limit=limit)
            return [dict(r) for r in result]

    # usuarios
    #sql lite se encarga de la autenticacion, pero el grafo necesita saber que usuarios existen para crear las relaciones RATED

    def create_user(self, username: str):
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run(
                    "MERGE (u:User {name: $username})",
                    username=username,
                )
            )

    def user_exists_in_graph(self, username: str) -> bool:
        with self.driver.session() as session:
            result = session.run(
                "MATCH (u:User {name: $username}) RETURN u LIMIT 1",
                username=username,
            ).single()
            return result is not None


    
    #cuando un usuario califica un juego, se crea una relación RATED en el grafo:
    #   (:User {name})-[:RATED {score}]->(:Game {appid})
    # de aqui se sacan las recomendaciones content-based y colaborativas

    def add_user_rating(self, username: str, appid: int, score: float):
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    MATCH (u:User {name: $username})
                    MATCH (g:Game {appid: $appid})
                    MERGE (u)-[r:RATED]->(g)
                    SET r.score = $score
                """, username=username, appid=int(appid), score=score)
            )

    def get_user_ratings(self, username: str):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {name: $username})-[r:RATED]->(g:Game)
                RETURN g.appid AS appid, g.name AS name, r.score AS score
                ORDER BY r.score DESC
            """, username=username)
            return [dict(r) for r in result]

    def remove_user_rating(self, username: str, appid: int):
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    MATCH (u:User {name: $username})-[r:RATED]->(g:Game {appid: $appid})
                    DELETE r
                """, username=username, appid=int(appid))
            )


    def import_games_csv(self, filepath: str, limit: int = 100): 
        df = pd.read_csv(filepath).head(limit)
        total = len(df)
        for i, (_, row) in enumerate(df.iterrows(), 1):
            self.create_game(row)
            self.add_genres(row["appid"], row.get("genres"))
            # steamspy_tags columna usada para Jaccard 
            self.add_tags(row["appid"], row.get("steamspy_tags"))
            self.add_developer(row["appid"], row.get("developer"))
            if i % 100 == 0:
                print(f"  Imported {i}/{total} games...")
        print(f"  Done — {total} games imported.")

    # Compara cada oar de juegos por sus tags  
    # If overlap >= 0.3, creates: (:Game)-[:SIMILAR {score}]->(:Game)

    def calculate_jaccard_similarity(self):
        with self.driver.session() as session:
            game_ids = [r["appid"] for r in
                        session.run("MATCH (g:Game) RETURN g.appid AS appid")]
            pairs = list(combinations(game_ids, 2))
            total = len(pairs)

            for i, (g1, g2) in enumerate(pairs, 1):
                result = session.run("""
                    MATCH (game1:Game {appid: $g1})-[:HAS_TAG]->(t1:Tag)
                    WITH collect(t1.name) AS tags1
                    MATCH (game2:Game {appid: $g2})-[:HAS_TAG]->(t2:Tag)
                    WITH tags1, collect(t2.name) AS tags2
                    RETURN tags1, tags2
                """, g1=g1, g2=g2).single()

                if i % 500 == 0:
                    print(f"  Jaccard: {i}/{total} pairs...")

                if result is None:
                    continue

                tags1 = set(result["tags1"])
                tags2 = set(result["tags2"])
                if not tags1 or not tags2:
                    continue

                score = len(tags1 & tags2) / len(tags1 | tags2)

                if score >= 0.3:
                    session.run("""
                        MATCH (g1:Game {appid: $g1})
                        MATCH (g2:Game {appid: $g2})
                        MERGE (g1)-[s:SIMILAR]->(g2)
                        SET s.score = $score
                    """, g1=g1, g2=g2, score=score)

            print(f"  Jaccard done — {total} pairs evaluated.")
    
    def add_game_to_library(self, username: str, appid: int):
        with self.driver.session() as session:
            session.run("""
                MATCH (u:User {name:$username})
                MATCH (g:Game {appid:$appid})
                MERGE (u)-[:OWNS]->(g)
            """,
            username=username,
            appid=int(appid))
    
    def get_user_library(self, username: str):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {name:$username})-[:OWNS]->(g:Game)
                RETURN g.appid AS appid,
                    g.name AS name
                ORDER BY g.name
            """,
            username=username)

            return [dict(r) for r in result]

    def rate_game_like(self, username: str, appid: int):

        with self.driver.session() as session:

            session.run("""
                MATCH (u:User {name:$username})
                MATCH (g:Game {appid:$appid})

                MERGE (u)-[r:RATED]->(g)
                SET r.score = 1

                WITH u,g

                MATCH (g)-[:HAS_GENRE]->(genre:Genre)

                MERGE (u)-[p:PREFERENCE]->(genre)

                ON CREATE SET p.weight = 1
                ON MATCH SET p.weight = p.weight + 1
            """,
            username=username,
            appid=int(appid))

    def rate_game_dislike(self, username: str, appid: int):

        with self.driver.session() as session:

            session.run("""
                MATCH (u:User {name:$username})
                MATCH (g:Game {appid:$appid})

                MERGE (u)-[r:RATED]->(g)
                SET r.score = -1

                WITH u,g

                MATCH (g)-[:HAS_GENRE]->(genre:Genre)

                MERGE (u)-[p:PREFERENCE]->(genre)

                ON CREATE SET p.weight = -1
                ON MATCH SET p.weight = p.weight - 1
            """,
            username=username,
            appid=int(appid))
    
    def preference_recommendations(self, username: str):

        with self.driver.session() as session:

            result = session.run("""
                MATCH (u:User {name:$username})

                MATCH (candidate:Game)-[:HAS_GENRE]->(genre:Genre)

                MATCH (u)-[p:PREFERENCE]->(genre)

                WHERE NOT EXISTS(
                    (u)-[:OWNS]->(candidate)
                )

                WITH candidate,
                    SUM(p.weight) AS score

                RETURN candidate.appid AS appid,
                    candidate.name AS name,
                    score

                ORDER BY score DESC

                LIMIT 20
            """,
            username=username)

            return [dict(r) for r in result]
        
#recomendaciones ////////////////////////////////////////////////////////////////////////////

    def content_based_recommendations(self, username: str):

        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {name: $username})-[:RATED]->(g1:Game)
                MATCH (g1)-[s:SIMILAR]->(g2:Game)
                WHERE NOT (u)-[:RATED]->(g2)
                RETURN g2.appid      AS appid,
                       g2.name       AS game,
                       g2.price      AS price,
                       AVG(s.score)  AS similarity
                ORDER BY similarity DESC
                LIMIT 10
            """, username=username)
            return [dict(r) for r in result]

    def collaborative_filtering(self, username: str):

        with self.driver.session() as session:
            result = session.run("""
                MATCH (u1:User {name: $username})-[:RATED]->(g:Game)<-[:RATED]-(u2:User)
                WHERE u1 <> u2
                MATCH (u2)-[:RATED]->(rec:Game)
                WHERE NOT (u1)-[:RATED]->(rec)
                RETURN rec.appid  AS appid,
                       rec.name   AS game,
                       rec.price  AS price,
                       COUNT(*)   AS score
                ORDER BY score DESC
                LIMIT 10
            """, username=username)
            return [dict(r) for r in result]

    def hybrid_recommendations(self, username: str):
#deduplica por id
        cb     = {r["appid"]: {**r, "source": "content"}
                  for r in self.content_based_recommendations(username)}
        collab = {r["appid"]: {**r, "source": "collaborative"}
                  for r in self.collaborative_filtering(username)}

        # content-based wgana si hay conflicto. se suman las puntuaciones para ordenar 
        merged = {**collab, **cb}
        return sorted(
            merged.values(),
            key=lambda x: x.get("similarity", 0) + x.get("score", 0),
            reverse=True
        )[:10]