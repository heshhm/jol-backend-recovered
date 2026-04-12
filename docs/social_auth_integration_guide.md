# JOL Puzzles — Social Authentication Integration Guide

**Prepared For:** Mobile Application Developer  
**Prepared By:** Backend Team  
**Date:** April 12, 2026  
**Backend Stack:** Django 5.2 + Django REST Framework + django-allauth + dj-rest-auth

---

## Table of Contents

1. [Overview](#overview)
2. [Base URL](#base-url)
3. [Authentication Model](#authentication-model)
4. [Apple Sign In](#apple-sign-in)
5. [Google Sign In](#google-sign-in)
6. [All Auth Endpoints](#all-auth-endpoints)
7. [User Lifecycle](#user-lifecycle)
8. [Error Handling](#error-handling)
9. [Testing Checklist](#testing-checklist)

---

## Overview

The backend supports three authentication methods:

| Method | Status | Endpoint |
|--------|--------|----------|
| Email/Password | ✅ Active | `POST /api/auth/login/` |
| Google Sign In | ✅ Active | `POST /api/auth/google/` |
| **Apple Sign In** | ✅ **NEW** | `POST /api/auth/apple/` |

All social auth endpoints follow the same pattern: the mobile app obtains a token from the identity provider (Apple/Google) and sends it to the backend. The backend verifies the token, creates or logs in the user, and returns an auth token.

---

## Base URL

```
Production: https://jolpuzzles.com
```

All endpoints below are relative to this base URL.

---

## Authentication Model

The backend uses **Token Authentication**. After a successful login (any method), the server returns a `key` field — this is the auth token.

**Include this token in all subsequent API requests:**

```
Authorization: Token <your_token_here>
```

---

## Apple Sign In

### Endpoint

```
POST /api/auth/apple/
```

**Authentication:** None required (this is a login endpoint)  
**Content-Type:** `application/json`

### How It Works

```
┌──────────┐     ①  Tap "Sign in with Apple"     ┌──────────┐
│  Mobile   │ ──────────────────────────────────► │  Apple   │
│   App     │ ◄────────────────────────────────── │  Server  │
└──────────┘  ②  identity_token + auth_code       └──────────┘
      │
      │  ③  POST /api/auth/apple/
      │     { "access_token": "<identity_token>" }
      ▼
┌──────────┐
│  Backend │ ──► Verifies token with Apple's public keys
│  Server  │ ──► Creates or finds user
│          │ ──► Returns auth token
└──────────┘
      │
      │  ④  { "key": "abc123..." }
      ▼
┌──────────┐
│  Mobile   │  Now authenticated!
│   App     │
└──────────┘
```

### Request Body

The backend expects the Apple identity token in the `access_token` field. This is how `dj-rest-auth` / `django-allauth` handles social token exchange.

```json
{
  "access_token": "<APPLE_IDENTITY_TOKEN>",
  "code": "<AUTHORIZATION_CODE>"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_token` | string | ✅ Yes | The Apple identity token (JWT) received from `ASAuthorizationAppleIDCredential.identityToken` |
| `code` | string | ⚠️ Optional | The authorization code from `ASAuthorizationAppleIDCredential.authorizationCode`. Include if available. |

> **⚠️ Important**: The field name must be `access_token`, NOT `identity_token`. This is the field name that the backend framework (dj-rest-auth) expects.

### Successful Response (200 OK)

```json
{
  "key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
}
```

The `key` is the authentication token. Store it securely and include it in the `Authorization` header for all authenticated requests.

### First-Time User — Name Handling

Apple only provides the user's name on the **very first** Sign In with Apple authorization. The backend will use whatever name information is available from the Apple token claims.

**If you want to ensure the user's name is saved**, you can optionally make a profile update call after the first login:

```
PATCH /api/v1/user/profile/update/
Authorization: Token <key>

{
  "first_name": "John",
  "last_name": "Doe"
}
```

### Example — cURL

```bash
curl -X POST https://jolpuzzles.com/api/auth/apple/ \
  -H "Content-Type: application/json" \
  -d '{
    "access_token": "eyJraWQiOiJXNldjT0...<full Apple identity token>",
    "code": "c1234567890abcdef..."
  }'
```

### Example — Swift (iOS)

```swift
func handleAppleSignIn(credential: ASAuthorizationAppleIDCredential) {
    guard let identityTokenData = credential.identityToken,
          let identityToken = String(data: identityTokenData, encoding: .utf8) else {
        return
    }
    
    let authorizationCode = credential.authorizationCode
        .flatMap { String(data: $0, encoding: .utf8) }
    
    var body: [String: Any] = [
        "access_token": identityToken
    ]
    
    if let code = authorizationCode {
        body["code"] = code
    }
    
    // POST to /api/auth/apple/ with this body
    // On success, store response["key"] as the auth token
}
```

---

## Google Sign In

### Endpoint

```
POST /api/auth/google/
```

**Authentication:** None required (this is a login endpoint)  
**Content-Type:** `application/json`

### Request Body

```json
{
  "access_token": "<GOOGLE_ACCESS_TOKEN>"
}
```

Alternatively, if using an ID token from Google Sign-In SDK:

```json
{
  "id_token": "<GOOGLE_ID_TOKEN>"
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `access_token` | string | ✅ (one of) | Google OAuth2 access token |
| `id_token` | string | ✅ (one of) | Google ID token (from mobile SDK) |

> **Note**: Send **either** `access_token` or `id_token` — whichever your Google Sign-In SDK provides.

### Successful Response (200 OK)

```json
{
  "key": "a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0"
}
```

---

## All Auth Endpoints

### Authentication (No token required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/login/` | Email/username + password login |
| `POST` | `/api/auth/google/` | Google social login |
| `POST` | `/api/auth/apple/` | Apple social login |
| `POST` | `/api/auth/registration/` | New user registration |
| `POST` | `/api/auth/password/reset/` | Request password reset email |

### Authenticated (Token required)

| Method | Endpoint | Description |
|--------|----------|-------------|
| `POST` | `/api/auth/logout/` | Logout (invalidates token) |
| `POST` | `/api/auth/password/change/` | Change password |
| `POST` | `/api/auth/deactivate/` | Deactivate account |
| `POST` | `/api/auth/google-connect/` | Connect Google to existing account |
| `POST` | `/api/auth/apple-connect/` | Connect Apple to existing account |

### Social Connect (Linking accounts)

The `-connect` endpoints allow an already-authenticated user to **link** a social account to their existing JOL account. This is useful when a user signed up with email/password and later wants to also be able to sign in with Apple or Google.

```bash
# Link Apple account to existing user
curl -X POST https://jolpuzzles.com/api/auth/apple-connect/ \
  -H "Authorization: Token <existing_auth_token>" \
  -H "Content-Type: application/json" \
  -d '{"access_token": "<APPLE_IDENTITY_TOKEN>"}'
```

---

## User Lifecycle

When a user signs in with Apple or Google for the **first time**, the backend automatically:

1. ✅ Creates a new `User` account
2. ✅ Creates a `UserProfile` (with referral code)
3. ✅ Creates a `UserWallet` (with 0 coins)
4. ✅ Links the social account (Apple/Google)
5. ✅ Returns an auth token

On **subsequent logins**, the backend:

1. ✅ Finds the existing user by social account
2. ✅ Returns an auth token

### Email Handling

- **Apple**: May provide a real email or a Private Relay email (e.g., `abc123@privaterelay.appleid.com`). Both are stored and work correctly.
- **Google**: Always provides the user's real Gmail address.
- **Duplicate emails**: If a social login email matches an existing account's email, the accounts may be automatically linked (depending on allauth settings).

---

## Error Handling

### Common Error Responses

**400 Bad Request — Invalid or missing token:**
```json
{
  "non_field_errors": [
    "Incorrect value"
  ]
}
```

**400 Bad Request — Token expired:**
```json
{
  "non_field_errors": [
    "Token is expired"
  ]
}
```

**400 Bad Request — Account already exists with different provider:**
```json
{
  "non_field_errors": [
    "An account already exists with this e-mail address. Please sign in to that account first, then connect your Apple account."
  ]
}
```

### Handling Tips for Mobile

| Scenario | Recommended Action |
|----------|-------------------|
| `200 OK` with `key` | Store token, navigate to home screen |
| `400` with token errors | Show "Sign in failed, please try again" |
| `400` with duplicate email | Prompt user to sign in with their existing method first |
| `500` Server error | Show generic error, retry after delay |
| Network timeout | Retry with exponential backoff |

---

## Testing Checklist

| Test Case | Apple | Google |
|-----------|-------|--------|
| First-time login creates new user | ⬜ | ⬜ |
| Subsequent login returns existing user | ⬜ | ⬜ |
| Auth token returned and works for API calls | ⬜ | ⬜ |
| Private relay email handled (Apple only) | ⬜ | — |
| Account linking via `-connect` endpoint | ⬜ | ⬜ |
| Invalid/expired token returns 400 | ⬜ | ⬜ |
| User profile and wallet created on first login | ⬜ | ⬜ |

---

## Contact

For backend questions or issues, contact the backend team. For Apple Developer Portal or Google Cloud Console configuration, coordinate with the team lead.
