from neo4j import GraphDatabase

class GrafoDB:
    
    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()
        
    def create_vertex(self, name, price):
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("MERGE (v:Vertex {name: $name, price: $price})", name=name, price=price)
            )
            
    def create_edge(self, name1, name2):
        with self.driver.session() as session:
            session.execute_write(
                lambda tx: tx.run("""
                    MATCH (a:Vertex {name: $name1}),
                          (b:Vertex {name: $name2})
                    MERGE (a)-[:CONNECTED]->(b)
                """, name1=name1, name2=name2)
            )