# AIM Simulation Engine — Public API Documentation

**Version 1.1**
**Written by QWEN**
**Last Updated: 20.09.2025**

---

## Core Modules

### `aim.core.agent.BaseAgent`

**Description**: Base class for all agents in the simulation. Agents are passive — react to block entry and events. Spatial state is managed via `space_state`.

**Public Methods/Attributes**:

- `__init__(self)`
  - Initializes agent with default dimensions and empty space state.
- `on_enter_block(self, block: 'BaseBlock') -> None`
  - Called when agent enters a block. Override to react.
- `on_event(self, event: str) -> None`
  - Called when agent receives an event. Override to react.
- `emit_event(self, event: str) -> None`
  - Emit an event to be delivered to subscribed agents next tick.
- `width: float`
  - Agent's width (default: 0.0).
- `length: float`
  - Agent's length (default: 0.0).
- `space_state: Dict[str, Any]`
  - Space-specific state (e.g., `{"position": (x,y,z), "progress_on_entity": 0.5, "path": [...]}`).
- `current_block: Optional['BaseBlock']`
  - Read-only: current block the agent is in.

---

### `aim.core.block.BaseBlock`

**Description**: Abstract base class for all blocks. Blocks control agent flow and may hold agents.

**Public Methods/Attributes**:

- `__init__(self, simulator: 'Simulator')`
  - Initializes block and auto-registers with simulator.
- `take(self, agent: BaseAgent) -> None`
  - Accept an agent into this block. Must be overridden by subclasses.
- `on_enter: Optional[Callable[[BaseAgent], None]]`
  - Callback: called when agent enters block.
- `on_exit: Optional[Callable[[BaseAgent], None]]`
  - Callback: called when agent exits block (before ejection).
- `output_connections: List[Optional['BaseBlock']]`
  - List of output blocks (set via `.connect()`).

---

### `aim.core.simulator.Simulator`

**Description**: Central simulation controller. Manages ticks, blocks, agents, events, and named spaces.

**Public Methods/Attributes**:

- `__init__(self, max_ticks: int = 1000, random_seed: int = 42, spaces: Dict[str, SpaceManager])`
  - Initializes simulator with named spaces. At least one space required.
- `add_block(self, block: BaseBlock) -> None`
  - Register a block (auto-called if block initialized with simulator).
- `subscribe(self, agent: BaseAgent, event: str) -> None`
  - Subscribe agent to receive an event (exact match).
- `schedule_event(self, callback: Callable[[int], None], delay_ticks: int = 0, recurring: bool = False) -> None`
  - Schedule callback for `current_tick + delay_ticks`.
- `run(self) -> None`
  - Run simulation until `max_ticks` reached.
- `current_tick: int`
  - Current tick number.
- `max_ticks: int`
  - Maximum ticks before simulation stops.
- `get_space(self, name: str) -> SpaceManager`
  - Get space by name. Raises `KeyError` if not found.

---

### `aim.core.space.SpaceManager`

**Description**: Abstract base class for spatial systems. Manages agent position, movement, collision. Agents and entities must be registered before use.

**Public Methods**:

- `register_entity(self, entity: Any) -> None`
  - Register spatial entity (e.g., `Conveyor`). Idempotent.
- `is_entity_registered(self, entity: Any) -> bool`
  - Check if entity is registered.
- `register(self, agent: BaseAgent, initial_state: Dict[str, Any]) -> bool`
  - Register agent. Returns `False` if rejected (collision, invalid entity).
  - Expected keys: `"start_entity"`, `"end_entity"`, `"start_position"`, `"target_position"`, `"speed"`.
- `unregister(self, agent: BaseAgent) -> bool`
  - Unregister agent. Returns `False` if not registered.
- `update(self, delta_time: float) -> None`
  - Advance all agents by `delta_time`.
- `is_movement_complete(self, agent: BaseAgent) -> bool`
  - Check if agent completed movement (e.g., reached target).

---

## Block Modules

### `aim.blocks.source.SourceBlock`

**Description**: Spawns agents into simulation.

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, agent_class: Type[BaseAgent], spawn_schedule: Callable[[int], int])`
  - `spawn_schedule`: Returns number of agents to spawn at tick.

---

### `aim.blocks.queue.QueueBlock`

**Description**: Holds agents until downstream block accepts them.

**Public Methods/Attributes**:

- `size: int`
  - Current number of agents in queue.

---

### `aim.blocks.delay.DelayBlock`

**Description**: Holds agents for fixed ticks.

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, delay_ticks: int)`
  - Holds agent for `delay_ticks` before ejecting.
- `size: int`
  - Number of agents currently delayed.

---

### `aim.blocks.gate.GateBlock`

