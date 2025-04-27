class AuthError(Exception):
    def __init__(self, service: str, message: str):
        self.service = service
        self.message = message
    def __str__(self):
        return f'{self.service} error: {self.message}'


class PasswordError(AuthError):
    # def __init__(self, service: str,  message: str):
    #     super().__init__(service, message)
    def __str__(self):
        return f'{self.service} password error'


class UsernameError(AuthError):
    def __str__(self):
        return f'{self.service} username error' + (' (case-sensitive)' if self.service == 'InteleViewer' else '')


class ServerError(Exception):
    def __init__(self, code: int, message: str):
        self.code = code
        self.message = message

    def __str__(self):
        return f'{self.message} (code {self.code})'


class PowerscribeServerError(ServerError):
    def __init__(self, message: str, error_type: str, code: int, stack_trace: str):
        super().__init__(code, message)
        self.error_type = error_type
        self.stack_trace = stack_trace

    def __str__(self):
        return f'{self.error_type} error: {super().__str__()}'

    def __repr__(self):
        return f'WebServiceError(message={self.message}, error_type={self.error_type}, code={self.code})\n' + '\n'.join(
            self.stack_trace)

class InteleviewerServerError(ServerError):
    def __init__(self, code: int, message: str, data: dict):
        super().__init__(code, message)
        self.data = data
    def __str__(self):
        return f'{self.message} (code {self.code})'