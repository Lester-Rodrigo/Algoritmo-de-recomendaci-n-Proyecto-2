from neo4j import GraphDatabase
import pandas as pd
import ast
from itertools import combinations


class SteamGraphDB:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    

    def create_constraints(self):
        with self.driver.session() as session:
            session.run("CREATE CONSTRAINT game_appid IF NOT EXISTS FOR (g:Game) REQUIRE g.appid IS UNIQUE")
            session.run("CREATE CONSTRAINT user_name IF NOT EXISTS FOR (u:User) REQUIRE u.name IS UNIQUE")
            session.run("CREATE CONSTRAINT genre_name IF NOT EXISTS FOR (g:Genre) REQUIRE g.name IS UNIQUE")
            session.run("CREATE CONSTRAINT tag_name IF NOT EXISTS FOR (t:Tag) REQUIRE t.name IS UNIQUE")
            session.run("CREATE CONSTRAINT developer_name IF NOT EXISTS FOR (d:Developer) REQUIRE d.name IS UNIQUE")

    # GAMES ///////////////////////////////////////////

    def create_game(self, row):
        try:
            price = float(row["price"])
        except (ValueError, TypeError):
            price = 0.0
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    MERGE (g:Game {appid: $appid})
                    SET g.name = $name, g.release_date = $release_date,
                        g.price = $price, g.positive_ratings = $positive_ratings,
                        g.negative_ratings = $negative_ratings,
                        g.average_playtime = $average_playtime
                """,
                appid=int(row["appid"]), name=str(row["name"]),
                release_date=str(row["release_date"]), price=price,
                positive_ratings=int(row["positive_ratings"]),
                negative_ratings=int(row["negative_ratings"]),
                average_playtime=int(row["average_playtime"]))
            )

    def add_genres(self, appid, genres):
        if pd.isna(genres):
            return
        for genre in [g.strip() for g in str(genres).split(";") if g.strip()]:
            with self.driver.session() as session:
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
        for tag in [t.strip() for t in str(tags).split(";") if t.strip()]:
            with self.driver.session() as session:
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
            result = session.run(
                "MATCH (g:Game) "
                "RETURN g.appid AS appid, g.name AS name, g.price AS price, "
                "g.release_date AS release_date, "
                "g.positive_ratings AS positive_ratings, "
                "g.negative_ratings AS negative_ratings, "
                "g.average_playtime AS average_playtime "
                "ORDER BY g.name SKIP $offset LIMIT $limit",
                limit=int(limit), offset=int(offset)
            )
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
            result = session.run(
                "MATCH (g:Game) WHERE toLower(g.name) CONTAINS toLower($query) "
                "RETURN g.appid AS appid, g.name AS name, g.price AS price, "
                "g.release_date AS release_date, "
                "g.positive_ratings AS positive_ratings, "
                "g.negative_ratings AS negative_ratings "
                "ORDER BY positive_ratings DESC LIMIT $limit",
                query=query, limit=int(limit)
            )
            return [dict(r) for r in result]

    def get_all_genres(self):
        with self.driver.session() as session:
            result = session.run("MATCH (ge:Genre) RETURN ge.name AS name ORDER BY ge.name")
            return [r["name"] for r in result]

    def get_games_by_genre(self, genre: str, limit: int = 50):
        with self.driver.session() as session:
            result = session.run(
                "MATCH (g:Game)-[:HAS_GENRE]->(ge:Genre {name: $genre}) "
                "RETURN g.appid AS appid, g.name AS name, g.price AS price, "
                "g.release_date AS release_date, "
                "g.positive_ratings AS positive_ratings, "
                "g.negative_ratings AS negative_ratings "
                "ORDER BY positive_ratings DESC LIMIT $limit",
                genre=genre, limit=int(limit)
            )
            return [dict(r) for r in result]

    # MEDIA Y DESC

    def load_media(self, media_csv: str, desc_csv: str):
        self._media = {}
        self._descriptions = {}
        try:
            df = pd.read_csv(media_csv)
            for _, row in df.iterrows():
                appid = int(row["steam_appid"])
                screenshots = []
                try:
                    shots = ast.literal_eval(row["screenshots"]) if pd.notna(row.get("screenshots")) else []
                    screenshots = [s.get("path_full", "") for s in shots if isinstance(s, dict)][:5]
                except Exception:
                    pass
                self._media[appid] = {
                    "header_image": str(row.get("header_image") or ""),
                    "background":   str(row.get("background")   or ""),
                    "screenshots":  screenshots,
                }
            print(f"  Media loaded: {len(self._media)} entries.")
        except Exception as e:
            print(f"  Warning: media CSV: {e}")
        try:
            df = pd.read_csv(desc_csv)
            for _, row in df.iterrows():
                appid = int(row["steam_appid"])
                self._descriptions[appid] = {
                    "short_description":    str(row.get("short_description")    or ""),
                    "detailed_description": str(row.get("detailed_description") or ""),
                }
            print(f"  Descriptions loaded: {len(self._descriptions)} entries.")
        except Exception as e:
            print(f"  Warning: desc CSV: {e}")

    def get_game_media(self, appid: int):
        media = getattr(self, "_media", {}).get(appid, {})
        desc  = getattr(self, "_descriptions", {}).get(appid, {})
        return {**media, **desc}

    # USERS ///////////////////////////////////////////

    def create_user(self, username: str):
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("MERGE (u:User {name: $username})", username=username)
            )

    def user_exists_in_graph(self, username: str) -> bool:
        with self.driver.session() as session:
            result = session.run(
                "MATCH (u:User {name: $username}) RETURN u LIMIT 1", username=username
            ).single()
            return result is not None

    # PREFERENCES ///////////////////////////////////////////   

    def add_user_genres(self, username: str, genres: list):
        with self.driver.session() as session:
            for genre in genres:
                session.execute_write(
                    lambda tx, g=genre: tx.run("""
                        MATCH (u:User {name: $username})
                        MERGE (ge:Genre {name: $genre})
                        MERGE (u)-[:LIKES]->(ge)
                    """, username=username, genre=g)
                )

    def get_user_genres(self, username: str):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {name: $username})-[:LIKES]->(ge:Genre)
                RETURN ge.name AS genre
            """, username=username)
            return [r["genre"] for r in result]

    # LIKES/DISLIKES ///////////////////////////////////////////

    def like_game(self, username: str, appid: int):
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    MATCH (u:User {name: $username})
                    MATCH (g:Game {appid: $appid})
                    MERGE (u)-[:LIKED]->(g)
                    WITH u, g
                    OPTIONAL MATCH (u)-[d:DISLIKED]->(g)
                    DELETE d
                """, username=username, appid=appid)
            )

    def dislike_game(self, username: str, appid: int):
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    MATCH (u:User {name: $username})
                    MATCH (g:Game {appid: $appid})
                    MERGE (u)-[:DISLIKED]->(g)
                    WITH u, g
                    OPTIONAL MATCH (u)-[l:LIKED]->(g)
                    DELETE l
                """, username=username, appid=appid)
            )

    def remove_reaction(self, username: str, appid: int):
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    MATCH (u:User {name: $username})-[r:LIKED|DISLIKED]->(g:Game {appid: $appid})
                    DELETE r
                """, username=username, appid=appid)
            )

    def get_user_reactions(self, username: str):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {name: $username})-[r:LIKED|DISLIKED]->(g:Game)
                RETURN g.appid AS appid, g.name AS name,
                       g.price AS price, type(r) AS reaction
            """, username=username)
            return [dict(r) for r in result]

    def get_game_reaction(self, username: str, appid: int):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {name: $username})-[r:LIKED|DISLIKED]->(g:Game {appid: $appid})
                RETURN type(r) AS reaction
            """, username=username, appid=appid).single()
            return result["reaction"] if result else None

    # WISHLIST /////////////////////////////////////////////////////

    def add_to_wishlist(self, username: str, appid: int):
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    MATCH (u:User {name: $username})
                    MATCH (g:Game {appid: $appid})
                    MERGE (u)-[:WISHLISTED]->(g)
                """, username=username, appid=appid)
            )

    def remove_from_wishlist(self, username: str, appid: int):
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    MATCH (u:User {name: $username})-[r:WISHLISTED]->(g:Game {appid: $appid})
                    DELETE r
                """, username=username, appid=appid)
            )

    def get_wishlist(self, username: str):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {name: $username})-[:WISHLISTED]->(g:Game)
                RETURN g.appid AS appid, g.name AS name, g.price AS price,
                       g.release_date AS release_date,
                       g.positive_ratings AS positive_ratings,
                       g.negative_ratings AS negative_ratings
                ORDER BY g.name
            """, username=username)
            return [dict(r) for r in result]

    def is_wishlisted(self, username: str, appid: int) -> bool:
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {name: $username})-[:WISHLISTED]->(g:Game {appid: $appid})
                RETURN g LIMIT 1
            """, username=username, appid=appid).single()
            return result is not None

    # RATINGS //////////////////////////////////////////////////////

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

    # IMPORT

    def import_games_csv(self, filepath: str, limit: int = 100):
        df = pd.read_csv(filepath).head(limit)
        total = len(df)
        for i, (_, row) in enumerate(df.iterrows(), 1):
            self.create_game(row)
            self.add_genres(row["appid"], row.get("genres"))
            self.add_tags(row["appid"], row.get("steamspy_tags"))
            self.add_developer(row["appid"], row.get("developer"))
            if i % 100 == 0:
                print(f"  Imported {i}/{total} games...")
        print(f"  Done — {total} games imported.")

    # SIMILARITY //////////////////////////////////////


    def calculate_similarity(self):
        with self.driver.session() as session:
            rows = session.run("""
                MATCH (g:Game)
                OPTIONAL MATCH (g)-[:HAS_TAG]->(t:Tag)
                OPTIONAL MATCH (g)-[:HAS_GENRE]->(ge:Genre)
                OPTIONAL MATCH (g)-[:DEVELOPED_BY]->(d:Developer)
                RETURN g.appid AS appid, g.price AS price,
                       collect(DISTINCT t.name)  AS tags,
                       collect(DISTINCT ge.name) AS genres,
                       collect(DISTINCT d.name)  AS developers
            """)
            games = {r["appid"]: dict(r) for r in rows}

        pairs = list(combinations(games.keys(), 2))
        total = len(pairs)
        similar = 0

        with self.driver.session() as session:
            for i, (id1, id2) in enumerate(pairs, 1):
                g1, g2 = games[id1], games[id2]

                tags1, tags2 = set(g1["tags"]), set(g2["tags"])
                tag_score = len(tags1 & tags2) / len(tags1 | tags2) if tags1 and tags2 else 0.0

                genres1, genres2 = set(g1["genres"]), set(g2["genres"])
                genre_score = len(genres1 & genres2) / len(genres1 | genres2) if genres1 and genres2 else 0.0

                dev_score = 1.0 if set(g1["developers"]) & set(g2["developers"]) else 0.0

                try:
                    price_diff = abs(float(g1["price"]) - float(g2["price"]))
                    price_score = max(0.0, 1.0 - price_diff / 60.0)
                except (TypeError, ValueError):
                    price_score = 0.0

                score = tag_score * 0.5 + genre_score * 0.3 + dev_score * 0.1 + price_score * 0.1

                if score >= 0.2:
                    similar += 1
                    session.run("""
                        MATCH (g1:Game {appid: $g1})
                        MATCH (g2:Game {appid: $g2})
                        MERGE (g1)-[s:SIMILAR]->(g2)
                        SET s.score = $score
                    """, g1=id1, g2=id2, score=score)

                if i % 500 == 0:
                    print(f"  Similarity: {i}/{total} pairs ({similar} similar so far)...")

        print(f"  Done — {total} pairs, {similar} similar edges created.")

    # RECOMMENDATIONS ///////////////////////////////////////////

    def content_based_recommendations(self, username: str):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {name: $username})
                OPTIONAL MATCH (u)-[:RATED]->(rated:Game)
                OPTIONAL MATCH (u)-[:LIKED]->(liked:Game)
                WITH u, collect(DISTINCT rated) + collect(DISTINCT liked) AS seeds
                UNWIND seeds AS seed
                MATCH (seed)-[s:SIMILAR]->(rec:Game)
                WHERE NOT (u)-[:RATED]->(rec)
                  AND NOT (u)-[:LIKED]->(rec)
                  AND NOT (u)-[:DISLIKED]->(rec)
                RETURN rec.appid AS appid, rec.name AS game,
                       rec.price AS price, AVG(s.score) AS similarity
                ORDER BY similarity DESC LIMIT 10
            """, username=username)
            recs = [dict(r) for r in result]

            if not recs:
                result = session.run("""
                    MATCH (u:User {name: $username})-[:LIKES]->(ge:Genre)
                    MATCH (g:Game)-[:HAS_GENRE]->(ge)
                    WHERE NOT (u)-[:DISLIKED]->(g)
                    RETURN g.appid AS appid, g.name AS game,
                           g.price AS price, 0.5 AS similarity,
                           g.positive_ratings AS pos
                    ORDER BY pos DESC LIMIT 10
                """, username=username)
                recs = [dict(r) for r in result]

            return recs

    def collaborative_filtering(self, username: str):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u1:User {name: $username})-[:RATED|LIKED]->(g:Game)
                      <-[:RATED|LIKED]-(u2:User)
                WHERE u1 <> u2
                MATCH (u2)-[:RATED|LIKED]->(rec:Game)
                WHERE NOT (u1)-[:RATED]->(rec)
                  AND NOT (u1)-[:LIKED]->(rec)
                  AND NOT (u1)-[:DISLIKED]->(rec)
                RETURN rec.appid AS appid, rec.name AS game,
                       rec.price AS price, COUNT(*) AS score
                ORDER BY score DESC LIMIT 10
            """, username=username)
            return [dict(r) for r in result]

    def hybrid_recommendations(self, username: str):
        cb     = {r["appid"]: {**r, "source": "content"}
                  for r in self.content_based_recommendations(username)}
        collab = {r["appid"]: {**r, "source": "collaborative"}
                  for r in self.collaborative_filtering(username)}
        merged = {**collab, **cb}
        return sorted(
            merged.values(),
            key=lambda x: x.get("similarity", 0) + x.get("score", 0),
            reverse=True
        )[:10]

    def expanded_recommendations(self, username: str, limit: int = 10):
        with self.driver.session() as session:
            result = session.run("""
                MATCH (u:User {name: $username})-[:LIKES]->(ge:Genre)
                MATCH (seed:Game)-[:HAS_GENRE]->(ge)
                OPTIONAL MATCH (seed)-[s:SIMILAR]->(rec:Game)
                WHERE NOT (u)-[:DISLIKED]->(rec)
                RETURN COALESCE(rec.appid,  seed.appid) AS appid,
                       COALESCE(rec.name,   seed.name)  AS game,
                       COALESCE(rec.price,  seed.price) AS price,
                       SUM(COALESCE(s.score, 1))        AS score
                ORDER BY score DESC LIMIT $limit
            """, username=username, limit=limit)
            return [dict(r) for r in result]