import json
import csv
from pathlib import Path
from io import StringIO


def _flatten_dict(data: dict, parent_key: str = "", sep: str = "_") -> dict:
    items = {}

    for key, value in data.items():
        new_key = f"{parent_key}{sep}{key}" if parent_key else key

        if isinstance(value, dict):
            items.update(_flatten_dict(value, new_key, sep=sep))
        else:
            items[new_key] = value

    return items


def format_normal(results: list[dict]) -> str:
    blocks = []

    for entry in results:
        lines = []
        for key, value in entry.items():
            if isinstance(value, dict):
                lines.append(f"{key}:")
                for sub_key, sub_val in value.items():
                    lines.append(f"  {sub_key}: {sub_val}")
            else:
                lines.append(f"{key}: {value}")

        blocks.append("\n".join(lines))
        blocks.append("-" * 40)

    return "\n".join(blocks)


def format_json(results: list[dict]) -> str:
    return json.dumps(results, indent=4)


def format_csv(results: list[dict]) -> str:
    if not results:
        return ""

    flattened = [_flatten_dict(r) for r in results]

    fieldnames = sorted(
        {key for entry in flattened for key in entry.keys()}
    )

    buffer = StringIO()
    writer = csv.DictWriter(buffer, fieldnames=fieldnames)
    writer.writeheader()

    for entry in flattened:
        writer.writerow(entry)

    return buffer.getvalue()


def write_output(
    results: list[dict],
    path: str | Path,
    fmt: str = "normal",
) -> Path:
    fmt = fmt.lower()
    path = Path(path).resolve()

    if fmt == "json":
        content = format_json(results)
    elif fmt == "csv":
        content = format_csv(results)
    else:
        content = format_normal(results)

    path.write_text(content, encoding="utf-8")
    return path
