class LoginActions:
    def __init__(self, login_page, users):
        self.login_page = login_page
        self.users = users

    def login_as(self, user_type):
        user = self.users[user_type]

        self.login_page.login(user["username"], user["password"])
