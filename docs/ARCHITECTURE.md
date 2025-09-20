# AIM Simulation Engine — Architecture

**Version 1.1**
**Written by: QWEN**
**Last Updated: 20.09.2025**

---

## Overview

AIM is a discrete-event, agent-based simulation engine designed for modeling industrial conveyor systems, material handling, and logistics workflows. It combines agent reactivity with block-based process flow and spatial physics.

The architecture is modular, event-driven, and extensible — built around four core concepts:

- **Agents**: Autonomous entities that move, react to events, and hold state.
- **Blocks**: Process nodes that control agent flow (e.g., queues, delays, switches).
- **Spaces**: Spatial systems that manage agent position, collision, and movement.
- **Simulator**: Central controller that runs ticks, manages events, and coordinates blocks and spaces.

---

## Module Structure

```
aim/
├── core/              # Core abstractions: Agent, Block, Simulator, Space
├── blocks/            # Process blocks: Source, Queue, Delay, Switch, etc.
├── entities/          # Spatial entities: Conveyor, TurnTable
├── spaces/            # Spatial managers: ConveyorSpace, NoCollisionSpace
└── visualization/     # Observers: Console, Isometric, Matplotlib viewers
```

---

## Core Modules

### `core/agent.py`

- `BaseAgent`: Base class for all agents.
  - Holds `space_state` (position, progress, target).
  - Emits and receives events via `emit_event()` and `on_event()`.
  - Passive — reacts to block entry and events.

### `core/block.py`

- `BaseBlock`: Abstract base for all blocks.
  - Manages `output_connections` and agent flow.
  - Hooks: `on_enter`, `on_exit`.
  - Internal: `_agents`, `_tick()`.

### `core/simulator.py`

- `Simulator`: Central controller.
  - Runs ticks in fixed order: scheduled events → space update → event delivery → block ticks → event collection.
  - Manages blocks, agents, spaces, and event subscriptions.
  - Supports `schedule_event()` for time-based callbacks.

### `core/space.py`

- `SpaceManager`: Abstract base for spatial systems.
  - Manages agent position, movement, and collision.
  - Methods: `register()`, `unregister()`, `update()`, `is_movement_complete()`.

---

## Block Modules

Blocks control agent flow. All inherit from `BaseBlock`.

### Key Blocks

- `SourceBlock`: Spawns agents.
- `QueueBlock`: Holds agents until downstream accepts.
- `DelayBlock`: Holds agents for fixed ticks.
- `SwitchBlock`: Routes agents by key (e.g., `table_side`).
- `IfBlock`: Routes agents by boolean condition.
- `RestrictedAreaStart/End`: Limits concurrent agents in a zone.
- `ConveyorBlock/Exit`: Moves agents through `ConveyorSpace`.
- `SinkBlock`: Absorbs agents (counts output).

---

## Entity Modules

Entities define spatial geometry.

### `entities/manufacturing/conveyor.py`

- `Conveyor`: Linear 3D path with waypoints.
  - Properties: `points`, `speed`, `connections`.
  - Methods: `get_total_length()`, `get_position_at_progress()`.

### `entities/manufacturing/turn_table.py`

- `TurnTable`: Rotating platform.
  - Properties: `radius`, `angular_speed`.

---

## Space Modules

Spaces manage agent movement and collision.

### `spaces/manufacturing/conveyor_space.py`

- `ConveyorSpace`: Manages agents on conveyors and turntables.
  - Pathfinding via Dijkstra (time-weighted).
  - Collision detection using closed intervals.
  - Progress tracking: `progress_on_entity`, `progress_on_path`.

### `spaces/no_collision_space.py`

- `NoCollisionSpace`: 3D space with no collision.
  - Agents move at constant speed toward target.
  - Used for AGVs, robots, free-moving entities.

---

## Visualization Modules

Observers that render simulation state.

### `visualization/console_viewer.py`

- `ConsoleViewer`: Text-based output.
  - Prints agent state, position, progress each tick.

### `visualization/isometric_viewer.py`

- `IsometricMatplotlibViewer`: 2D isometric projection.
  - Shows Z-axis depth — distinguishes overlapping conveyors.

### `visualization/matplotlib_viewer.py`

- `Matplotlib2DViewer`: 2D top-down view.
  - Draws conveyors, agents, start/end points.

---

## Event System

- Agents emit events via `emit_event(event)`.
- Blocks and processors subscribe via `simulator.subscribe(listener, event)`.
- Events delivered at start of next tick.
- Scheduled events via `simulator.schedule_event(callback, delay_ticks)`.

---

## Spatial System

- Agents must be registered with a space to move.
- Spaces track `agent.space_state`: `position`, `progress`, `path`.
- Movement: `space.update(delta_time)` called each tick.
- Collision: Checked at entry — based on agent length and position.

---

## Process Flow

Agents flow through blocks:

```
Source → Queue → [Spatial Block] → Delay → Switch → Sink
                   (e.g., ConveyorBlock)
```

- Blocks are connected via `block.connect(next_block)`.
- Agents passed via `take(agent)` → may reject (collision, full).
- `QueueBlock` retries rejected agents next tick.

---

## Design Principles

1. **Explicit over implicit** — no hidden state, no magic.
2. **Fail fast** — crash on misconfiguration (e.g., unregistered entity).
3. **Single responsibility** — each module has one clear purpose.
4. **Extensible** — easy to add new blocks, spaces, entities.

---

## Example Flow: Box to Table

1. `SourceBlock` spawns `Box` with `target_table=3`.
2. `SwitchBlock` routes to table 3’s `QueueBlock`.
3. `RestrictedAreaStart` (max=1) accepts box.
4. `ConveyorBlock` moves box to table 3 (takes N ticks).
5. `DelayBlock` holds box for 5 ticks.
6. On exit, box emits `table_3_ready_for_tote`.
7. `ToteDispatcher` routes next tote to table 3.
8. Box ejected to `SinkBlock`.

---

