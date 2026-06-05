# Latency Benchmark Guide

## Objective
Measure end-to-end latency from event ingest timestamp to websocket delivery and track p50, p95, p99 across builds.

## Local run
From backend folder:
- python scripts/latency_e2e_probe.py --sample-size 120 --assert-p95-ms 300 --output reports/latency/latest.json
- python scripts/latency_trend_report.py

## Output
- JSON report: reports/latency/latest.json
- Trend markdown table: reports/latency/trend.md

## SLO
- Target: p95 < 300ms
- Ideal: p95 < 150ms

## Diagnostics when failing
- Check ws_broadcast_latency_seconds histogram and active websocket count.
- Check Redis CPU saturation and network jitter.
- Check backend process memory and GC pauses.
