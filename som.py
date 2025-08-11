from typing import List
from pydantic import BaseModel



class OrganizationBlock(BaseModel):
    name: str
    is_parent: bool
    branch: List["OrganizationBlock"] = []
