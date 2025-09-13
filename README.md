This is a Python-based simulation engine for discrete-time agent modeling, centered around a block-driven execution model.
Agents are passive data objects that react to entering blocks and receiving string-tagged events.
Blocks — such as Source, Convey, Sink, and If — control agent movement and flow.
The event loop drives simulation ticks: it triggers spawns, advances agents through conveyors, and delivers events emitted in the previous tick to agents whose declared interest tags match the event prefix.
Events are strings, delivery is next-tick only to prevent recursion, and filtering is done via simple string prefix matching.
Agents influence flow only by changing internal state (e.g., setting a flag) or emitting events — blocks read that state to make routing decisions.
The entire system is designed for local, single-user prototyping — no auth, no scaling, no deployment complexity. Inheritance is used minimally: agents subclass a base class to override two hooks — on_enter_block and on_event. The architecture is intentionally simple, avoiding over-engineering, to validate the block-flow model quickly before a full rewrite in a faster language.
