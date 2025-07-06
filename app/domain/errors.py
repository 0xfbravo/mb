"""Shared error classes for domain layer."""

from typing import Optional


class DomainError(Exception):
    """Base exception for domain-related errors."""

    pass


class ValidationError(DomainError):
    """Raised when domain validation fails."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class NotFoundError(DomainError):
    """Raised when a resource is not found."""

    def __init__(self, resource_type: str, identifier: str):
        self.resource_type = resource_type
        self.identifier = identifier
        super().__init__(f"{resource_type} with identifier {identifier} not found")


class InvalidInputError(DomainError):
    """Raised when input data is invalid."""

    def __init__(self, message: str, field: Optional[str] = None):
        self.message = message
        self.field = field
        super().__init__(message)


class BusinessRuleError(DomainError):
    """Raised when a business rule is violated."""

    def __init__(self, message: str, rule: Optional[str] = None):
        self.message = message
        self.rule = rule
        super().__init__(message)


class ConfigurationError(DomainError):
    """Raised when configuration is invalid or missing."""

    def __init__(self, message: str, config_key: Optional[str] = None):
        self.message = message
        self.config_key = config_key
        super().__init__(message)
