from typing import List, Dict, Any, Optional
from pydantic import BaseModel

class StrategyParameter(BaseModel):
    name: str
    type: str
    default: Optional[Any] = None
    description: Optional[str] = None

class StrategySchema(BaseModel):
    name: str
    description: Optional[str] = None
    parameters: List[StrategyParameter] = []

    class Config:
        from_attributes = True