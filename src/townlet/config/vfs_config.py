"""VFS configuration wrappers."""

from pydantic import BaseModel, Field, model_validator

from townlet.vfs.schema import VariableDef, VariableScope


class VariablesReferenceConfig(BaseModel):
    """Configuration wrapper for variables_reference.yaml."""

    version: str = Field(description="Configuration version")
    variables: list[VariableDef] = Field(description="List of variable definitions")

    @model_validator(mode="after")
    def reject_item_scoped_variables(self) -> "VariablesReferenceConfig":
        for variable in self.variables:
            if variable.scope == VariableScope.ITEM:
                raise ValueError("variables_reference.yaml cannot define item-scoped variables; use vfs_profiles.yaml item_profiles.")
        return self
