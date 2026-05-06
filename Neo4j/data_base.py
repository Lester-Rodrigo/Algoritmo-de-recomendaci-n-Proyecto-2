from neo4j import GraphDatabase

class GrafoDB:
    
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()
        
    def create_vertex_game(self, name, price):
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("MERGE (v:Vertex {name: $name, price: $price})", name=name, price=price)
            )
            
    def create_vertex_user(self, name):
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("MERGE (u:User {name: $name})", name=name)
            )
            
    def create_vertex_vertex_edge(self, vex1, vex2):
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    MATCH (a:Vertex {name: $name1}),
                          (b:Vertex {name: $name2})
                    MERGE (a)-[:CONNECTED]->(b)
                """, name1=vex1, name2=vex2)
            )
            
    def create_user_vertex_edge(self, user_name, vertex_name):
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    MATCH (u:User {name: $user_name}),
                          (v:Vertex {name: $vertex_name})
                    MERGE (u)-[:INTERESTED_IN]->(v)
                """, user_name=user_name, vertex_name=vertex_name)
            )
    
    def get_user_interests(self, user_name):
        with self.driver.session() as session:
            return session.execute_read(
                lambda tx: [
                    f"{user_name} is interested in {r['vertex_name']} (price: {r['price']})"
                    for r in tx.run("""
                        MATCH (u:User {name: $user_name})-[:INTERESTED_IN]->(v:Vertex)
                        RETURN v.name AS vertex_name, v.price AS price
                    """, user_name=user_name)
                ]
        )
            
    def get_possible_recommendations(self, user_name):
        with self.driver.session() as session:
            return session.execute_read(
                lambda tx: [
                    f"{user_name} might also like {r['vertex_name']} (price: {r['price']})"
                    for r in tx.run("""
                        MATCH (u:User {name: $user_name})-[:INTERESTED_IN]->(v1:Vertex)-[:CONNECTED]->(v2:Vertex)
                        WHERE NOT (u)-[:INTERESTED_IN]->(v2)
                        RETURN DISTINCT v2.name AS vertex_name, v2.price AS price
                    """, user_name=user_name)
                ]
        )
            
    def get_vertex_connections(self, vertex_name):
        with self.driver.session() as session:
            return session.execute_read(
                lambda tx: [
                    f"{vertex_name} is connected to {r['connected_vertex']} (price: {r['price']})"
                    for r in tx.run("""
                        MATCH (v1:Vertex {name: $vertex_name})-[:CONNECTED]->(v2:Vertex)
                        RETURN v2.name AS connected_vertex, v2.price AS price
                    """, vertex_name=vertex_name)
                ]
        )