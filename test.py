import requests
import json
import textwrap

# BASE_URL = "http://127.0.0.1:8000/api/auth"
BASE_URL = "https://nonabstemiously-stocky-cynthia.ngrok-free.dev/api/auth"
session = requests.Session()


def pretty_print(title, res):
    print(f"\n[{title}] — {res.status_code}")
    try:
        print(json.dumps(res.json(), indent=4))
    except Exception:
        snippet = res.text.strip().replace("\n", " ")
        print(textwrap.shorten(snippet, width=300, placeholder=" ..."))


def set_auth(token):
    session.headers.update({"Authorization": f"Token {token}"})


def register_user(username, email, password):
    url = f"{BASE_URL}/registration/"
    data = {
        "username": username,
        "email": email,
        "password1": password,
        "password2": password
    }
    res = session.post(url, json=data)
    pretty_print("REGISTER", res)
    if res.status_code == 201 and "key" in res.json():
        token = res.json()["key"]
        set_auth(token)
        return token
    elif res.status_code == 400 and "username" in res.json():
        return login_user(email, password)
    return None


def login_user(email, password):
    url = f"{BASE_URL}/login/"
    data = {"email": email, "password": password}
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
    data = {"first_name": "John", "last_name": "Doe"}
    res = session.patch(f"{BASE_URL}/profile/", json=data)
    pretty_print("UPDATE PROFILE", res)


def update_wallet():
    data = {"coins": 100, "type": "increment"}
    res = session.post(f"{BASE_URL}/wallet-update/", json=data)
    pretty_print("UPDATE WALLET", res)


def change_password(old_pw, new_pw):
    data = {
        "old_password": old_pw,
        "new_password1": new_pw,
        "new_password2": new_pw
    }
    res = session.post(f"{BASE_URL}/password/change/", json=data)
    pretty_print("PASSWORD CHANGE", res)


def deactivate_user(password):
    data = {"password": password}
    res = session.post(f"{BASE_URL}/deactivate/", json=data)
    pretty_print("DEACTIVATE USER", res)


def delete_user(password):
    data = {"password": password}
    res = session.post(f"{BASE_URL}/delete/", json=data)
    pretty_print("DELETE USER", res)


def logout_user():
    res = session.post(f"{BASE_URL}/logout/")
    pretty_print("LOGOUT", res)


def run_flow():
    print("\n--- AUTH API TEST FLOW ---\n")

    username = "bong"
    email = "bong@example.com"
    password = "strongpassword123"
    new_pw = "newpassword123"

    token = register_user(username, email, password)
    if not token:
        print("❌ Could not authenticate — aborting tests.")
        return

    get_profile()
    update_profile()
    update_wallet()
    change_password(password, new_pw)

    print("\n[RE-LOGIN AFTER PASSWORD CHANGE]")
    session.headers.clear()
    new_token = login_user(email, new_pw)
    if new_token:
        get_profile()
        deactivate_user(new_pw)
        logout_user()
        delete_user(new_pw)


if __name__ == "__main__":
    run_flow()
