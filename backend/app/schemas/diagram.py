from pydantic import BaseModel, ConfigDict
from typing import Dict, Any, Optional, Literal

class DiagramGenerationResponse(BaseModel):
    model_config = ConfigDict(extra='allow')
    
    strategy: Literal['primitive', 'code']
    primitive_name: Optional[str] = None
    primitive_params: Optional[Dict[str, Any]] = None
    python_code: Optional[str] = None
