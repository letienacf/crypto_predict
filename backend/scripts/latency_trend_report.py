import json
from pathlib import Path


def build_markdown(rows: list[dict]) -> str:
    header = "| Timestamp | Samples | p50 (ms) | p95 (ms) | p99 (ms) |\n|---|---:|---:|---:|---:|"
    body = [
        f"| {row.get('timestamp', '-')} | {row.get('sample_size', 0)} | {row.get('p50_ms', 0)} | {row.get('p95_ms', 0)} | {row.get('p99_ms', 0)} |"
        for row in rows
    ]
    return "\n".join([header] + body)


def main() -> None:
    reports_dir = Path("reports/latency")
    report_files = sorted(reports_dir.glob("*.json"))
    rows: list[dict] = []

    for file_path in report_files:
        try:
            payload = json.loads(file_path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if isinstance(payload, dict):
            rows.append(payload)

    markdown = build_markdown(rows)
    output = reports_dir / "trend.md"
    output.write_text(markdown, encoding="utf-8")
    print(markdown)


if __name__ == "__main__":
    main()
