<!-- bildfast:pipeline phase=backend -->
# Build Pipeline

_System-owned. The build advances through these gates; each unlocks only when the user clicks
**Approve & continue**. Agents do the current phase's work and signal readiness — they never edit
this file._

- [x] business    — seeded
- [x] plan        — seeded
- [x] frontend    — seeded
- [>] backend     — seeded
- [ ] testing     — active
- [ ] performance — locked
- [ ] golive      — locked
