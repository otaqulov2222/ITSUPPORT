from pydantic import BaseModel, Field


class LoginRequest(BaseModel):
    # Login yoki email (masalan: adminitsupport)
    email: str = Field(min_length=3, max_length=255)
    password: str = Field(min_length=8, max_length=128)


class RefreshRequest(BaseModel):
    refresh_token: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class MeResponse(BaseModel):
    id: str
    email: str
    full_name: str
    roles: list[str]
    permissions: list[str]
