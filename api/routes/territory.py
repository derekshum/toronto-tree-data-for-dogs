import pandas as pd
from flask import Blueprint, jsonify, request
from sqlalchemy import text

from api.db import get_engine

territory_bp = Blueprint("territory", __name__)

@territory_bp.route("/territory/stats", methods=["POST"])
def territory_stats():
    """
    Accepts a list of tree IDs defining the dog's territory.
    Returns stats about trees, species, streets, and off-leash areas within it.
    """
    data = request.get_json()
    ids = data.get("tree_ids", [])
    if not ids or len(ids) < 3:
        return jsonify({"error": "At least 3 tree IDs required to define a territory"}), 400

    engine = get_engine()

    tree_query = """
        WITH territory AS (
            SELECT ST_ConvexHull(ST_Collect(geometry)) AS polygon
            FROM trees
            WHERE id = ANY(:ids)
        )
        SELECT
            t.*,
            ST_Area(territory.polygon::geography) AS territory_area_m2
        FROM trees t
        JOIN territory ON ST_Intersects(t.geometry, territory.polygon)
    """
    trees_df = pd.read_sql(text(tree_query), engine, params={"ids": ids})

    off_leash_query = """
        WITH territory AS (
            SELECT ST_ConvexHull(ST_Collect(geometry)) AS polygon
            FROM trees
            WHERE id = ANY(:ids)
        )
        SELECT off_leash_areas.*
        FROM off_leash_areas
        JOIN territory ON ST_Intersects(off_leash_areas.geometry, territory.polygon)
    """
    off_leash_df = pd.read_sql(text(off_leash_query), engine, params={"ids": ids})

    area_m2 = float(trees_df["territory_area_m2"].iloc[0]) if not trees_df.empty else 0

    return jsonify({
        "territory_area_m2": round(area_m2, 1),
        "tree_count": len(trees_df),
        "street_count": int(trees_df["street_name"].nunique()),
        "species_count": int(trees_df["common_name"].nunique()),
        "species": sorted(trees_df["common_name"].dropna().unique().tolist()),
        "off_leash_areas": off_leash_df["location_name"].tolist(),
    })


@territory_bp.route("/territory/geojson", methods=["POST"])
def territory_geojson():
    """
    Returns the territory polygon and trees within it as GeoJSON,
    for rendering on the frontend map.
    """
    data = request.get_json()
    ids = data.get("tree_ids", [])
    if not ids or len(ids) < 3:
        return jsonify({"error": "At least 3 tree IDs required"}), 400

    engine = get_engine()

    query = """
        WITH territory AS (
            SELECT ST_ConvexHull(ST_Collect(geometry)) AS polygon
            FROM trees
            WHERE id = ANY(:ids)
        )
        SELECT
            json_build_object(
                'type', 'FeatureCollection',
                'features', json_agg(
                    json_build_object(
                        'type', 'Feature',
                        'geometry', ST_AsGeoJSON(t.geometry)::json,
                        'properties', json_build_object(
                            'id', t.id,
                            'common_name', t.common_name,
                            'street_name', t.street_name
                        )
                    )
                )
            ) AS geojson,
            ST_AsGeoJSON(territory.polygon)::json AS territory_polygon
        FROM trees t
        JOIN territory ON ST_Intersects(t.geometry, territory.polygon)
        GROUP BY territory.polygon
    """
    with engine.connect() as conn:
        result = conn.execute(text(query), {"ids": ids}).fetchone()

    if not result:
        return jsonify({"error": "No results found"}), 404

    return jsonify({
        "trees": result.geojson,
        "territory_polygon": result.territory_polygon,
    })
