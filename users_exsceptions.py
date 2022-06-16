"""My own exception classes."""

class GetIncorrectAnswer(Exception):
    """Exception for incorrect response."""

    # def __init__(self, *args):
    #     if args:
    #         self.message = args[0]
    #     else:
    #         self.message = None

    # def __str__(self):
    #     print('calling str')
    #     if self.message:
    #         return 'MyCustomError, {0} '.format(self.message)
    #     else:
    #         return 'MyCustomError has been raised'
    pass


class AbsenceOfRequiredVariables(Exception):
    """Raises in the absence of one of the necessary variables."""

    pass


class ConnectionTimeOut(Exception):

    pass


class NotForSend(Exception):
    """Raises when bot should not send a message."""

    pass
