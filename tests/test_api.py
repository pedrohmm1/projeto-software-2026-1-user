def test_get_user_404(client):

    # Teste de Recuperação
    get_response = client.get(f"/users/1")
    assert get_response.status_code == 404 

def test_create_and_get_user_and_delete_user(client):
    pass

def test_create_and_delete_user(client):
    pass

def test_create_two_users_and_list_and_delete_both_users(client):
    pass