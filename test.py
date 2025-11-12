from test.user import *
from test.game import *

# Test users
USER1 = {"username": "user1", "email": "user1@test.com", "password": "Pass1234Pass1234!"}
USER2 = {"username": "user2", "email": "user2@test.com", "password": "Pass1234Pass1234!"}



def main():

    # register_user(USER1["username"], USER1["email"], USER1["password"])
    # register_user(USER2["username"], USER2["email"], USER2["password"])

    token = login_user(USER1["email"], USER1["password"])

    user_res = requests.get(f"{BASE_URL}/v1/user/detail/", headers={"Authorization": f"Token {token}"})
    player_id = user_res.json()["pk"]  # or "sub" if Auth0
    print(f"\nPlayer ID: {player_id}")

    # 3. Add several games
    add_game(token, {**solo_timed_payload(player_id=player_id), "final_score": 99})
    add_game(token, {**solo_untimed_payload(player_id=player_id), "accuracy_percentage": 100.0})
    add_game(token, {**multiplayer_payload(player_id=player_id, position=1), "hints_used": 0})

    # 4. List personal history
    list_games(token, page_size=10)

    # 5. Leaderboards
    get_leaderboard(token, period="today")
    get_leaderboard(token, period="this_week")
    get_leaderboard(token, period="all_time", page_size=5)


if __name__ == "__main__":
    main()
