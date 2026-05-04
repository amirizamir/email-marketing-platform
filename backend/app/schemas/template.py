from pydantic import BaseModel, Field


class TemplateCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    subject: str = Field(min_length=1, max_length=998)
    html_content: str = Field(min_length=1)


class TemplateUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=255)
    subject: str | None = Field(default=None, min_length=1, max_length=998)
    html_content: str | None = Field(default=None, min_length=1)


class TemplateOut(BaseModel):
    id: int
    name: str
    subject: str
    html_content: str
    version: int

    model_config = {"from_attributes": True}
