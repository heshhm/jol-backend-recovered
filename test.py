from test.user import *

# Test users
USER1 = {"username": "user1", "email": "user1@test.com", "password": "Pass1234Pass1234!"}
USER2 = {"username": "user2", "email": "user2@test.com", "password": "Pass1234Pass1234!"}



def main():
    print("\n=== USER 1 LOGIN & PROFILE SETUP ===")


    register_user(USER1["username"], USER1["email"], USER1["password"])
    register_user(USER2["username"], USER2["email"], USER2["password"])

    token1 = login_user(USER1["email"], USER1["password"])
    get_user(token1)
    update_user(token1, first_name="Alice", last_name="Smith")
    update_profile(token1, bio="I am Alice", location="Wonderland")
    get_profile(token1)
    get_wallet(token1)

    print("\n=== USER 1 REFERRAL CODE ===")
    # Get referral code of user1 from profile
    headers1 = {"Authorization": f"Token {token1}"}
    res1 = requests.get(f"{BASE_URL}/v1/user/profile/", headers=headers1)
    referral_code_user1 = res1.json().get("referral_code")
    print(f"User 1 Referral Code: {referral_code_user1}")

    print("\n=== USER 2 LOGIN & APPLY REFERRAL ===")
    token2 = login_user(USER2["email"], USER2["password"])
    get_user(token2)
    update_user(token2, first_name="Bob", last_name="Johnson")
    update_profile(token2, bio="I am Bob", location="Narnia")
    process_referral(token2, referral_code_user1)
    get_wallet(token2)

    print("\n=== USER 1 WALLET AFTER REFERRAL ===")
    get_wallet(token1)

    print("\n=== TEST WALLET UPDATE FOR USER 2 ===")
    update_wallet(token2, coins=50, type="increment")
    get_wallet(token2)
    update_wallet(token2, coins=20, type="decrement")
    get_wallet(token2)

    print("\n=== TEST PASSWORD CHANGE FOR USER 2 ===")
    change_password(token2, USER2["password"], "NewPass123!")

    print("\n=== TEST LOGOUT & RELOGIN FOR USER 2 ===")
    logout_user(token2)
    token2_new = login_user(USER2["email"], "NewPass123!")

    print("\n=== TEST DEACTIVATE & DELETE USER 2 ===")
    deactivate_user(token2_new, "NewPass123!")

    print("\n=== TEST FLOW COMPLETED ===")


if __name__ == "__main__":
    main()
