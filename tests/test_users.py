from fastapi import status


def test_01_get_user_details(client, seed_user):
    r = client.get("/users/getUserDetails")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    print(f'data is {data}')
    assert data["UserName"] == "sund"
    # Verify the values match what seed_user fixture creates
    assert data["FirstName"] == "Sundari"
    assert data["EmailAddress"] == "test@example.com"


def test_02_change_user_password(client, seed_user):
    r = client.post("/users/changeUserPassword?old_password=testing123?&new_password=newpass123?")
    # If the password was already changed in a prior test, this will fail with 401
    # Accept both 200 (success) and 401 (password already changed) for idempotency
    assert r.status_code == status.HTTP_200_OK

    r = client.post("/users/changeUserPassword?old_password=wrongoldpass&new_password=anothernewpass123?")
    assert r.status_code == status.HTTP_401_UNAUTHORIZED


def test_03_modify_user_details(client, seed_user):
    # Modify your own details (seed_user at ID=1)
    r = client.put("/users/modifyUserDetails", params={"first_name": "Sundari_Updated", "email_addr": "updated@example.com"})
    assert r.status_code == status.HTTP_200_OK
    assert r.json() == {"message": "User details updated successfully"}

    # Verify the updates took effect
    r = client.get("/users/getUserDetails")
    assert r.status_code == status.HTTP_200_OK
    data = r.json()
    assert data["FirstName"] == "Sundari_Updated"
    assert data["EmailAddress"] == "updated@example.com"  
