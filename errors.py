
class AuthError(Exception):
    def __init__(self, message):
        self.message = message
    def __str__(self):
        return f'{self.__class__.__name__}: {self.message}'

class PasswordError(AuthError): pass

class UsernameError(AuthError): pass

class ServerError(Exception): pass

class InteleviewerServerError(ServerError):
    def __init__(self, code: int, message: str, data: dict):
        self.code = code
        self.message = message
        self.data = data
    def __str__(self):
        return f'{self.message} (code {self.code})'