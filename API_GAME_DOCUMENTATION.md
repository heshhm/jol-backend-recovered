# Game API Documentation

## Overview
The Game API handles game history recording, scoring, and leaderboard management. The system separates **client-provided data** from **server-calculated points** to maintain integrity.

---

## Core Endpoint: Add Game

### Endpoint
```
POST /api/v1/game/add-game/
```

### Authentication
- **Required**: Token authentication (`Authorization: Token <token>`)
- **User**: Authenticated user (automatically set as `player`)

---

## Request Payload

### Required Fields (Client Provides)

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `match_id` | string (UUID) | ✅ | Unique identifier for this game (36 chars, e.g., `"550e8400-e29b-41d4-a716-446655440000"`) - Must be unique across all games |
| `player_id` | string | ✅ | Must match authenticated user's ID. Used for validation only. |
| `game_type` | enum | ✅ | `"solo"` or `"multiplayer"` |
| `game_mode` | enum | ✅ | `"timed"` or `"untimed"` |
| `operation` | enum | ✅ | `"addition"` or `"subtraction"` (math operation type) |
| `grid_size` | integer | ✅ | Grid dimension (e.g., `4` for 4×4 grid) |
| `timestamp` | ISO 8601 datetime | ✅ | When game was completed (e.g., `"2025-12-05T14:30:00Z"`) |
| `status` | enum | ✅ | `"completed"`, `"abandoned"`, or `"timed_out"` |
| `final_score` | integer (0-100) | ✅ | Player's raw score percentage |
| `accuracy_percentage` | float (0-100) | ✅ | `correct_cells / total_player_cells * 100` |
| `hints_used` | integer | ✅ | Number of hints the player used |

### Conditional Fields (Required Based on Game Type/Mode)

| Field | Type | When Required | Description |
|-------|------|---------------|-------------|
| `completion_time` | integer | ✅ If `game_mode == "timed"` | Seconds taken to complete the game |
| `room_code` | string (6 chars) | ✅ If `game_type == "multiplayer"` | Unique room identifier |
| `position` | integer | ✅ If `game_type == "multiplayer"` | Player's final ranking (1st, 2nd, etc.) |
| `total_players` | integer | ✅ If `game_type == "multiplayer"` | Number of players in the room |

---

## Example Payloads

### Solo Timed Game
```json
{
  "match_id": "550e8400-e29b-41d4-a716-446655440001",
  "player_id": "42",
  "game_type": "solo",
  "game_mode": "timed",
  "operation": "addition",
  "grid_size": 4,
  "timestamp": "2025-12-05T14:30:00Z",
  "status": "completed",
  "final_score": 85,
  "accuracy_percentage": 92.5,
  "hints_used": 1,
  "completion_time": 120
}
```

### Solo Untimed Game
```json
{
  "match_id": "550e8400-e29b-41d4-a716-446655440002",
  "player_id": "42",
  "game_type": "solo",
  "game_mode": "untimed",
  "operation": "subtraction",
  "grid_size": 5,
  "timestamp": "2025-12-05T15:45:00Z",
  "status": "completed",
  "final_score": 78,
  "accuracy_percentage": 88.0,
  "hints_used": 3
}
```

### Multiplayer Game
```json
{
  "match_id": "550e8400-e29b-41d4-a716-446655440003",
  "player_id": "42",
  "game_type": "multiplayer",
  "game_mode": "timed",
  "operation": "addition",
  "grid_size": 4,
  "timestamp": "2025-12-05T16:20:00Z",
  "status": "completed",
  "final_score": 90,
  "accuracy_percentage": 95.0,
  "hints_used": 0,
  "completion_time": 95,
  "room_code": "ABC123",
  "position": 1,
  "total_players": 4
}
```

---

## Response Format

### Success Response (201 Created)
```json
{
  "match_id": "550e8400-e29b-41d4-a716-446655440001",
  "game_type": "solo",
  "game_mode": "timed",
  "operation": "addition",
  "grid_size": 4,
  "timestamp": "2025-12-05T14:30:00Z",
  "status": "completed",
  "final_score": 85,
  "accuracy_percentage": 92.5,
  "hints_used": 1,
  "completion_time": 120,
  "room_code": null,
  "position": null,
  "total_players": null,
  "points_earned": 145
}
```

### Error Response (400 Bad Request)
```json
{
  "field_name": ["Error message describing the validation failure"]
}
```

#### Common Validation Errors:
- `"player_id does not match authenticated user."` - player_id must match token's user
- `"completion_time": ["Required for timed mode."]` - Missing for timed games
- `"room_code": ["Required for multiplayer games."]` - Missing for multiplayer
- `"match_id": ["This field must be unique."]` - match_id already exists
- `"accuracy_percentage": ["Ensure this value is less than or equal to 100."]` - Invalid accuracy

---

## Points Calculation System

### Server-Side Calculation (Automatic)

The `points_earned` field is **calculated automatically by the server** on game creation. The client **does NOT** provide this value.

#### Scoring Algorithm

**Base Score: 100 points** (only if status is "completed")

If status is anything other than "completed" (e.g., "abandoned", "timed_out"), the game earns **0 points**.

#### 1. Accuracy Bonus (Max +40)
Applied based on `accuracy_percentage`:

| Accuracy | Points |
|----------|--------|
| ≥ 95% | +40 |
| ≥ 85% | +35 |
| ≥ 75% | +30 |
| ≥ 65% | +25 |
| ≥ 50% | +20 |
| ≥ 25% | +10 |
| < 25% | 0 |

**Example**: If accuracy is 92%, add +35 points

#### 2. Hints Penalty (Max -20)
Deducted based on `hints_used`:

