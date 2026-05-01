from sqlalchemy import create_engine
from sqlalchemy.engine import Engine
import pandas as pd
from datetime import datetime

def get_trees_in_territory(engine: Engine, ids: list[int]) -> pd.DataFrame:
    """Get the dataframe for trees within the territory defined by tree ids provided"""
    query = """
        WITH territory AS (
            SELECT ST_ConvexHull(ST_Collect(geometry)) AS polygon
            FROM trees
            WHERE id = ANY(%(ids)s)
        )
        SELECT *
        FROM trees
        JOIN territory
        ON ST_Intersects(trees.geometry, territory.polygon)
    """
    return pd.read_sql(query, engine, params={"ids": ids})

def get_off_leash_areas_in_territory(engine: Engine, ids: list[int]) -> pd.DataFrame:
    """Get the dataframe for off leash areas within the territory defined by tree ids provided"""
    query = """
        WITH territory AS (
            SELECT ST_ConvexHull(ST_Collect(geometry)) AS polygon
            FROM trees
            WHERE id = ANY(%(ids)s)
        )
        SELECT *
        FROM off_leash_areas
        JOIN territory
        ON ST_Intersects(off_leash_areas.geometry, territory.polygon)
    """
    return pd.read_sql(query, engine, params={"ids": ids})

def get_unique_list(df: pd.DataFrame, property: str) -> list[str]:
    """Get the alphabetized list of all the unique values in column of the 
    property provided"""
    return sorted(df[property].dropna().unique())

startTime = datetime.now()
engine = create_engine("postgresql+psycopg://localdb:local@localhost:5434/localdb")
test_trees = [1, 10, 100, 12944, 14518, 4410]
df = get_trees_in_territory(engine, test_trees)
print("Trees in territory: ", len(df.index))
print("Number of streets with trees in territory: ", df["street_name"].nunique())
print("Unique tree types in territory: ", df["common_name"].nunique())
print("Trees types in territory: ", get_unique_list(df, "common_name"))
off_leash_areas_df = get_off_leash_areas_in_territory(engine, test_trees)
print("Off leash areas in territory: ", off_leash_areas_df["location_name"].tolist())
print("Execution time: ", datetime.now() - startTime)
