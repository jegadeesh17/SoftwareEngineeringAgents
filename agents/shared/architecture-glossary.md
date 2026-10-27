## Architecture vocabulary

Use these terms exactly, in critiques, reviews and reports.

- **Module:** any unit of code (service, class, function group) with an **Interface** (what callers must know) and an **Implementation** (the secrets it hides).
- **Deep module (target):** hides complex implementation behind a simple, minimal interface. High capability per unit of interface learned.
- **Shallow module (red flag):** a complex or chatty interface, pass-through parameters, or leaked internal state, hiding little logic.
- **Seam:** the exact boundary where two module interfaces meet. All mocking and contract testing happens at seams.
- **Adapter:** a concrete implementation behind a seam's interface (a live DB or API adapter, or an in-memory fake for tests).
- **Locality:** how far related logic and state changes are collocated in one deep module. Low locality: one business rule change edits several files across layers.
- **Leverage:** reliable behavior a caller gets per unit of interface complexity.
