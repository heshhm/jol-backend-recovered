from test.user import *

USERNAME = "testuser"
EMAIL = "test@gmail.com"
PASSWORD = "FUCKYOU123FUCKYOU123"
NEW_PASSWORD = "FUCKYOU123FUCKYOU123"

def main():
    # register_user(USERNAME, EMAIL, PASSWORD)
    token = login_user(EMAIL , PASSWORD)
    get_profile(token)
    update_profile(token, first_name="Alice", last_name="Smith", location="Wonderland")

    pass

if __name__ == "__main__":
    main()
