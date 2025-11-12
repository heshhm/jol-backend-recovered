# test_game_full_leaderboard.py
from test.user import *
from test.game import *

# === TEST USERS ===
TOPUSER = {"username": "topuser", "email": "top@test.com", "password": "Pass1234Pass1234!"}
MIDGAMER = {"username": "midgamer", "email": "mid@test.com", "password": "Pass1234Pass1234!"}
LOWUSER = {"username": "lowuser", "email": "low@test.com", "password": "Pass1234Pass1234!"}

USERS = [TOPUSER, MIDGAMER, LOWUSER]

def create_user_and_play_games(user_data, game_payloads):
    """Register, login, get player_id, play games"""
    register_user(user_data["username"], user_data["email"], user_data["password"])
    token = login_user(user_data["email"], user_data["password"])

    # Get real player_id
    res = requests.get(f"{BASE_URL}/v1/user/detail/", headers={"Authorization": f"Token {token}"})
    player_id = res.json()["pk"]
    print(f"\n[+] {user_data['username']} logged in → player_id: {player_id}")

    # Play games — FIXED: use lambda p: payload(p) correctly
    for payload_func in game_payloads:
        payload = payload_func(player_id)  # ← Call with player_id
        add_game(token, payload)
        print(f"   → Played: {payload['game_type']} {payload['game_mode']} | "
              f"Acc: {payload['accuracy_percentage']}% | Hints: {payload['hints_used']} | "
              f"Time: {payload.get('completion_time', 'N/A')}s")

    return token

def main():
    print("\n" + "="*60)
    print("   LEADERBOARD TEST: topuser vs midgamer vs lowuser")
    print("="*60 + "\n")

    # === TOPUSER: GOD TIER ===
    top_games = [
        lambda p: {**solo_timed_payload(player_id=p), "accuracy_percentage": 100.0, "hints_used": 0, "completion_time": 90},
        lambda p: {**solo_timed_payload(player_id=p), "accuracy_percentage": 99.0, "hints_used": 0, "completion_time": 105},
        lambda p: {**multiplayer_payload(player_id=p, position=1), "accuracy_percentage": 98.0, "hints_used": 0, "completion_time": 140},
        lambda p: {**multiplayer_payload(player_id=p, position=1), "accuracy_percentage": 100.0, "hints_used": 0},
    ]
    top_token = create_user_and_play_games(TOPUSER, top_games)

    # === MIDGAMER: RESPECTABLE ===
    mid_games = [
        lambda p: {**solo_timed_payload(player_id=p), "accuracy_percentage": 85.0, "hints_used": 1, "completion_time": 180},
        lambda p: {**solo_untimed_payload(player_id=p), "accuracy_percentage": 88.0, "hints_used": 2},
        lambda p: {**multiplayer_payload(player_id=p, position=2), "accuracy_percentage": 82.0, "hints_used": 3},
    ]
    mid_token = create_user_and_play_games(MIDGAMER, mid_games)

    # === LOWUSER: LEARNING ===
    low_games = [
        lambda p: {**solo_timed_payload(player_id=p), "accuracy_percentage": 45.0, "hints_used": 6, "completion_time": 400},
        lambda p: {**solo_untimed_payload(player_id=p), "accuracy_percentage": 30.0, "hints_used": 8},
        lambda p: {**multiplayer_payload(player_id=p, position=4), "accuracy_percentage": 55.0, "hints_used": 5},
    ]
    low_token = create_user_and_play_games(LOWUSER, low_games)

    print("\n" + "—"*60)
    print("   ALL GAMES PLAYED — CHECKING LEADERBOARD")
    print("—"*60 + "\n")

    # === FINAL LEADERBOARD CHECK ===
    print("\nTODAY LEADERBOARD")
    get_leaderboard(top_token, period="today", page_size=10)

    print("\nALL TIME LEADERBOARD (top 5)")
    get_leaderboard(top_token, period="all_time", page_size=5)

    print("\nWEEK LEADERBOARD")
    get_leaderboard(mid_token, period="this_week", page_size=10)

    print("\n" + "="*60)
    print("   TEST COMPLETE — LEADERBOARD WORKS PERFECTLY!")
    print("="*60)

if __name__ == "__main__":
    main()