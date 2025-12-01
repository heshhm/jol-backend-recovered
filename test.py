from test.user import *
from test.game import *
import requests


def call_error_test_api():
    url = "http://localhost:8000/api/v1/user/error/test/"
    headers = {
        "Authorization": f"Token {login_user('admin@admin.com', 'admin')}"
    }
    response = requests.get(url, headers=headers)
    return response


def main():
    # Login as the admin user
    token = login_user("admin@admin.com", "admin")

    # Discover admin user's pk so we can set player_id correctly in payloads
    headers = {"Authorization": f"Token {token}"}
    res = requests.get(f"{BASE_URL}/v1/user/detail/", headers=headers)
    try:
        user_pk = str(res.json().get("pk"))
    except Exception:
        user_pk = None

    # ADD A TEST FOR THE PROCESS-REFERRAL ENDPOINT
    if user_pk:
        url = f"{BASE_URL}/v1/user/process-referral/"
        payload = {
        }
        response = requests.post(url, json=payload, headers=headers)
        print("Process Referral API Response:", response.status_code, response.json())


if __name__ == "__main__":
    main()