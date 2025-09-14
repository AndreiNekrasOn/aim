# AIM Simulation Engine — Architecture

## Core Philosophy

- **Discrete-time, agent-based simulation.**
- **Block-driven flow control** — agents move through blocks.
- **Event-driven interaction** — agents emit string events, blocks react.
- **Spatial simulation optional** — decoupled from flow control.
- **No hidden state** — all buffering explicit (`QueueBlock`).
- **User-defined logic** — callbacks, events, conditions, all modifying agent state.

---

## Boundaries

### 1. Flow Control Blocks
Control agent movement. Do not modify agent state (beyond routing and user callbacks).

- `SourceBlock` — spawns agents.
- `QueueBlock` — buffers agents.
- `IfBlock` — routes based on condition.
- `GateBlock` — opens/closes based on state/event.
- `DelayBlock` — holds agents for N ticks.
- `SinkBlock` — absorbs agents.

### 2. State Transformation Blocks
Modify agent state or split/combine agents.

- `CombineBlock` — merges N agents into one (sets `parent_agents`/`children_agents`).
- `SplitBlock` — splits one agent into itself + children (uses `children_agents`).

### 3. Spatial Simulation
Optional layer for 3D movement, conveyors, zones.

- `ConveyorBlock` — interface to conveyor.
- `Conveyor` — spatial entity (path, speed).
- `ConveyorNetwork` — manages conveyors and agent positions.

---

## Agent Events

- **String-tagged, global, next-tick delivery.**
- Use for lightweight, decoupled notifications.
- Example: agent emits `"task_complete"` → other agents react in `on_event`.

---

## Scheduled Events

- **Callbacks triggered at future ticks.**
- Use for time-based logic (e.g., open gate every 5 ticks).
- Randomized execution order (fixed seed for reproducibility).

---

## Block Contracts

| Block | Input | Output | Side Effects |
|-------|-------|--------|--------------|
| `SourceBlock` | None | Agents to next block | Spawns agents per `spawn_schedule`. |
| `QueueBlock` | Agents from any block | Agents to next block | Buffers agents if next block rejects. |
| `IfBlock` | Agents | Agents to `first` or `second` output | Routes based on callback `condition(agent)`. |
| `GateBlock` | Agents | Agents to next block | Holds agents until open. |
| `DelayBlock` | Agents | Agents to next block after N ticks | Holds agents until timeout |
| `CombineBlock` | Agents to `container` or `pickup` ports | Combined agent to next block | Sets `parent_agents`/`children_agents` for agent |
| `SplitBlock` | Container agent (with `children_agents`) | Container to `first`, children to `second` | Clears container’s `children_agents`. |
| `ConveyorBlock` | Agents | Agents to next block after traversal | Places agents on conveyor, ejects at end. |

---

## Error Handling

- Blocks reject agents -> raise `RuntimeError` (upstream `QueueBlock` must handle).
- Invalid state -> raise immediately (no silent failures).
- Miswired blocks -> raise at connection or first use.

---

## Anti-Patterns

- **Do not** connect blocks directly without `QueueBlock` if downstream can reject.
- **Do not** use agent events for time-critical logic — use scheduled events.
- **Do not** modify `BaseAgent` core attributes outside `CombineBlock`/`SplitBlock`.

---

## Future Work

- Performance profiling.
- Spatial indexing (KD-tree, grid).
- Agent pooling.
- Visualization hooks.
