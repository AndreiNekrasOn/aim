# AIM Simulation Engine — Public API Documentation

Written by QWEN

---

## Core Modules

### `aim.core.agent.BaseAgent`

**Description**: Base class for all agents in the simulation. Agents are passive data containers that react to entering blocks or receiving events.

**Public Methods/Attributes**:

- `__init__(self)`
  - Initializes agent with default dimensions and empty space state.
- `on_enter_block(self, block: 'BaseBlock') -> None`
  - Called when agent enters a block. Override to react.
- `on_event(self, event: str) -> None`
  - Called when agent receives an event. Override to react.
- `emit_event(self, event: str) -> None`
  - Emit an event to be delivered to all agents next tick (exact string match).
- `width: float`
  - Agent's width (default: 0.0).
- `length: float`
  - Agent's length (default: 0.0).
- `space_state: Dict[str, Any]`
  - Space-specific state (e.g., `{"progress": 0.5}` for conveyors).
- `current_block: Optional['BaseBlock']`
  - Read-only property: current block the agent is in.

---

### `aim.core.block.BaseBlock`

**Description**: Abstract base class for all blocks. Blocks control agent flow and may hold agents.

**Public Methods/Attributes**:

- `__init__(self, simulator: 'Simulator')`
  - Initializes block and auto-registers with simulator.
- `take(self, agent: BaseAgent) -> None`
  - Accept an agent into this block. Must be overridden by subclasses.
- `on_enter: Optional[Callable[[BaseAgent], None]]`
  - User-provided callback: called when agent enters block.
- `on_exit: Optional[Callable[[BaseAgent], None]]`
  - User-provided callback: called when agent exits block (before ejection).
- `output_connections: List[Optional['BaseBlock']]`
  - List of output blocks (set via `.connect()`).

---

### `aim.core.simulator.Simulator`

**Description**: Central simulation controller. Manages ticks, blocks, agents, and events.

**Public Methods/Attributes**:

- `__init__(self, max_ticks: int = 1000, random_seed: int = 42, space: Optional[SpaceManager] = None)`
  - Initializes simulator with optional space manager.
- `add_block(self, block: BaseBlock) -> None`
  - Register a block (auto-called if block initialized with simulator).
- `subscribe(self, agent: BaseAgent, event: str) -> None`
  - Subscribe agent to receive an event (exact match).
- `schedule_event(self, callback: Callable[[int], None], delay_ticks: int = 0, recurring: bool = False) -> None`
  - Schedule a callback to be executed at `current_tick + delay_ticks`.
- `run(self) -> None`
  - Run simulation until `max_ticks` reached.
- `current_tick: int`
  - Current tick number.
- `max_ticks: int`
  - Maximum ticks before simulation stops.

---

### `aim.core.space.SpaceManager`

**Description**: Abstract base class for spatial systems. Manages agent position, movement, and collision. Agents must be registered with the space before entering spatial blocks. Spatial entities (e.g., `Conveyor`, `TurnTable`) must be registered with the space before use.

**Public Methods**:

- `register_entity(self, entity: Any) -> None`
  Register a spatial entity (e.g., `Conveyor`, `TurnTable`) with the space. Must be called before any agent attempts to use the entity. Idempotent.

- `is_entity_registered(self, entity: Any) -> bool`
  Check if a spatial entity is registered with the space.

- `register(self, agent: BaseAgent, initial_state: Dict[str, Any]) -> bool`
  Register agent with initial state.
  Returns False if agent cannot be placed (e.g., collision, unregistered entity).
  Expected keys in `initial_state`: "start_entity", "end_entity" (for pathfinding).

- `unregister(self, agent: BaseAgent) -> bool`
  Unregister agent from space. Returns False if agent was not registered.

- `update(self, delta_time: float) -> None`
  Advance all agents by delta_time.
  For `Conveyor`: progress += (speed * delta_time) / total_length.

- `is_movement_complete(self, agent: BaseAgent) -> bool`
  Check if agent has completed its current movement (e.g., reached end of path).

---

## Block Modules

### `aim.blocks.source.SourceBlock`

**Description**: Spawns new agents into the simulation each tick.

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, agent_class: Type[BaseAgent] = BaseAgent, spawn_schedule: Callable[[int], int] = lambda tick: 1)`
  - `spawn_schedule`: Function that takes `current_tick` and returns number of agents to spawn.

---

### `aim.blocks.queue.QueueBlock`

**Description**: Holds agents until downstream block can accept them.

**Public Methods/Attributes**:

- `size: int`
  - Current number of agents in queue.
- `max_size: int`
  - Peak number of agents ever queued.

---

### `aim.blocks.delay.DelayBlock`

**Description**: Holds agents for a fixed number of ticks or until an event is received.

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, delay_ticks: int = -1, release_event: str = None)`
  - `delay_ticks = -1` + `release_event`: Hold indefinitely until event received.
- `size: int`
  - Number of agents currently delayed.

---

### `aim.blocks.gate.GateBlock`

**Description**: Gates agent flow based on open/closed state.

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, initial_state: str = "closed", release_mode: str = "one")`
  - `release_mode`: `"one"` (release one agent per tick) or `"all"` (release all at once).
- `toggle(self) -> None`
  - Toggle gate state (open ↔ closed).
- `state(self) -> str`
  - Return current state (`"open"` or `"closed"`).
- `size: int`
  - Number of agents waiting at gate.

---

### `aim.blocks.if_block.IfBlock`

**Description**: Routes agents to different outputs based on a condition.

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, condition: Callable[[BaseAgent], bool])`
  - `condition`: Function that takes agent and returns `True`/`False`.
