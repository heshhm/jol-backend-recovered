import requests
import json
import textwrap
import uuid
from datetime import datetime, timezone

BASE_URL = "http://127.0.0.1:8000/api"

def pretty_print(title, res):
    print(f"\n[{title}] — {res.status_code}")
    try:
        print(json.dumps(res.json(), indent=4))
    except Exception:
        snippet = res.text.strip().replace("\n", " ")
        print(textwrap.shorten(snippet, width=300, placeholder=" ..."))


def add_game(token, payload_override=None):
    """
    POST /api/v1/game/add-game/
    Saves a completed game. Payload must match the official spec exactly.
    """
    headers = {"Authorization": f"Token {token}"}

    # Default valid solo timed game
    default_payload = {
        "match_id": str(uuid.uuid4()),
        "player_id": "",  # will be filled from token later
        "game_type": "solo",
        "game_mode": "timed",
        "operation": "addition",
        "grid_size": 4,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "completed",
        "final_score": 92,
        "accuracy_percentage": 96.5,
        "hints_used": 1,
        "completion_time": 238,
        "room_code": None,
        "position": None,
        "total_players": None
    }

    payload = default_payload.copy()
    if payload_override:
        payload.update(payload_override)

    # Auto-fill player_id from token (you can override if testing spoofing)
    if not payload.get("player_id"):
        # Extract from token or pass manually in test
        # For real tests: we'll fill it in the test script after login
        payload["player_id"] = "PLACEHOLDER"

    res = requests.post(f"{BASE_URL}/v1/game/add-game/", json=payload, headers=headers)
    pretty_print("ADD GAME", res)
    return res


def list_games(token, page_size=20, page=1):
    """
    GET /api/v1/game/list/
    Returns paginated personal game history (newest first)
    """
    headers = {"Authorization": f"Token {token}"}
    params = {"page_size": page_size, "page": page}
    res = requests.get(f"{BASE_URL}/v1/game/list/", headers=headers, params=params)
    pretty_print("LIST GAMES", res)
    return res


def get_leaderboard(token, period="all_time", page_size=50, page=1):
    """
    GET /api/v1/game/leaderboard/
    ?period=today|this_week|this_month|all_time
    """
    headers = {"Authorization": f"Token {token}"}
    params = {
        "period": period,
        "page_size": page_size,
        "page": page
    }
    res = requests.get(f"{BASE_URL}/v1/game/leaderboard/", headers=headers, params=params)
    pretty_print(f"LEADERBOARD ({period.upper()})", res)
    return res


# ──────────────────────────────────────────────────────────────
# Helper payloads for common scenarios
# ──────────────────────────────────────────────────────────────
def solo_timed_payload(match_id=None, player_id=None):
    return {
        "match_id": match_id or str(uuid.uuid4()),
        "player_id": player_id or "PLACEHOLDER",
        "game_type": "solo",
        "game_mode": "timed",
        "operation": "addition",
        "grid_size": 4,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "completed",
        "final_score": 95,
        "accuracy_percentage": 98.0,
        "hints_used": 0,
        "completion_time": 115  # gold time!
    }


def solo_untimed_payload(match_id=None, player_id=None):
    payload = solo_timed_payload(match_id, player_id)
    payload.update({
        "game_mode": "untimed",
        "completion_time": None  # must be omitted
    })
    payload.pop("completion_time", None)
    return payload


def multiplayer_payload(match_id=None, player_id=None, position=1):
    return {
        "match_id": match_id or str(uuid.uuid4()),
        "player_id": player_id or "PLACEHOLDER",
        "game_type": "multiplayer",
        "game_mode": "timed",
        "operation": "subtraction",
        "grid_size": 5,
        "timestamp": datetime.now(timezone.utc).isoformat().replace("+00:00", "Z"),
        "status": "completed",
        "final_score": 88,
        "accuracy_percentage": 90.0,
        "hints_used": 2,
        "completion_time": 305,
        "room_code": "ABC123",
        "position": position,
        "total_players": 4
    }