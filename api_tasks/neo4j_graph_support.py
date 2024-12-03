from neo4j import GraphDatabase
from typing import Dict, Any, List

class Neo4jGraphDB:
    def __init__(self, uri: str, username: str, password: str):
        """Initialize connection to Neo4j database."""
        self.driver = GraphDatabase.driver(uri, auth=(username, password))

    def close(self):
        """Close the database connection."""
        self.driver.close()

    def add_node(self, label: str, node_id: str, properties: Dict[str, Any]):
        """
        Add a node with the given label and properties.
        Example: add_node("Person", "alice", {"name": "Alice", "age": 30})
        """
        with self.driver.session() as session:
            query = (
                f"CREATE (n:{label} {{id: $node_id}}) "
                "SET n += $properties "
                "RETURN n"
            )
            return session.run(query, node_id=node_id, properties=properties)
        
    def add_nodes_batch(self, label: str, nodes_list: List[Dict]):
        """
        Add multiple nodes in batch
        
        Args:
            label: Node label for all nodes
            nodes_list: List of dictionaries containing node properties
        """
        with self.driver.session() as session:
            cypher_query = (
                f"UNWIND $nodes as node "
                f"CREATE (n:{label}) "
                "SET n = node"
            )
            session.run(cypher_query, nodes=nodes_list)

    def add_relationship(self, from_id: str, to_id: str, rel_type: str, properties: Dict[str, Any] = None, symmetrical = False, id_var:str = 'id'):
        """
        Create a relationship between two nodes.
        Example: add_relationship("alice", "bob", "KNOWS", {"since": "2020"})
        """
        if properties is None:
            properties = {}
        
        if symmetrical:
            query = (f'''
                MATCH (a), (b)
                WHERE a.{id_var} = $from_id AND b.{id_var} = $to_id
                CREATE (a)-[r1:{rel_type}]->(b)
                CREATE (b)-[r2:{rel_type}]->(a)
                SET r1 += $properties
                SET r2 += $properties
                RETURN r1, r2
                '''
            )
        else:
            query = (f'''
                MATCH (a), (b)
                WHERE a.{id_var} = $from_id AND b.{id_var} = $to_id
                CREATE (a)-[r:{rel_type}]->(b)
                SET r += $properties 
                RETURN r
                '''
            )
        with self.driver.session() as session:
            return session.run(query, from_id=from_id, to_id=to_id, properties=properties)

    def get_node(self, node_id: str):
        """Get a node by its ID."""
        with self.driver.session() as session:
            query = "MATCH (n {id: $node_id}) RETURN n"
            result = session.run(query, node_id=node_id)
            return result.single()

    def get_relationships(self, node_id: str):
        """Get all relationships for a node."""
        with self.driver.session() as session:
            query = """
            MATCH (n {id: $node_id})-[r]-(m)
            RETURN type(r) as relationship_type, 
                   startNode(r).id as from_node, 
                   endNode(r).id as to_node, 
                   properties(r) as properties
            """
            return list(session.run(query, node_id=node_id))
        

    def add_relationships_batch(self, relationships: List[Dict], symmetrical: bool = False, id_var: str = 'id'):
        """
        Create multiple relationships between nodes in batch.
        
        Args:
            relationships: List of dictionaries containing relationship information.
                        Each dict should have keys: 'from_id', 'to_id', 'rel_type', and optionally 'properties'
            symmetrical: If True, creates reciprocal relationships in both directions
            id_var: The node property to use as identifier (default: 'id')
        
        Example:
            add_relationships_batch([
                {'from_id': 'alice', 'to_id': 'bob', 'rel_type': 'KNOWS', 'properties': {'since': '2020'}},
                {'from_id': 'bob', 'to_id': 'charlie', 'rel_type': 'FOLLOWS'}
            ])
        """
        # Validate and normalize input
        normalized_rels = []
        for rel in relationships:
            normalized_rel = {
                'from_id': rel['from_id'],
                'to_id': rel['to_id'],
                'rel_type': rel['rel_type'],
                'properties': rel.get('properties', {})
            }
            normalized_rels.append(normalized_rel)

        if symmetrical:
            query = f"""
            UNWIND $rels AS rel
            MATCH (a), (b)
            WHERE a.{id_var} = rel.from_id AND b.{id_var} = rel.to_id
            CREATE (a)-[r1:`${{rel.rel_type}}`]->(b)
            CREATE (b)-[r2:`${{rel.rel_type}}`]->(a)
            SET r1 += rel.properties
            SET r2 += rel.properties
            RETURN r1, r2
            """
        else:
            query = f"""
            UNWIND $rels AS rel
            MATCH (a), (b)
            WHERE a.{id_var} = rel.from_id AND b.{id_var} = rel.to_id
            CREATE (a)-[r:`${{rel.rel_type}}`]->(b)
            SET r += rel.properties
            RETURN r
            """
        
        with self.driver.session() as session:
            return session.run(query, rels=normalized_rels)
        
    def execute_query(self, query: str, parameters: Dict[str, Any] = None):
        """Execute a custom Cypher query."""
        if parameters is None:
            parameters = {}
            
        with self.driver.session() as session:
            return list(session.run(query, parameters))

    def clear_database(self):
        """
        Clear all nodes and relationships from the database.
        USE WITH CAUTION - this will delete all data!
        """
        with self.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")

    # def find_shortest_path(self, from_id: str, to_id: str):
    #     with self.driver.session() as session:
    #         query = '''
    #             MATCH (start), (end)
    #             WHERE start.name = $from_id AND end.name = $to_id
    #             MATCH path = shortestPath((start)-[*]-(end))
    #             RETURN [node in nodes(path) | node.name] as nodes,
    #                 [relationship in relationships(path) | type(relationship)] as relationships
    #         '''
    #         result = session.run(query, from_id=from_id, to_id=to_id)
    #         record = result.single()
    #         if record:
    #             return record['nodes'], record['relationships']
    #         return None
    def find_shortest_path(self, from_id: str, to_id: str, id_var: str = 'id'):
        with self.driver.session() as session:
            query = f'''
                MATCH (start), (end)
                WHERE start.{id_var} = $from_id AND end.{id_var} = $to_id
                MATCH path = shortestPath((start)-[*]-(end))
                RETURN [node in nodes(path) | node.{id_var}] as nodes,
                    [relationship in relationships(path) | type(relationship)] as relationships
            '''
            result = session.run(query, from_id=from_id, to_id=to_id)
            record = result.single()
            if record is None:
                print(f"No path found between {from_id} and {to_id}")
                return None, None  # or you could raise an exception here
            return record['nodes'], record['relationships']
        