- `connect_first(self, block: BaseBlock) -> None`
  - Connect the "True" branch.
- `connect_second(self, block: BaseBlock) -> None`
  - Connect the "False" branch.

---

### `aim.blocks.restricted_area_start.RestrictedAreaStart`

**Description**: Controls entry into a restricted area (max N agents at a time).

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, max_agents: int = 1)`
  - `max_agents`: Maximum agents allowed in restricted area.
- `set_end(self, end_block: 'RestrictedAreaEnd') -> None`
  - Bind to `RestrictedAreaEnd`.
- `size: int`
  - Number of agents waiting to enter.
- `active_agents: int`
  - Number of agents currently inside restricted area.

---

### `aim.blocks.restricted_area_end.RestrictedAreaEnd`

**Description**: Marks exit from a restricted area (frees up a slot).

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, start_block: 'RestrictedAreaStart')`
  - `start_block`: Paired `RestrictedAreaStart`.

---

### `aim.blocks.combine.CombineBlock`

**Description**: Combines one container with N pickups into one agent.

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, max_pickups: int = 1)`
  - `max_pickups`: Number of pickups to collect before ejecting container.
- `container: _CombineInputPort`
  - Input port for containers.
- `pickup: _CombineInputPort`
  - Input port for pickups.
- `container_held: bool`
  - `True` if container is held.
- `pickup_queue_size: int`
  - Number of pickups queued.

---

### `aim.blocks.split.SplitBlock`

**Description**: Splits a container agent into itself and its children.

**Public Methods/Attributes**:

- `connect_first(self, block: BaseBlock) -> None`
  - Connect output for container.
- `connect_second(self, block: BaseBlock) -> None`
  - Connect output for children.

---

### `aim.blocks.sink.SinkBlock`

**Description**: Absorbs and holds agents indefinitely.

**Public Methods/Attributes**:

- `count: int`
  - Number of agents absorbed.

---

### `aim.blocks.manufacturing.conveyor_block.ConveyorBlock`

**Description**: Block that moves agents through a `ConveyorSpace` from `start_entity` to `end_entity`.
Does NOT eject agents when movement is complete -- must use `ConveyorExit`.
Enforces one agent entry per tick -- subsequent agents in same tick are rejected with `RuntimeError`.
Holds agents that complete movement if downstream block rejects them -- retries ejection each tick.

**Public Methods/Attributes**:

- `__init__(self, simulator: Simulator, space: SpaceManager, start_entity: Any, end_entity: Any)`
  Raises `ValueError` if `start_entity` or `end_entity` is not registered with `space`.

- `take(self, agent: BaseAgent) -> None`
  Place agent in space at `start_entity`.
  Rejects agent if:
    -- Space registration fails (collision, invalid entity), or
    -- An agent already entered this tick (`RuntimeError: only one agent per tick`).

- `_tick(self) -> None`
  Ejects agents for which `space.is_movement_complete(agent)` is `True`.
  If ejection fails (downstream rejects), agent remains in block and retries next tick.

---

### `aim.blocks.manufacturing.conveyor_exit.ConveyorExit`

**Description**: Removes agents from space (frees occupancy). Does not unregister agents -- unregistration is handled by `ConveyorBlock` upon successful ejection.

**Public Methods/Attributes**:

- `take(self, agent: BaseAgent) -> None`
  Simply passes agent to next block. Does not interact with space.

---

## Entity Modules

### `aim.entities.manufacturing.conveyor.Conveyor`

**Description**: A linear path in 3D space defined by waypoints.

**Public Methods/Attributes**:

- `__init__(self, points: List[Tuple[float, float, float]], speed: float = 1.0, name: str = "")`
  - `points`: List of 3D waypoints.
  - `speed`: Progress increment per tick.
- `get_total_length(self) -> float`
  - Calculate total length of conveyor path.
- `get_position_at_progress(self, progress: float) -> Tuple[float, float, float]`
  - Get 3D position at normalized progress (0.0 to 1.0).
- `connections: List[Any]`
  - List of connected spatial entities (for pathfinding).

---

### `aim.entities.manufacturing.turn_table.TurnTable`

**Description**: A rotating platform that turns agents by a target angle.

**Public Methods/Attributes**:

- `__init__(self, radius: float, angular_speed: float, name: str = "")`
  - `radius`: Radius of turntable.
  - `angular_speed`: Radians per tick.
- `get_position_at_angle(self, angle: float) -> Tuple[float, float, float]`
  - Get 3D position at angle (radians).
- `connections: List[Any]`
  - List of connected spatial entities.

---

## Space Modules

### `aim.spaces.manufacturing.conveyor_space.ConveyorSpace`

**Description**: Manages agents moving on a graph of conveyors, turntables, and other spatial entities.

**Public Methods**:

- Inherits all methods from `SpaceManager` (see above).

---

## Example Modules

- `examples/boltzman_wealth_demo.py`: Simulates wealth distribution via scheduled events.
- `examples/callback_event_demo.py`: Demonstrates agent/block callbacks and global events.
- `examples/happy_agents_demo.py`: Routes agents based on state using `IfBlock`.
- `examples/scheduled_event_demo.py`: Shows scheduled event execution.

---

## Test Modules

- `tests/unit/`: Smoke tests for individual blocks.
- `tests/integration/`: End-to-end tests for block combinations.

---

This documentation covers all public methods and attributes of the AIM simulation engine. Internal methods (prefixed with `_`) are not documented — they are not part of the public API.
