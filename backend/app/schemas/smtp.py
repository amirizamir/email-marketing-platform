from pydantic import BaseModel, EmailStr, Field


class SMTPAccountCreate(BaseModel):
    name: str = Field(min_length=1, max_length=255)
    smtp_host: str
    smtp_port: int = Field(ge=1, le=65535)
    username: str
    password: str
    from_email: EmailStr
    from_name: str = ""
    use_tls: bool = True


class SMTPAccountOut(BaseModel):
    id: int
    name: str
    smtp_host: str
    smtp_port: int
    username: str
    from_email: str
    from_name: str
    use_tls: bool

    model_config = {"from_attributes": True}


class SMTPTestRequest(BaseModel):
    smtp_host: str
    smtp_port: int = Field(ge=1, le=65535)
    username: str
    password: str
    use_tls: bool = True


class SMTPTestExisting(BaseModel):
    smtp_id: int
