import pydantic


class Request(pydantic.BaseModel):
    text: str


class Response(pydantic.BaseModel):
    text: str
