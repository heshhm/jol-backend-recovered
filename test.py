# test_game_full_leaderboard.py
from test.user import *
from test.game import *

def call_error_test_api():
    import requests

    url = "http://localhost:8000/api/v1/user/error/test/"
    headers = {
        "Authorization": f"Token {login_user('admin@admin.com', 'admin')}"
    }
    response = requests.get(url, headers=headers)
    return response



def main():
    call_error_test_api()


if __name__ == "__main__":
    main()