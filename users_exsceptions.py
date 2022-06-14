"""My own exception classes."""

class GetIncorrectAnswer(Exception):
    """Exception for incorrect response."""

    pass


class AbsenceOfRequiredVariables(Exception):
    """Raises in the absence of one of the necessary variables."""

    pass


class NotForSend(Exception):
    """Raises when bot should not send a message."""

    pass
