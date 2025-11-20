"""VFS configuration wrappers."""

from pydantic import BaseModel, Field

from townlet.vfs.schema import VariableDef


class VariablesReferenceConfig(BaseModel):
    """Configuration wrapper for variables_reference.yaml."""

    version: str = Field(description="Configuration version")
    variables: list[VariableDef] = Field(description="List of variable definitions")
