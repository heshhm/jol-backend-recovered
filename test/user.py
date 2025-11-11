import requests
import json
import textwrap

BASE_URL = "http://127.0.0.1:8000/api"


def pretty_print(title, res):
    print(f"\n[{title}] — {res.status_code}")
    try:
        print(json.dumps(res.json(), indent=4))
    except Exception:
        snippet = res.text.strip().replace("\n", " ")
        print(textwrap.shorten(snippet, width=300, placeholder=" ..."))


def login_user(email, password):
    url = f"{BASE_URL}/auth/login/"
    data = {"email": email, "password": password}
    res = requests.post(url, json=data)
    pretty_print("LOGIN", res)
    if res.status_code == 200 and "key" in res.json():
        return res.json()["key"]
    raise Exception("Login failed")



def get_profile(token):
    headers = {"Authorization": f"Token {token}"}
    res = requests.get(f"{BASE_URL}/v1/user/profile/", headers=headers)
    pretty_print("GET PROFILE", res)


def update_profile(token, first_name="John", last_name="Doe", location="Nowhere"):
    headers = {"Authorization": f"Token {token}"}
    data = {"first_name": first_name, "last_name": last_name, "profile": {"location": location}}
    res = requests.patch(f"{BASE_URL}/v1/user/profile/", json=data, headers=headers)
    pretty_print("UPDATE PROFILE", res)


def update_wallet(token, coins=100, type="increment"):
    headers = {"Authorization": f"Token {token}"}
    data = {"coins": coins, "type": type}
    res = requests.post(f"{BASE_URL}/v1/user/wallet-update/", json=data, headers=headers)
    pretty_print("UPDATE WALLET", res)


def change_password(token, old_pw, new_pw):
    headers = {"Authorization": f"Token {token}"}
    data = {
        "old_password": old_pw,
        "new_password1": new_pw,
        "new_password2": new_pw
    }
    res = requests.post(f"{BASE_URL}/auth/password/change/", json=data, headers=headers)
    pretty_print("PASSWORD CHANGE", res)


def deactivate_user(token, password_input):
    headers = {"Authorization": f"Token {token}"}
    data = {"password": password_input}
    res = requests.post(f"{BASE_URL}/auth/deactivate/", json=data, headers=headers)
    pretty_print("DEACTIVATE USER", res)


def delete_user(token, password_input):
    headers = {"Authorization": f"Token {token}"}
    data = {"password": password_input}
    res = requests.post(f"{BASE_URL}/auth/delete/", json=data, headers=headers)
    pretty_print("DELETE USER", res)


def logout_user(token):
    headers = {"Authorization": f"Token {token}"}
    res = requests.post(f"{BASE_URL}/auth/logout/", headers=headers)
    pretty_print("LOGOUT", res)
