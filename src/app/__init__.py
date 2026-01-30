import os
import json
from flask import Flask, request, Response
from flask_swagger_ui import get_swaggerui_blueprint
from .database.mongo import mongo
from .provider.mail import mail
from .routes.routes import routes
from .config import Config
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS explícito para Swagger e API (evita "Failed to fetch" no /doc)
    CORS(
        app,
        resources={r"/*": {"origins": "*", "methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"], "allow_headers": ["*"], "expose_headers": ["*"]}},
        supports_credentials=False,
    )

    mongo.init_app(app)
    mail.init_app(app)

    SWAGGER_URL = "/doc"
    # Usar rota da própria app para o spec (mesma origem, evita CORS no fetch do spec)
    API_URL = "/doc/swagger.json"

    # Rota que serve o swagger.json com host/scheme dinâmicos (evita erro de URL scheme)
    static_dir = os.path.join(os.path.dirname(__file__), "static")

    @app.route("/doc/swagger.json")
    def serve_swagger_spec():
        path = os.path.join(static_dir, "swagger.json")
        with open(path, "r", encoding="utf-8") as f:
            spec = json.load(f)
        # Garantir host e scheme válidos para "Try it out"
        try:
            base = request.host_url.rstrip("/")
            if base.startswith("http://") or base.startswith("https://"):
                spec["host"] = request.host
                spec["schemes"] = [base.split(":")[0]]
        except Exception:
            pass
        return Response(
            json.dumps(spec),
            mimetype="application/json",
            headers={"Access-Control-Allow-Origin": "*"},
        )

    SWAGGERUI_BLUEPRINT = get_swaggerui_blueprint(
        SWAGGER_URL,
        API_URL,
        config={
            "app_name": "API MemoBelc",
            "docExpansion": "list",
            "filter": "true",
            "tryItOutEnabled": "true",
            "displayRequestDuration": "true",
        },
    )

    app.register_blueprint(SWAGGERUI_BLUEPRINT, url_prefix=SWAGGER_URL)
    app.register_blueprint(routes)

    return app