**Description**: Gates agent flow based on state.

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, initial_state: str = "closed")`
  - `initial_state`: `"open"` or `"closed"`.
- `toggle(self) -> None`
  - Toggle state.
- `state: str`
  - Current state (`"open"` or `"closed"`).
- `size: int`
  - Number of agents waiting.

---

### `aim.blocks.if_block.IfBlock`

**Description**: Routes agents to outputs based on condition.

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, condition: Callable[[BaseAgent], bool])`
  - `condition`: Returns `True`/`False` for agent.
- `connect_first(self, block: BaseBlock) -> None`
  - Connect "True" branch (output 0).
- `connect_second(self, block: BaseBlock) -> None`
  - Connect "False" branch (output 1).

---

### `aim.blocks.restricted_area_start.RestrictedAreaStart`

**Description**: Controls entry to restricted area (max N agents).

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, max_agents: int)`
  - `max_agents`: Max concurrent agents.
- `set_end(self, end_block: 'RestrictedAreaEnd') -> None`
  - Bind to exit block.
- `size: int`
  - Agents waiting to enter.
- `active_agents: int`
  - Agents currently inside.

---

### `aim.blocks.restricted_area_end.RestrictedAreaEnd`

**Description**: Marks exit from restricted area.

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, start_block: 'RestrictedAreaStart')`
  - `start_block`: Paired start block.

---

### `aim.blocks.switch.SwitchBlock`

**Description**: Routes agents to outputs based on key (like switch-case).

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, key_func: Callable[[BaseAgent], Hashable])`
  - `key_func`: Returns key (str, int, Conveyor, etc.) for routing.
- `connect(self, key: Hashable, block: BaseBlock) -> None`
  - Connect output block to key.

---

### `aim.blocks.sink.SinkBlock`

**Description**: Absorbs agents indefinitely.

**Public Methods/Attributes**:

- `count: int`
  - Number of agents absorbed.

---

### `aim.blocks.manufacturing.conveyor_block.ConveyorBlock`

**Description**: Moves agents through `ConveyorSpace` from `start_entity` to `end_entity`.
Does NOT eject agents — must use `ConveyorExit`.
Enforces one agent per tick — rejects subsequent agents in same tick.
Holds agents that complete movement if downstream rejects — retries ejection.

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, space_name: str, start_entity: Any, end_entity: Any)`
  - `space_name`: Name of space in simulator.
  - Raises `ValueError` if entities not registered.
- `take(self, agent: BaseAgent) -> None`
  - Place agent in space. Rejects if collision or agent already entered this tick.

---

### `aim.blocks.manufacturing.conveyor_exit.ConveyorExit`

**Description**: Passes agent to next block. Does not interact with space.

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, space_name: str)`
  - `space_name`: Name of space (for consistency — not used).

---

## Entity Modules

### `aim.entities.manufacturing.conveyor.Conveyor`

**Description**: Linear 3D path defined by waypoints.

**Public Methods/Attributes**:

- `__init__(self, points: List[Tuple[float, float, float]], speed: float = 1.0, name: str = "")`
  - `points`: 3D waypoints.
  - `speed`: Meters per tick.
- `get_total_length(self) -> float`
  - Total path length.
- `get_position_at_progress(self, progress: float) -> Tuple[float, float, float]`
  - 3D position at progress (0.0 to 1.0).
- `connections: List[Any]`
  - Connected spatial entities (for pathfinding).

---

### `aim.entities.manufacturing.turn_table.TurnTable`

**Description**: Rotating platform.

**Public Methods/Attributes**:

- `__init__(self, radius: float, angular_speed: float, name: str = "")`
  - `radius`: Radius.
  - `angular_speed`: Radians per tick.
- `get_position_at_angle(self, angle: float) -> Tuple[float, float, float]`
  - 3D position at angle.
- `connections: List[Any]`
  - Connected entities.

---

## Space Modules

### `aim.spaces.manufacturing.conveyor_space.ConveyorSpace`

**Description**: Manages agents on conveyors and turntables. Supports pathfinding (Dijkstra, time-weighted). Collision detection uses closed intervals.

**Public Methods**:

- Inherits all from `SpaceManager`.

---

### `aim.spaces.no_collision_space.NoCollisionSpace`

**Description**: 3D space with no collision. Agents move at constant speed toward target.

**Public Methods**:

- Inherits all from `SpaceManager`.

---

## Example Modules

- `examples/boltzman_wealth_demo.py`: Wealth distribution via events.
- `examples/callback_event_demo.py`: Agent/block callbacks.
- `examples/happy_agents_demo.py`: Routing with `IfBlock`.
- `examples/scheduled_event_demo.py`: Scheduled events.

---

## Test Modules

- `tests/unit/`: Smoke tests for blocks.
- `tests/integration/`: End-to-end tests.
- `tests/stress/`: Performance and scale tests.

---

This documentation covers all public methods and attributes. Internal methods (prefixed with `_`) are not part of the public API.
