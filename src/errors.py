"""Error model for the RLS governance pipeline (spec section 36)."""


class RlsGovernanceError(Exception):
    """Base class for all errors raised by this application."""

    code = "UNKNOWN_ERROR"


class AuthenticationFailedError(RlsGovernanceError):
    code = "AUTHENTICATION_FAILED"


class FabricAuthorizationFailedError(RlsGovernanceError):
    code = "FABRIC_AUTHORIZATION_FAILED"


class SemanticModelNotFoundError(RlsGovernanceError):
    code = "SEMANTIC_MODEL_NOT_FOUND"


class GetDefinitionFailedError(RlsGovernanceError):
    code = "GET_DEFINITION_FAILED"


class EncryptedSensitivityLabelNotSupportedError(RlsGovernanceError):
    code = "ENCRYPTED_SENSITIVITY_LABEL_NOT_SUPPORTED"


class DuplicateDefinitionPartError(RlsGovernanceError):
    code = "DUPLICATE_ROLE_PATH"

    def __init__(self, path: str):
        super().__init__(f"Duplicate definition part path: {path}")
        self.path = path


class RolePathCollisionError(RlsGovernanceError):
    code = "ROLE_PATH_COLLISION"


class ConcurrentModelChangeDetectedError(RlsGovernanceError):
    code = "CONCURRENT_MODEL_CHANGE_DETECTED"


class UpdateDefinitionFailedError(RlsGovernanceError):
    code = "UPDATE_DEFINITION_FAILED"


class LroFailedError(RlsGovernanceError):
    code = "LRO_FAILED"


class LroTimeoutError(RlsGovernanceError):
    code = "LRO_TIMEOUT"


class FabricRateLimitedError(RlsGovernanceError):
    code = "FABRIC_RATE_LIMITED"


class PostDeploymentValidationFailedError(RlsGovernanceError):
    code = "POST_DEPLOYMENT_VALIDATION_FAILED"


class RoleDeleteNotSupportedError(RlsGovernanceError):
    code = "ROLE_DELETE_NOT_SUPPORTED"
