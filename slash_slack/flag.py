from pydantic import BaseModel


class Flag(BaseModel):
    value: str
    help: str = ""
