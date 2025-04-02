from neo4j import GraphDatabase
import classification

URI = "bolt://localhost:7687"
AUTH = ("neo4j", "Rmkmrmkm0107")

steps = [
    "x^2 + 8x + 2 = 0",
    "x^2 + 2x + x + 2",
    "x^2 + x + 2x + 2",
    "x(x+2) + 1(x+2) = 0",
    "(x+1)(x+2) = 0",
    "x = -1",
    "x = -2"
]

def process_steps(steps):
    driver = GraphDatabase.driver(URI, auth=AUTH)
    prev_step_id = None

    with driver.session() as session:
        print(f"DEBUG: Full classified_steps dictionary → {classification.classified_steps}")

        for i, step in enumerate(steps):
            try:
                if isinstance(classification.classified_steps, dict):
                    step_label = classification.classified_steps.get(step.strip(), "Uncategorized")
                else:
                    raise TypeError("classification.classified_steps is not a dictionary!")

                print(f"DEBUG: Step {i+1} → {step} → Category: {step_label}")

                query = """
                MERGE (s:Steps {id: $step_id, expression: $expression, name: $category})
                RETURN s.id
                """
                step_id = session.run(query, step_id=i+1, expression=step, category=step_label).single()[0]

                if prev_step_id is not None:
                    session.run("""
                    MATCH (s1:Steps {id: $prev_step_id}), (s2:Steps {id: $step_id})
                    MERGE (s1)-[:NEXT]->(s2)
                    """, prev_step_id=prev_step_id, step_id=step_id)

                prev_step_id = i + 1

            except Exception as e:
                print(f"❌ Error processing step {i+1}: {step} → {e}")

    driver.close()


process_steps(steps)