# Example usage
def main():
    # Initialize the database connection

    
    from basic_poligon_u import load_from_json, post_request
    import os
    import sys
    json_secrets = load_from_json(filepath=rf'{os.path.dirname(__file__)}\..\config.json')
    neo4js_password = json_secrets["neo4j_ai_devs_db_password"]

    db = Neo4jGraphDB(
        uri="neo4j://localhost:7687",  # Update with your Neo4j URI
        username="neo4j",              # Update with your username
        password=neo4js_password # Update with your password
    )
    db.clear_database()
    

    try:
        # Add nodes (people)
        db.add_node("Person", "alice", {
            "name": "Alice",
            "age": 30,
            "occupation": "Engineer"
        })
        db.add_node("Person", "bob", {
            "name": "Bob",
            "age": 35,
            "occupation": "Designer"
        })
        db.add_node("Person", "charlie", {
            "name": "Charlie",
            "age": 28,
            "occupation": "Manager"
        })

        # Add relationships
        db.add_relationship("alice", "bob", "KNOWS", {"since": "2020"})
        db.add_relationship("bob", "charlie", "WORKS_WITH", {"project": "GraphDB"})
        db.add_relationship("bob", "alice", "CONNIVES", {"since": "forever"},symmetrical=True)

        # Query example: Find all of Bob's connections
        query = """
        MATCH (p:Person {id: 'bob'})-[r]-(connected)
        RETURN type(r) as relationship, 
               connected.name as connected_person,
               properties(r) as relationship_properties
        """
        results = db.execute_query(query)
        for record in results:
            print(f"Bob {record['relationship']} {record['connected_person']}")
            print(f"Properties: {record['relationship_properties']}")

        query = """
        MATCH (p:Person {id: 'alice'})-[r]-(connected)
        RETURN type(r) as relationship, 
               connected.name as connected_person,
               properties(r) as relationship_properties
        """
        results = db.execute_query(query)
        for record in results:
            print(f"Alice {record['relationship']} {record['connected_person']}")
            print(f"Properties: {record['relationship_properties']}")

    finally:
        db.close()

if __name__ == "__main__":
    main()