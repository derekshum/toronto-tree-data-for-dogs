from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import pandas as pd

def get_tree_count_in_territory(engine: Engine, ids: list[int]) -> int:
    """Get the total number of trees within the territory defined by tree ids provided"""
    query = """
        WITH territory AS (
            SELECT ST_ConvexHull(ST_Collect(geometry)) AS polygon
            FROM trees
            WHERE id = ANY(%(ids)s)
        )
        SELECT COUNT(*) AS count
        FROM trees
        JOIN territory
        ON ST_Intersects(trees.geometry, territory.polygon)
    """
    df = pd.read_sql(query, engine, params={"ids": ids})
    return df.iloc[0]["count"]

def get_unique_list(engine: Engine, ids: list[int], property: str) -> list[str]:
    """Get the alphabetized list of all the unique values in column of the 
    property provided"""
    query = f"""
        WITH territory AS (
            SELECT ST_ConvexHull(ST_Collect(geometry)) AS polygon
            FROM trees
            WHERE id = ANY(%(ids)s)
        )
        SELECT DISTINCT {property}
        FROM trees
        JOIN territory
        ON ST_Intersects(trees.geometry, territory.polygon)
        GROUP BY {property}
        ORDER BY {property}
    """
    df = pd.read_sql(query, engine, params={"ids": ids, "property": property})
    return df[property].tolist()

engine = create_engine("postgresql+psycopg://localdb:local@localhost:5434/localdb")
test_points = [12944, 14518, 4410]
print("Trees in territory:", get_tree_count_in_territory(engine, test_points))
print("Unique tree types in territory:", len(get_unique_list(engine, test_points, "common_name")))
print("Number of streets with trees in territory:", len(get_unique_list(engine, test_points, "street_name")))
