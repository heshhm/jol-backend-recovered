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
    """
    Logs in a user and returns the authentication token.
    """
    url = f"{BASE_URL}/auth/login/"
    data = {"email": email, "password": password}
    res = requests.post(url, json=data)
    pretty_print("LOGIN", res)
    if res.status_code == 200 and "key" in res.json():
        return res.json()["key"]
    raise Exception("Login failed")


def logout_user(token):
    """
    Logs out the authenticated user.
    """
    headers = {"Authorization": f"Token {token}"}
    res = requests.post(f"{BASE_URL}/auth/logout/", headers=headers)
    pretty_print("LOGOUT", res)


def get_user(token):
    """
    Retrieves user account info (username, email, first_name, last_name, wallet summary, profile summary)
    """
    headers = {"Authorization": f"Token {token}"}
    res = requests.get(f"{BASE_URL}/v1/user/", headers=headers)
    pretty_print("GET USER", res)


def update_user(token, first_name="John", last_name="Doe"):
    """
    Updates user account first_name and last_name only.
    """
    headers = {"Authorization": f"Token {token}"}
    data = {"first_name": first_name, "last_name": last_name}
    res = requests.patch(f"{BASE_URL}/v1/user/", json=data, headers=headers)
    pretty_print("UPDATE USER", res)


def get_profile(token):
    """
    Retrieves full profile info (bio, location, birth_date, avatar)
    """
    headers = {"Authorization": f"Token {token}"}
    res = requests.get(f"{BASE_URL}/v1/user/profile/", headers=headers)
    pretty_print("GET PROFILE", res)


def update_profile(token, bio=None, location=None, birth_date=None, avatar=None):
    """
    Updates profile fields selectively. Only editable fields: bio, location, birth_date, avatar.
    """
    headers = {"Authorization": f"Token {token}"}
    data = {}
    if bio is not None:
        data["bio"] = bio
    if location is not None:
        data["location"] = location
    if birth_date is not None:
        data["birth_date"] = birth_date
    if avatar is not None:
        data["avatar"] = avatar  # should be URL or file handling in real tests

    res = requests.patch(f"{BASE_URL}/v1/user/profile/", json=data, headers=headers)
    pretty_print("UPDATE PROFILE", res)


def get_wallet(token):
    """
    Retrieves wallet info (total_coins, used_coins, available_coins)
    """
    headers = {"Authorization": f"Token {token}"}
    res = requests.get(f"{BASE_URL}/v1/user/wallet/", headers=headers)
    pretty_print("GET WALLET", res)


def update_wallet(token, coins=100, type="increment"):
    """
    Increment or decrement coins in wallet using CoinSerializer.
    """
    headers = {"Authorization": f"Token {token}"}
    data = {"coins": coins, "type": type}
    res = requests.post(f"{BASE_URL}/v1/user/wallet/adjust/", json=data, headers=headers)
    pretty_print("UPDATE WALLET", res)


def process_referral(token, referral_code):
    """
    Submits a referral code and rewards referrer/referee accordingly.
    """
    headers = {"Authorization": f"Token {token}"}
    data = {"referral_code": referral_code}
    res = requests.post(f"{BASE_URL}/v1/user/process-referral/", json=data, headers=headers)
    pretty_print("PROCESS REFERRAL", res)


def change_password(token, old_pw, new_pw):
    """
    Changes password for authenticated user.
    """
    headers = {"Authorization": f"Token {token}"}
    data = {
        "old_password": old_pw,
        "new_password1": new_pw,
        "new_password2": new_pw
    }
    res = requests.post(f"{BASE_URL}/auth/password/change/", json=data, headers=headers)
    pretty_print("PASSWORD CHANGE", res)


def deactivate_user(token, password_input):
    """
    Deactivates the authenticated user's account.
    """
    headers = {"Authorization": f"Token {token}"}
    data = {"password": password_input}
    res = requests.post(f"{BASE_URL}/auth/deactivate/", json=data, headers=headers)
    pretty_print("DEACTIVATE USER", res)


def delete_user(token, password_input):
    """
    Permanently deletes the authenticated user's account.
    """
    headers = {"Authorization": f"Token {token}"}
    data = {"password": password_input}
    res = requests.post(f"{BASE_URL}/auth/delete/", json=data, headers=headers)
    pretty_print("DELETE USER", res)


def register_user(username, email, password):
    url = f"{BASE_URL}/auth/registration/"
    data = {
        "username": username,
        "email": email,
        "password1": password,
        "password2": password
    }
    res = requests.post(url, json=data)
    pretty_print("REGISTER", res)

