from flask import Flask, request, jsonify
from db import db
from models import User
import redis
import json

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "postgresql://appuser:apppass@localhost:5432/users"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

redis_client = redis.Redis(
    host="localhost",
    port=6379,
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

    redis_client.rpush("events-queue", json.dumps(event))

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

@app.route("/users/<uuid:user_id>", methods=["GET"])
def get_user(user_id):
    user = User.query.get_or_404(user_id)

    return jsonify({
        "id": str(user.id),
        "name": user.name,
        "email": user.email
    }), 200

@app.route("/users/<uuid:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

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
    app.run(debug=True, port=5001)