| Hints | Penalty |
|-------|---------|
| ≥ 5 | -20 |
| ≥ 3 | -15 |
| = 2 | -10 |
| = 1 | -5 |
| = 0 | 0 |

**Example**: If 2 hints used, subtract -10 points

#### 3. Time Bonus (Max +30, Timed Mode Only)
Applied only if `game_mode == "timed"`. Based on `completion_time` and `grid_size`:

**Time Thresholds** (in seconds):
- Gold: `grid_size * 30` (e.g., 4×4 = 120s)
- Silver: `grid_size * 45` (e.g., 4×4 = 180s)
- Bronze: `grid_size * 60` (e.g., 4×4 = 240s)

| Speed | Points |
|-------|--------|
| ≤ Gold | +30 |
| ≤ Silver | +15 |
| ≤ Bronze | +5 |
| > Bronze | 0 |

**Example**: 4×4 grid (120s gold), completed in 100s → +30 points

#### 4. Multiplayer Position Bonus (Max +30, Multiplayer Only)
Applied only if `game_type == "multiplayer"` based on `position`:

| Position | Points |
|----------|--------|
| 1st (Winner) | +30 |
| 2nd | +20 |
| 3rd | +10 |
| 4th+ | 0 |

**Example**: Won 1st place → +30 points

#### 5. Minimum Floor
The final score is **never below 10 points** (even with heavy penalties):
```
final_points = max(10, calculated_points)
```

---

## Calculation Example

**Scenario**: Solo timed game, completed

**Input**:
- Base: 100
- Accuracy: 92% → +35
- Hints used: 1 → -5
- Completion time: 100s, grid 4×4 (gold ≤ 120s) → +30
- Game type: solo (no position bonus)

**Calculation**:
```
100 + 35 - 5 + 30 = 160 points
```

**Response**:
```json
{
  "points_earned": 160
}
```

---

## Data Storage

### Database Fields in GameHistory

| Field | Type | Stored | Purpose |
|-------|------|--------|---------|
| `match_id` | CharField(36) | ✅ Client | Unique game identifier |
| `player_id` | ForeignKey | ✅ Server | Links to User (set from auth token) |
| `game_type` | CharField | ✅ Client | Game classification |
| `game_mode` | CharField | ✅ Client | Game mode type |
| `operation` | CharField | ✅ Client | Math operation |
| `grid_size` | PositiveSmallInt | ✅ Client | Grid dimension |
| `timestamp` | DateTime | ✅ Client | Completion time |
| `status` | CharField | ✅ Client | Final game status |
| `final_score` | PositiveSmallInt | ✅ Client | Raw score percentage |
| `accuracy_percentage` | Float | ✅ Client | Accuracy %, used in calculation |
| `hints_used` | PositiveSmallInt | ✅ Client | Hints count, used in calculation |
| `points_earned` | PositiveInt | 🔄 Server | **Calculated & stored** on save |
| `completion_time` | PositiveInt | ✅ Client | Only for timed games |
| `room_code` | CharField(6) | ✅ Client | Only for multiplayer |
| `position` | PositiveSmallInt | ✅ Client | Only for multiplayer |
| `total_players` | PositiveSmallInt | ✅ Client | Only for multiplayer |

**Legend**:
- ✅ = Client provides, server stores
- 🔄 = Server calculates, then stores

---

## Related Endpoints

### Get Personal Game History
```
GET /api/v1/game/list/
```
**Parameters**:
- `page_size` (default: 20, max: 100)
- `page` (default: 1)

**Response**: Paginated list of user's games with `points_earned`

### Get Leaderboard
```
GET /api/v1/game/leaderboard/
```
**Parameters**:
- `period`: `"today"`, `"this_week"`, `"this_month"`, `"all_time"` (default: `"all_time"`)
- `page_size` (default: 50, max: 100)
- `page` (default: 1)

**Response**: User rankings with `total_points` (sum of `points_earned`) and `games_played`

---

## Validation Rules

### Player ID Validation
- `player_id` must exactly match the authenticated user's ID
- Server automatically uses `request.user` regardless of player_id input

### Match ID Validation
- Must be unique across all games (no duplicates allowed)
- Recommended format: UUID v4 (36 characters)

### Timed Mode Validation
- **Required**: `completion_time` must be provided
- Must be a positive integer (in seconds)

### Multiplayer Mode Validation
- **Required**: `room_code`, `position`, `total_players`
- `position` must be 1 or greater
- `total_players` must be > 1

### Status Validation
- Only `"completed"` games earn points
- `"abandoned"` and `"timed_out"` games store as 0 points

### Accuracy & Score Validation
- `accuracy_percentage`: 0-100 (float)
- `final_score`: 0-100 (integer)

---

## Notes

1. **Points are calculated server-side** – Never trust client-provided points
2. **Match IDs must be unique** – Client should generate UUIDs to avoid collisions
3. **Timestamp is client-provided** – Server trusts client's device time for now (future: add server-side drift detection)
4. **Status determines if points count** – Only "completed" games contribute to leaderboards
5. **Points are recalculated on save** – Stored in `points_earned` column for fast leaderboard queries

---

## Database Indexes

For performance optimization:
- `(player, -timestamp)` – Fast personal game history queries
- `(-timestamp)` – Fast global leaderboard queries
- `(room_code, -timestamp)` – Fast room-specific results
- `(match_id)` – Unique constraint ensures no duplicate submissions
- `(points_earned)` – Fast leaderboard sorting

---

## Future Enhancements

- [ ] Server-side timestamp validation (detect & flag client drift)
- [ ] Anti-cheat scoring (flag impossible accuracy/speed combinations)
- [ ] Seasonal leaderboards with reset
- [ ] Achievement/badge system based on points
- [ ] Multiplayer room validation (verify room_code exists before accept)
