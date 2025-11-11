from test.user import *

# Test users
USER1 = {"username": "user1", "email": "user1@test.com", "password": "Pass1234Pass1234!"}
USER2 = {"username": "user2", "email": "user2@test.com", "password": "Pass1234Pass1234!"}



def main():

    register_user(USER1["username"], USER1["email"], USER1["password"])
    register_user(USER2["username"], USER2["email"], USER2["password"])


if __name__ == "__main__":
    main()
