class ConfigurationError(Exception):
    """Base class for configuration-related exceptions."""

    pass


class ConfigurationLoadError(ConfigurationError):
    """Exception raised when a configuration file cannot be loaded."""
    pass


class ConfigurationValidationError(ConfigurationError):
    """Exception raised when a configuration file fails validation."""
    pass
