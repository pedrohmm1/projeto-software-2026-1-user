from flask import Flask, request, jsonify
from db import db
from models import User
import redis
import json
import os

app = Flask(__name__)

# ✅ DATABASE (usa variável de ambiente ou fallback correto)
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv(
    "DATABASE_URL",
    "postgresql://appuser:apppass@postgres-users:5432/users"
)
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

# ✅ REDIS (usa variável de ambiente)
redis_client = redis.Redis(
    host=os.getenv("REDIS_HOST", "redis-2"),
    port=int(os.getenv("REDIS_PORT", 6379)),
    decode_responses=True
)

def send_event(event_type, description):
    event = {
        "id": None,
        "type": event_type,
        "description": description,
        "source": "USERS_API",
        "date": None
    }

    try:
        redis_client.rpush("events-queue", json.dumps(event))
    except Exception as e:
        print("Erro ao enviar evento:", e)


@app.route("/users", methods=["POST"])
def create_user():
    data = request.json

    user = User(
        name=data["name"],
        email=data["email"]
    )

    db.session.add(user)
    db.session.commit()

    send_event("CREATE_USER", f"User {user.name} created")

    return jsonify({
        "id": str(user.id),
        "name": user.name,
        "email": user.email
    }), 201


# 🔥 IMPORTANTE: removi o <uuid:...> (evita erro de conversão)
@app.route("/users/<user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    return jsonify({
        "id": str(user.id),
        "name": user.name,
        "email": user.email
    }), 200


@app.route("/users/<user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.filter_by(id=user_id).first()

    if not user:
        return jsonify({"erro": "Usuário não encontrado"}), 404

    db.session.delete(user)
    db.session.commit()

    send_event("DELETE_USER", f"User {user.id} deleted")

    return "", 204


@app.route("/users", methods=["GET"])
def list_users():
    users = User.query.all()

    send_event("LIST_USER", "List all users")

    return jsonify([
        {
            "id": str(user.id),
            "name": user.name,
            "email": user.email
        }
        for user in users
    ]), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)