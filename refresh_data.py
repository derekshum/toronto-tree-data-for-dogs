import requests
import json
import pandas as pd
import geopandas as gpd
from io import StringIO
from shapely.geometry import shape
from sqlalchemy import create_engine

# Toronto Open Data is stored in a CKAN instance. It's APIs are documented here:
# https://docs.ckan.org/en/latest/api/

# To hit our API, you'll be making requests to:
BASE_URL = "https://ckan0.cf.opendata.inter.prod-toronto.ca"

# Datasets are called "packages". Each package can contain many "resources"
# To retrieve the metadata for this package and its resources, use the package name in this page's URL:
URL = BASE_URL + "/api/3/action/package_show"

DATABASE_CONNECTION = "postgresql+psycopg://localdb:local@localhost:5434/localdb"

def refresh_data(id: str, table_name: str, column_renames: dict[str, str] = {}):
    """Refresh the data for """

    params = { "id": id}
    package = requests.get(URL, params = params).json()

    # To get resource data:
    for idx, resource in enumerate(package["result"]["resources"]):

        # for datastore_active resources:
        if resource["datastore_active"]:
            
            # To get all records in CSV format:
            url = BASE_URL + "/datastore/dump/" + resource["id"]
            resource_dump_data = requests.get(url).text
            df = pd.read_csv(StringIO(resource_dump_data))
            
            df["geometry"] = df["geometry"].apply(
                lambda geometry_str: 
                    shape(json.loads(geometry_str)) 
                    if not pd.isna(geometry_str) 
                    else None
            )
            gdf = gpd.GeoDataFrame(df, geometry="geometry", crs="EPSG:4326")
            gdf = gdf.rename(
                columns = column_renames
            )
            engine = create_engine(DATABASE_CONNECTION)
            gdf.to_postgis(
                name=table_name,
                con=engine,
                if_exists="replace",
                index=False
            )
            print(f"Refreshed {table_name} data.")

# refresh trees
refresh_data(
    "street-tree-data", 
    "trees", 
    {
        "_id": "id",
        "OBJECTID": "object_id", 
        "STRUCTID": "struct_id",
        "ADDRESS": "address", 
        "STREETNAME": "street_name", 
        "CROSSSTREET1": "cross_street_1",
        "CROSSSTREET2": "cross_street_2", 
        "SUFFIX": "suffix",
        "UNIT_NUMBER": "unit_number",
        "TREE_POSITION_NUMBER": "tree_position_number", 
        "SITE": "site",
        "WARD": "ward",
        "BOTANICAL_NAME": "botanical_name",
        "COMMON_NAME": "common_name",
        "DBH_TRUNK": "dbh_trunk",
        "geometry": "geometry"
    }
)

# refresh off leash areas
refresh_data(
    "off-leash-areas", 
    "off_leash_areas", 
    {
        "_id": "id",
        "OBJECTID": "object_id", 
        "STRUCTID": "struct_id"
    }
)
