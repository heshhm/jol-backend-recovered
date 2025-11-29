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

    # Create a few sample games for the admin user
    # 1) Solo timed (high accuracy)
    payload1 = solo_timed_payload(player_id=user_pk)
    add_game(token, payload_override=payload1)

    # 2) Solo untimed
    payload2 = solo_untimed_payload(player_id=user_pk)
    add_game(token, payload_override=payload2)

    # 3) Multiplayer - 1st place
    payload3 = multiplayer_payload(player_id=user_pk, position=1)
    add_game(token, payload_override=payload3)

    # 4) Multiplayer - lower place
    payload4 = multiplayer_payload(player_id=user_pk, position=3)
    add_game(token, payload_override=payload4)

    # List games to verify
    list_games(token)


if __name__ == "__main__":
    main()