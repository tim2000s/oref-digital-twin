# ingestion

Nightscout pulls — `devicestatus`, `entries`, `treatments`, `profile` — normalised to a common schema. Chunk to ~7-day windows with backoff (long windows 502). Read-only tokens only.

See [../DESIGN.md](../DESIGN.md) §5.1 and §12 phase 1. Not implemented yet — scaffold only.
