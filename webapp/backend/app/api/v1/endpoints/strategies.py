from fastapi import APIRouter
from typing import List
import inspect

from app.schemas.strategy import StrategySchema, StrategyParameter
from app.services.backtest_runner import STRATEGY_CLASSES

router = APIRouter()

@router.get("/", response_model=List[StrategySchema])
def list_strategies():
    """
    List available backtesting strategies with their parameters.
    """
    strategies = []
    for name, cls in STRATEGY_CLASSES.items():
        # Get constructor signature
        sig = inspect.signature(cls.__init__)
        params = []
        for param_name, param in list(sig.parameters.items())[1:]:  # skip 'self'
            if param_name == 'kwargs':
                continue
            param_type = str(param.annotation) if param.annotation != inspect.Parameter.empty else "Any"
            default = param.default if param.default != inspect.Parameter.empty else None
            params.append(StrategyParameter(
                name=param_name,
                type=param_type,
                default=default,
                description=None
            ))
        strategies.append(StrategySchema(
            name=name,
            description=cls.__doc__ or "",
            parameters=params
        ))
    return strategies