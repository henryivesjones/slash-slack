class SlashSlackException(Exception):
    """
    Base Exception for all Slash Slack Exceptions
    """


class NoSigningSecretException(SlashSlackException):
    """
    Exception raised when no signing secret is provided.
    """


class DuplicateCommandException(SlashSlackException):
    """
    Exception raised when a command is registered twice.
    """


class MultipleSlashSlackRequestParametersException(SlashSlackException):
    """
    Exception raised when a command function has multiple SlashSlackRequest parameters.
    """


class ParamAfterUnknownLengthListException(SlashSlackException):
    """
    Exception raised when a command function has a parameter after a SlashSlackRequest parameter.
    """


class InvalidDefaultValueException(SlashSlackException):
    """
    Exception raised when a command function has a parameter with an invalid default value.
    """


class InvalidAnnotationException(SlashSlackException):
    """
    Exception raised when a command function has a parameter with an invalid annotation.
    """
