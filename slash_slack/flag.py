from pydantic import BaseModel


class Flag(BaseModel):
    help: str = ""
