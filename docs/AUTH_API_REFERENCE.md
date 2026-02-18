# JOL Backend — Auth & User API Reference

> **Base URL:** `https://<your-domain>/api/`
> **Auth:** All endpoints (except registration, login, password reset) require `Authorization: Token <key>` header.
> **Swagger:** Live docs available at `/api/` (Swagger UI) and `/api/docs/` (ReDoc)

---

## 1. Registration (Sign Up)

```
POST /api/auth/registration/
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `username` | string | ✅ | Unique |
| `email` | string | ✅ | Unique, used for verification |
| `password1` | string | ✅ | Must pass Django validators |
| `password2` | string | ✅ | Must match `password1` |

**Response** `201 Created`:
```json
{
  "detail": "Verification e-mail sent."
}
```

> **⚠️ Email verification is MANDATORY.** The user cannot log in until they click the verification link sent to their email. Attempting to login before verification returns `403` with `"E-mail is not verified."`.

---

## 2. Email Verification

After registration, the user receives an email with a verification link. The link contains a **key**.

```
POST /api/auth/registration/verify-email/
```

| Field | Type | Required |
|---|---|---|
| `key` | string | ✅ |

**Response** `200 OK`:
```json
{
  "detail": "ok"
}
```

> **Mobile Integration:** Intercept the email link using a deep link / universal link scheme. Extract the `key` parameter and POST it to this endpoint.

---

## 3. Login

```
POST /api/auth/login/
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `username` | string | ✅* | Can use username OR email |
| `email` | string | ✅* | Can use username OR email |
| `password` | string | ✅ | |

*One of `username` or `email` is required.*

**Response** `200 OK`:
```json
{
  "key": "abc123tokenhere..."
}
```

> **Important Behavior:**
> - A **new token** is generated on every login. Any previous token is **invalidated**.
> - This enforces **single-device sessions** — logging in on a second device logs out the first.
> - Store the `key` securely and include it as `Authorization: Token <key>` in all subsequent requests.

---

## 4. Logout

```
POST /api/auth/logout/
```

🔒 Requires auth token.

**Response** `200 OK`:
```json
{
  "detail": "Successfully logged out."
}
```

---

## 5. Password Change (Logged-In User)

```
POST /api/auth/password/change/
```

🔒 Requires auth token.

| Field | Type | Required |
|---|---|---|
| `old_password` | string | ✅ |
| `new_password1` | string | ✅ |
| `new_password2` | string | ✅ |

**Response** `200 OK`:
```json
{
  "detail": "New password has been saved."
}
```

---

## 6. Password Reset (Forgot Password)

This is a **two-step** flow:

### Step 1: Request Reset Email

```
POST /api/auth/password/reset/
```

| Field | Type | Required |
|---|---|---|
| `email` | string | ✅ |

**Response** `200 OK`:
```json
{
  "detail": "Password reset e-mail has been sent."
}
```

The user receives an email with a link containing `uid` and `token`.

### Step 2: Confirm New Password

```
POST /api/auth/password/reset/confirm/<uid>/<token>/
```

| Field | Type | Required |
|---|---|---|
| `new_password1` | string | ✅ |
| `new_password2` | string | ✅ |
| `uid` | string | ✅ |
| `token` | string | ✅ |

**Response** `200 OK`:
```json
{
  "detail": "Password has been reset with the new password."
}
```

> **Mobile Integration:** Use a deep link to intercept the reset email link. Extract `uid` and `token` from the URL path, then POST them along with the new password.

---

## 7. Google Social Login

```
POST /api/auth/google/
```

| Field | Type | Required | Notes |
|---|---|---|---|
| `access_token` | string | ✅* | OAuth2 access token from Google |
| `code` | string | ✅* | OAuth2 auth code (alternative) |

*Send either `access_token` or `code`.*

**Response** `200 OK`:
```json
{
  "key": "abc123tokenhere..."
}
```

### Connect Google to Existing Account

```
POST /api/auth/google-connect/
```

🔒 Requires auth token. Same body as above. Links a Google account to the currently logged-in user.

---

## 8. Account Deactivation

```
POST /api/auth/deactivate/
```

🔒 Requires auth token.

| Field | Type | Required |
|---|---|---|
| `password` | string | ✅ |

**Response** `200 OK`:
```json
{
  "message": "User account has been deactivated"
}
```

> The account is soft-deleted (`is_active = False`). The user cannot log in after this.

---

## 9. User Profile & Wallet (Quick Reference)

All require `Authorization: Token <key>`.

| Method | Endpoint | Description |
|---|---|---|
| `GET/PUT` | `/api/v1/user/detail/` | Get/update user info (username, name) |
| `GET/PUT` | `/api/v1/user/profile/` | Get/update profile (bio, location, avatar) |
| `GET` | `/api/v1/user/wallet/` | Get wallet balance |
| `POST` | `/api/v1/user/wallet/adjust/` | Adjust coins (admin use) |
| `POST` | `/api/v1/user/wallet/redeem/` | Redeem game points → coins |
| `POST` | `/api/v1/user/process-referral/` | Process referral reward at signup |

---

## 10. Game Endpoints (Quick Reference)

All require `Authorization: Token <key>`.

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/v1/game/add-game/` | Submit completed game result |
| `GET` | `/api/v1/game/list/` | User's game history (paginated) |
| `GET` | `/api/v1/game/leaderboard/` | Leaderboard (`?period=today\|this_week\|this_month\|all_time`) |

---

## Error Responses

All endpoints return errors in this format:

```json
{
  "field_name": ["Error message here."]
}
```

Or for non-field errors:

```json
{
  "non_field_errors": ["Unable to log in with provided credentials."],
  "detail": "Error description."
}
```

| Status Code | Meaning |
|---|---|
| `400` | Bad request / validation error |
| `401` | Missing or invalid auth token |
| `403` | Email not verified / permission denied |
| `404` | Resource not found |
| `500` | Server error |
