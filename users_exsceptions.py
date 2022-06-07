"""My own exception classes."""

class GetIncorrectAnswer(Exception):
    """Exception for incorrect response."""

    pass


class AbsenceOfRequiredVariables(Exception):
    """Rises in the absence of one of the necessary variables."""

    pass