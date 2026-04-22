def test_get_user_404(client):
    get_response = client.get("/users/1")
    assert get_response.status_code == 404


def test_create_and_get_user_and_delete_user(client):
    create_response = client.post(
        "/users",
        json={
            "name": "Pedro",
            "email": "pedro@email.com"
        }
    )
    assert create_response.status_code == 201

    created_user = create_response.get_json()
    assert created_user["name"] == "Pedro"
    assert created_user["email"] == "pedro@email.com"
    assert "id" in created_user

    user_id = created_user["id"]

    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 200

    fetched_user = get_response.get_json()
    assert fetched_user["id"] == user_id
    assert fetched_user["name"] == "Pedro"
    assert fetched_user["email"] == "pedro@email.com"

    delete_response = client.delete(f"/users/{user_id}")
    assert delete_response.status_code == 204

    get_after_delete = client.get(f"/users/{user_id}")
    assert get_after_delete.status_code == 404


def test_create_and_delete_user(client):
    create_response = client.post(
        "/users",
        json={
            "name": "Maria",
            "email": "maria@email.com"
        }
    )
    assert create_response.status_code == 201

    created_user = create_response.get_json()
    user_id = created_user["id"]

    delete_response = client.delete(f"/users/{user_id}")
    assert delete_response.status_code == 204

    get_response = client.get(f"/users/{user_id}")
    assert get_response.status_code == 404


def test_create_two_users_and_list_and_delete_both_users(client):
    response1 = client.post(
        "/users",
        json={
            "name": "Joao",
            "email": "joao@email.com"
        }
    )
    assert response1.status_code == 201
    user1 = response1.get_json()

    response2 = client.post(
        "/users",
        json={
            "name": "Ana",
            "email": "ana@email.com"
        }
    )
    assert response2.status_code == 201
    user2 = response2.get_json()

    list_response = client.get("/users")
    assert list_response.status_code == 200

    users = list_response.get_json()
    assert len(users) == 2

    ids = [user["id"] for user in users]
    assert user1["id"] in ids
    assert user2["id"] in ids

    delete_response1 = client.delete(f"/users/{user1['id']}")
    assert delete_response1.status_code == 204

    delete_response2 = client.delete(f"/users/{user2['id']}")
    assert delete_response2.status_code == 204

    final_list_response = client.get("/users")
    assert final_list_response.status_code == 200
    assert final_list_response.get_json() == []