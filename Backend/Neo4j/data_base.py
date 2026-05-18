from neo4j import GraphDatabase
import pandas as pd
from itertools import combinations

class SteamGraphDB:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(
            uri,
            auth=(user, password)
        )

    def close(self):
        self.driver.close()

    #CONSTRAINTS

    def create_constraints(self):

        with self.driver.session() as session:

            session.run("""
                CREATE CONSTRAINT game_appid IF NOT EXISTS
                FOR (g:Game)
                REQUIRE g.appid IS UNIQUE
            """)

            session.run("""
                CREATE CONSTRAINT user_name IF NOT EXISTS
                FOR (u:User)
                REQUIRE u.name IS UNIQUE
            """)

            session.run("""
                CREATE CONSTRAINT genre_name IF NOT EXISTS
                FOR (g:Genre)
                REQUIRE g.name IS UNIQUE
            """)

            session.run("""
                CREATE CONSTRAINT tag_name IF NOT EXISTS
                FOR (t:Tag)
                REQUIRE t.name IS UNIQUE
            """)

            session.run("""
                CREATE CONSTRAINT developer_name IF NOT EXISTS
                FOR (d:Developer)
                REQUIRE d.name IS UNIQUE
            """)

    #CREARR JUEGO ####################

    def create_game(self, row):

        with self.driver.session() as session:

            session.execute_write(
                lambda tx: tx.run("""

                    MERGE (g:Game {appid:$appid})

                    SET g.name = $name,
                        g.release_date = $release_date,
                        g.price = $price,
                        g.positive_ratings = $positive_ratings,
                        g.negative_ratings = $negative_ratings,
                        g.average_playtime = $average_playtime

                """,

                appid=int(row["appid"]),
                name=row["name"],
                release_date=row["release_date"],
                price=float(row["price"]),
                positive_ratings=int(row["positive_ratings"]),
                negative_ratings=int(row["negative_ratings"]),
                average_playtime=int(row["average_playtime"])
                )
            )

    #generos #################``

    def add_genres(self, appid, genres):

        if pd.isna(genres):
            return

        genre_list = str(genres).split(";")

        with self.driver.session() as session:

            for genre in genre_list:

                genre = genre.strip()

                session.execute_write(
                    lambda tx: tx.run("""

                        MATCH (g:Game {appid:$appid})

                        MERGE (ge:Genre {name:$genre})

                        MERGE (g)-[:HAS_GENRE]->(ge)

                    """,

                    appid=int(appid),
                    genre=genre
                    )
                )

    #tags ################

    def add_tags(self, appid, tags):

        if pd.isna(tags):
            return

        tag_list = str(tags).split(";")

        with self.driver.session() as session:

            for tag in tag_list:

                tag = tag.strip()

                session.execute_write(
                    lambda tx: tx.run("""

                        MATCH (g:Game {appid:$appid})

                        MERGE (t:Tag {name:$tag})

                        MERGE (g)-[:HAS_TAG]->(t)

                    """,

                    appid=int(appid),
                    tag=tag
                    )
                )

    #developers #####################

    def add_developer(self, appid, developer):

        if pd.isna(developer):
            return

        with self.driver.session() as session:

            session.execute_write(
                lambda tx: tx.run("""

                    MATCH (g:Game {appid:$appid})

                    MERGE (d:Developer {name:$developer})

                    MERGE (g)-[:DEVELOPED_BY]->(d)

                """,

                appid=int(appid),
                developer=developer
                )
            )

    #usuarios #####################

    def create_user(self, username):

        with self.driver.session() as session:

            session.execute_write(
                lambda tx: tx.run("""

                    MERGE (u:User {name:$username})

                """,

                username=username
                )
            )

    #user ratings ###################

    def add_user_rating(self, username, appid, score):

        with self.driver.session() as session:

            session.execute_write(
                lambda tx: tx.run("""

                    MATCH (u:User {name:$username})
                    MATCH (g:Game {appid:$appid})

                    MERGE (u)-[r:RATED]->(g)

                    SET r.score = $score

                """,

                username=username,
                appid=int(appid),
                score=score
                )
            )

    

    def import_games_csv(self, filepath):

        df = pd.read_csv(filepath)

        for _, row in df.iterrows():

            self.create_game(row)

            self.add_genres(
                row["appid"],
                row["genres"]
            )

            self.add_tags(
                row["appid"],
                row["steamspy_tags"]
            )

            self.add_developer(
                row["appid"],
                row["developer"]
            )

    #Jaccard similarity ##################

    def calculate_jaccard_similarity(self):

        with self.driver.session() as session:

            games = session.run("""
                MATCH (g:Game)
                RETURN g.appid AS appid
            """)

            game_ids = [r["appid"] for r in games]

            for g1, g2 in combinations(game_ids, 2):

                result = session.run("""

                    MATCH (game1:Game {appid:$g1})-[:HAS_TAG]->(t:Tag)
                    WITH game1, collect(t.name) AS tags1

                    MATCH (game2:Game {appid:$g2})-[:HAS_TAG]->(t:Tag)
                    WITH tags1, collect(t.name) AS tags2

                    RETURN tags1, tags2

                """, g1=g1, g2=g2).single()

                if result is None:
                    continue

                tags1 = set(result["tags1"])
                tags2 = set(result["tags2"])

                if len(tags1) == 0 or len(tags2) == 0:
                    continue

                intersection = len(tags1.intersection(tags2))
                union = len(tags1.union(tags2))

                score = intersection / union

                if score >= 0.3:

                    session.run("""

                        MATCH (g1:Game {appid:$g1})
                        MATCH (g2:Game {appid:$g2})

                        MERGE (g1)-[s:SIMILAR]->(g2)

                        SET s.score = $score

                    """,

                    g1=g1,
                    g2=g2,
                    score=score
                    )

    #CONTENT BASED FILTERING ##################

    def content_based_recommendations(self, username):

        with self.driver.session() as session:

            result = session.run("""

                MATCH (u:User {name:$username})-[r:RATED]->(g1:Game)

                MATCH (g1)-[s:SIMILAR]->(g2:Game)

                WHERE NOT (u)-[:RATED]->(g2)

                RETURN g2.name AS game,
                        AVG(s.score) AS similarity

                ORDER BY similarity DESC
                LIMIT 10

            """,

            username=username
            )

            return [
                {
                    "game": r["game"],
                    "similarity": r["similarity"]
                }
                for r in result
            ]

    #COLLABORATIVE FILTERING ##################

    def collaborative_filtering(self, username):

        with self.driver.session() as session:

            result = session.run("""

                MATCH (u1:User {name:$username})
                        -[:RATED]->(g:Game)
                        <-[:RATED]-(u2:User)

                WHERE u1 <> u2

                MATCH (u2)-[:RATED]->(rec:Game)

                WHERE NOT (u1)-[:RATED]->(rec)

                RETURN rec.name AS game,
                        COUNT(*) AS score

                ORDER BY score DESC
                LIMIT 10

            """,

            username=username
            )

            return [
                {
                    "game": r["game"],
                    "score": r["score"]
                }
                for r in result
            ]


