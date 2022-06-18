"""My own exception classes."""

class GetIncorrectAnswer(Exception):
    """Exception for incorrect response."""

    def __init__(self, *args):
        if args:
            self.message = args
        else:
            self.message = None


class AbsenceOfRequiredVariables(Exception):
    """Raises in the absence of one of the necessary variables."""

    pass


class NotForSend(Exception):
    """Raises when bot should not send a message."""

    pass
