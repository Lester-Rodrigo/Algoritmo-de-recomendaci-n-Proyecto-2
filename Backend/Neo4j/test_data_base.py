from neo4j import GraphDatabase

driver = GraphDatabase.driver(
    "bolt://localhost:7687",
    auth=("neo4j", "qwertyui")
)

with driver.session() as session:
    result = session.run("RETURN 'Connected' AS msg")
    print(result.single()["msg"])

driver.close()