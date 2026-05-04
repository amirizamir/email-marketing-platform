from pydantic import BaseModel, EmailStr


class ContactOut(BaseModel):
    id: int
    email: EmailStr
    list_id: int

    model_config = {"from_attributes": True}


class ContactsUploadResult(BaseModel):
    imported: int
    skipped_invalid: int
    skipped_duplicate: int
