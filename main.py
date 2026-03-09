from flask import Flask, request, jsonify
from db import db
from models import User
import os

postgres_user = os.environ.get('POSTGRES_USER', 'appuser')
postgres_password = os.environ.get('POSTGRES_PASSWORD', 'apppass')
postgres_url = os.environ.get('POSTGRES_URL', 'localhost')

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{postgres_user}:{postgres_password}@{postgres_url}:5432/users"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db.init_app(app)

@app.route("/users", methods=["POST"])
def create_user():
    data = request.json

    user = User(
        name=data["name"],
        email=data["email"]
    )

    db.session.add(user)
    db.session.commit()

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
    }), 201

@app.route("/users/<uuid:user_id>", methods=["DELETE"])
def delete_user(user_id):
    user = User.query.get_or_404(user_id)

    db.session.delete(user)
    db.session.commit()

    return "", 204

@app.route("/users", methods=["GET"])
def list_users():
    users = User.query.all()

    return [
        {
            "id": str(user.id),
            "name": user.name,
            "email": user.email
        }
        for user in users
    ], 200

if __name__ == "__main__":
    app.run(debug=True, port=5001)