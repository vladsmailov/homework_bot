"""My own exception classes."""

class GetIncorrectAnswer(Exception):
    """Exception for incorrect response."""

    pass


class AbsenceOfRequiredVariables(Exception):
    """Raises in the absence of one of the necessary variables."""

    pass


class CanNotSendMessage(Exception):
    """Raises when bot can't send message."""

    pass
