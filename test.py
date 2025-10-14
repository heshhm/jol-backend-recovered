import requests
import json
import textwrap

BASE_URL = "http://127.0.0.1:8000/api/auth"
session = requests.Session()


def pretty_print(title, res):
    print(f"\n[{title}] — {res.status_code}")
    content_type = res.headers.get("Content-Type", "")
    if "application/json" in content_type:
        print(json.dumps(res.json(), indent=4))
    else:
        snippet = res.text.strip().replace("\n", " ")
        print(textwrap.shorten(snippet, width=300, placeholder=" ..."))


def set_auth(token):
    session.headers.update({"Authorization": f"Token {token}"})


def register_user():
    url = f"{BASE_URL}/registration/"
    data = {
        "username": "testuser",
        "email": "test@example.com",
        "password1": "strongpassword123",
        "password2": "strongpassword123"
    }
    res = session.post(url, json=data)
    pretty_print("REGISTER", res)
    if res.status_code == 201 and "key" in res.json():
        token = res.json()["key"]
        set_auth(token)
        return token
    return None


def login_user():
    url = f"{BASE_URL}/login/"
    data = {
        "email": "test@example.com",
        "password": "strongpassword123"
    }
    res = session.post(url, json=data)
    pretty_print("LOGIN", res)
    if res.status_code == 200 and "key" in res.json():
        token = res.json()["key"]
        set_auth(token)
        return token
    return None


def get_profile():
    res = session.get(f"{BASE_URL}/profile/")
    pretty_print("GET PROFILE", res)


def update_profile():
    data = {"bio": "Updated bio text", "location": "Pakistan"}
    res = session.patch(f"{BASE_URL}/profile/", json=data)
    pretty_print("UPDATE PROFILE", res)


def update_wallet():
    data = {"coins": 100, "type": "increment"}
    res = session.post(f"{BASE_URL}/wallet-update/", json=data)
    pretty_print("UPDATE WALLET", res)


def change_password():
    data = {
        "old_password": "strongpassword123",
        "new_password1": "newpassword123",
        "new_password2": "newpassword123"
    }
    res = session.post(f"{BASE_URL}/password/change/", json=data)
    pretty_print("PASSWORD CHANGE", res)


def deactivate_user():
    data = {"password": "newpassword123"}
    res = session.post(f"{BASE_URL}/deactivate/", json=data)
    pretty_print("DEACTIVATE USER", res)


def delete_user():
    data = {"password": "newpassword123"}
    res = session.post(f"{BASE_URL}/delete/", json=data)
    pretty_print("DELETE USER", res)


def logout_user():
    res = session.post(f"{BASE_URL}/logout/")
    pretty_print("LOGOUT", res)


def run_all_tests():
    print("\n--- AUTH API TEST FLOW ---")

    token = register_user()
    if not token:
        token = login_user()

    if not token:
        print("❌ Authentication failed — cannot continue tests.")
        return

    get_profile()
    update_profile()
    update_wallet()
    change_password()
    deactivate_user()
    logout_user()
    delete_user()


if __name__ == "__main__":
    run_all_tests()
