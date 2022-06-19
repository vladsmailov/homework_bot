"""My own exception classes."""

from email import message


class GetIncorrectAnswer(Exception):
    """Exception for incorrect response."""

    def __init__(self, *args):
        if args:
            self.message = args
            

class NotForSend(Exception):
    """Raises when bot should not send a message."""

    pass
