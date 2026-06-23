from flask import Blueprint, jsonify, request
from sqlalchemy import text

from api.db import get_engine

trees_bp = Blueprint("trees", __name__)

@trees_bp.route("/test", methods=["GET"])
def get_test():
    return jsonify({"test": "test"})

@trees_bp.route("/trees", methods=["GET"])
def get_trees():
    """
    Returns all trees as GeoJSON for initial map render.
    Accepts optional bbox query params to limit results:
    ?min_lat=&min_lng=&max_lat=&max_lng=
    """
    engine = get_engine()

    min_lat = request.args.get("min_lat")
    max_lat = request.args.get("max_lat")
    min_lng = request.args.get("min_lng")
    max_lng = request.args.get("max_lng")

    if all([min_lat, max_lat, min_lng, max_lng]):
        query = """
            SELECT id, common_name, street_name,
                   ST_AsGeoJSON(geometry)::json AS geom
            FROM trees
            WHERE geometry && ST_MakeEnvelope(:min_lng, :min_lat, :max_lng, :max_lat, 4326)
        """
        params = {
            "min_lat": float(min_lat), "max_lat": float(max_lat),
            "min_lng": float(min_lng), "max_lng": float(max_lng)
        }
    else:
        query = """
            SELECT id, common_name, street_name,
                   ST_AsGeoJSON(geometry)::json AS geom
            FROM trees
        """
        params = {}

    with engine.connect() as conn:
        rows = conn.execute(text(query), params).fetchall()

    features = [
        {
            "type": "Feature",
            "geometry": row.geom,
            "properties": {
                "id": row.id,
                "common_name": row.common_name,
                "street_name": row.street_name,
            }
        }
        for row in rows
    ]
    return jsonify({"type": "FeatureCollection", "features": features})
