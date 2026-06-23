from flask import Flask

from api.routes.territory import territory_bp
from api.routes.trees import trees_bp


def create_app():
    app = Flask(__name__)
    app.register_blueprint(territory_bp)
    app.register_blueprint(trees_bp)
    return app

if __name__ == "__main__":
    app = create_app()
    app.run(debug=True, host="0.0.0.0", port=5000)
