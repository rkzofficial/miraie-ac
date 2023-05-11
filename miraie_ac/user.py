class User:
    access_token: str
    expires_in: int
    refresh_token: str
    user_id: str

    def __init__(
        self,
        access_token: str,
        expires_in: int,
        refresh_token: str,
        user_id: str,
    ):
        self.access_token = access_token
        self.expires_in = expires_in
        self.refresh_token = refresh_token
        self.user_id = user_id
