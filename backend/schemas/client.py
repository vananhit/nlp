from pydantic import BaseModel

class ClientCredentials(BaseModel):
    client_id: str
    client_secret: str
