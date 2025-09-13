# aim/__init__.py

# Core simulation classes
from .core.agent import BaseAgent
from .core.block import BaseBlock
from .core.simulator import Simulator
from .core.space import Space, SpatialEntity

# Built-in blocks
from .blocks.source import SourceBlock
from .blocks.sink import SinkBlock
from .blocks.if_block import IfBlock

# Manufacturing-specific blocks and entities
from .blocks.manufacturing.conveyor_block import ConveyorBlock
from .entities.manufacturing.conveyor import Conveyor
from .spaces.manufacturing.conveyor_network import ConveyorNetwork

__all__ = [
    # Core
    'BaseAgent',
    'BaseBlock',
    'Simulator',
    'Space',
    'SpatialEntity',

    # Generic Blocks
    'SourceBlock',
    'SinkBlock',
    'IfBlock',

    # Manufacturing
    'ConveyorBlock',
    'Conveyor',
    'ConveyorNetwork',
]
