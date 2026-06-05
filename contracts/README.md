# Event Contracts v1

This folder contains contract-first schemas for cross-team integration.

## Versioning policy
- Non-breaking changes: add optional fields only.
- Breaking changes: create a new major version folder (v2, v3...).
- Producers and consumers must validate payloads against the same major version.

## Topics
- trade.tick
- kline.partial
- kline.closed
- system.gap_detected
- api.market.klines.response

## Validation
- Backend can validate with JSON Schema compatible validators.
- Frontend can validate with Zod generated from schema, or direct JSON Schema tooling.
