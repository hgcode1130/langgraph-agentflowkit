class AgentFlowKitError(Exception):
    """Base error for AgentFlowKit."""


class DuplicateRegistrationError(AgentFlowKitError):
    """Raised when a tool, skill, or template name is registered twice."""


class MissingInputError(AgentFlowKitError):
    """Raised when a workflow template requires an absent input."""


class ModelRoutingError(AgentFlowKitError):
    """Raised when no model profile can execute a workflow step."""


class ModelClientError(AgentFlowKitError):
    """Raised when a model provider request fails or returns invalid data."""


class PlanningError(AgentFlowKitError):
    """Raised when a request cannot be planned explicitly."""


class RegistryLookupError(AgentFlowKitError):
    """Raised when a requested registry entry is unknown."""
