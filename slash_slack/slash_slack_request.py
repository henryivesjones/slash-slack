from typing import Optional

from pydantic import BaseModel


class SlashSlackRequest(BaseModel):
    """
    The parsed request from the slash command.
    """

    token: str
    team_id: str
    team_domain: str
    enterprise_id: Optional[str] = None
    enterprise_name: Optional[str] = None
    channel_id: str
    channel_name: str
    user_id: str
    user_name: str
    command: str
    text: str
    response_url: str
    trigger_id: str
    api_app_id: str
