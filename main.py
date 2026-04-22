from flask import Flask, request, jsonify
from flask_cors import CORS
from db import db
from models import User
import os
import jwt
from jwt import PyJWKClient

AUTH0_DOMAIN = "dev-ms8hzcq7g2ruglnt.us.auth0.com"
API_AUDIENCE = "https://users-api"
ISSUER = f"https://{AUTH0_DOMAIN}/"
NAMESPACE = "https://social-insper.com/"


def create_app():
    app = Flask(__name__)

    CORS(app, resources={
        r"/*": {
            "origins": [
                "http://localhost:5173",
                "http://127.0.0.1:5173",
                "https://projeto-software-2026-1-front-teal.vercel.app"
            ]
        }
    })

    postgres_user = os.environ.get("POSTGRES_USER", "appuser")
    postgres_password = os.environ.get("POSTGRES_PASSWORD", "apppass")
    postgres_url = os.environ.get("POSTGRES_URL", "localhost")

    db_uri = f"postgresql://{postgres_user}:{postgres_password}@{postgres_url}:5432/users"
    app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("SQLALCHEMY_DATABASE_URI", db_uri)
    app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

    db.init_app(app)

    jwks_url = f"https://{AUTH0_DOMAIN}/.well-known/jwks.json"
    jwk_client = PyJWKClient(jwks_url)

    def get_token_from_header():
        auth_header = request.headers.get("Authorization")

        if not auth_header:
            raise Exception("Authorization header ausente")

        parts = auth_header.split()

        if len(parts) != 2 or parts[0] != "Bearer":
            raise Exception("Authorization header inválido")

        return parts[1]

    def verify_token(token):
        signing_key = jwk_client.get_signing_key_from_jwt(token)

        payload = jwt.decode(
            token,
            signing_key.key,
            algorithms=["RS256"],
            audience=API_AUDIENCE,
            issuer=ISSUER
        )

        return payload

    def require_auth():
        token = get_token_from_header()
        return verify_token(token)

    def require_admin():
        payload = require_auth()
        roles = payload.get(f"{NAMESPACE}roles", [])

        if "ADMIN" not in roles:
            raise PermissionError("Apenas ADMIN pode executar esta ação")

        return payload

    @app.route("/public", methods=["GET"])
    def public():
        return jsonify({"message": "rota publica"}), 200

    @app.route("/me", methods=["GET"])
    def me():
        try:
            payload = require_auth()
            return jsonify({
                "sub": payload.get("sub"),
                "email": payload.get(f"{NAMESPACE}email"),
                "roles": payload.get(f"{NAMESPACE}roles", [])
            }), 200
        except Exception as e:
            return jsonify({"error": str(e)}), 401

    @app.route("/users", methods=["POST"])
    def create_user():
        try:
            require_auth()

            data = request.get_json()

            if not data or "name" not in data or "email" not in data:
                return jsonify({"error": "name e email são obrigatórios"}), 400

            user = User(name=data["name"], email=data["email"])
            db.session.add(user)
            db.session.commit()

            return jsonify({
                "id": str(user.id),
                "name": user.name,
                "email": user.email
            }), 201

        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 401

    @app.route("/users", methods=["GET"])
    def get_users():
        try:
            require_auth()

            users = User.query.all()

            return jsonify([
                {
                    "id": str(user.id),
                    "name": user.name,
                    "email": user.email
                }
                for user in users
            ]), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 401

    @app.route("/users/<user_id>", methods=["GET"])
    def get_user(user_id):
        try:
            require_auth()

            user = db.session.get(User, user_id)

            if not user:
                return jsonify({"error": "usuário não encontrado"}), 404

            return jsonify({
                "id": str(user.id),
                "name": user.name,
                "email": user.email
            }), 200

        except Exception as e:
            return jsonify({"error": str(e)}), 401

    @app.route("/users/<user_id>", methods=["DELETE"])
    def delete_user(user_id):
        try:
            require_admin()

            user = db.session.get(User, user_id)

            if not user:
                return jsonify({"error": "usuário não encontrado"}), 404

            db.session.delete(user)
            db.session.commit()

            return jsonify({"message": "usuário deletado com sucesso"}), 200

        except PermissionError as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 403
        except Exception as e:
            db.session.rollback()
            return jsonify({"error": str(e)}), 401

    with app.app_context():
        db.create_all()

    return app


app = create_app()

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5003, debug=True)