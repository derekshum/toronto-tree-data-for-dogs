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
base_url = "https://ckan0.cf.opendata.inter.prod-toronto.ca"

# Datasets are called "packages". Each package can contain many "resources"
# To retrieve the metadata for this package and its resources, use the package name in this page's URL:
url = base_url + "/api/3/action/package_show"
params = { "id": "street-tree-data"}
package = requests.get(url, params = params).json()

# To get resource data:
for idx, resource in enumerate(package["result"]["resources"]):

    # for datastore_active resources:
    if resource["datastore_active"]:

        # To get all records in CSV format:
        url = base_url + "/datastore/dump/" + resource["id"]
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
            columns = {
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
        engine = create_engine("postgresql+psycopg://localdb:local@localhost:5434/localdb")
        gdf.to_postgis(
            name="trees",
            con=engine,
            if_exists="replace",
            index=False
        )
        print("Refreshed tree data.")
