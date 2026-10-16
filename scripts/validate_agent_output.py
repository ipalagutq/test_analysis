"""Agent output validator.

Validates agent output against machine-readable schema contracts in
schemas/agent-output/. Checks required sections, size budget, target
file mentions, unknown markers, forbidden phrases and trailing text.

Usage:
    python scripts/validate_agent_output.py --agent code-mapper --input FILE \
        [--target-file PATH] [--target-file PATH] [--json]
"""

import argparse
import json
import re
import sys
from pathlib import Path

SCHEMAS_DIR = Path(__file__).resolve().parent.parent / "schemas" / "agent-output"

FORBIDDEN_PHRASES_DEFAULT = [
    "TODO", "TBD", "...", "etc.", "и т.д.", "to be filled",
]

HEADING_RE = re.compile(r"^#{1,4}\s+(.+)$", re.MULTILINE)


def load_schema(agent: str) -> dict:
    schema_path = SCHEMAS_DIR / f"{agent}.json"
    if not schema_path.is_file():
        raise FileNotFoundError(f"No schema for agent '{agent}': {schema_path}")
    return json.loads(schema_path.read_text(encoding="utf-8"))


def extract_sections(text: str) -> list[tuple[str, int]]:
    """Return [(section_title, line_index), ...] for markdown headings."""
    results = []
    for i, line in enumerate(text.splitlines()):
        m = re.match(r"^#{1,4}\s+(.+)$", line)
        if m:
            results.append((m.group(1).strip(), i))
    return results


def validate_output(text: str, schema: dict, target_files: list[str] | None = None) -> list[dict]:
    findings = []

    # Required sections
    required = schema["required_sections"]
    sections = extract_sections(text)
    section_titles = [s[0] for s in sections]

    found_required = []
    for req in required:
        if req not in section_titles:
            findings.append({
                "level": "FAIL",
                "code": "MISSING_SECTION",
                "message": f"Missing required section: '{req}'",
            })
        else:
            found_required.append(req)

    # Section order
    if len(found_required) == len(required):
        order_in_doc = [s for s in section_titles if s in required]
        if order_in_doc != required:
            findings.append({
                "level": "FAIL",
                "code": "SECTION_ORDER",
                "message": f"Sections out of order: expected {required}, got {order_in_doc}",
            })

    # Size budget
    max_chars = schema.get("max_chars")
    if max_chars and len(text) > max_chars:
        findings.append({
            "level": "FAIL",
            "code": "OVER_BUDGET",
            "message": f"Output exceeds max_chars: {len(text)} > {max_chars}",
        })

    # Forbidden phrases
    forbidden = schema.get("forbidden_phrases", FORBIDDEN_PHRASES_DEFAULT)
    for phrase in forbidden:
        if phrase in text:
            findings.append({
                "level": "FAIL",
                "code": "FORBIDDEN_PHRASE",
                "message": f"Contains forbidden phrase: '{phrase}'",
            })

    # Target file mentions
    if schema.get("target_files_required") and target_files:
        allowed_markers = schema.get("allowed_unknown_markers", [])
        for tf in target_files:
            if tf not in text:
                marker_found = False
                for marker in allowed_markers:
                    if f"{marker}: {tf}" in text or f"{marker}: {Path(tf).name}" in text:
                        marker_found = True
                        break
                if not marker_found:
                    findings.append({
                        "level": "FAIL",
                        "code": "MISSING_TARGET_FILE",
                        "message": f"Target file not mentioned and no valid unknown marker: '{tf}'",
                    })

    # Invalid unknown markers
    allowed_markers = schema.get("allowed_unknown_markers", [])
    unknown_marker_re = re.compile(r"\b(NOT_FOUND|CHAIN_BREAK|INSUFFICIENT_CONTEXT)\b")
    for match in unknown_marker_re.finditer(text):
        marker = match.group(1)
        if marker not in allowed_markers:
            findings.append({
                "level": "FAIL",
                "code": "INVALID_UNKNOWN_MARKER",
                "message": f"Disallowed unknown marker: '{marker}'",
            })

    # Unstructured trailing text
    if schema.get("no_unstructured_trailing_text"):
        lines = text.rstrip().splitlines()
        # Find last heading line
        last_heading_idx = -1
        for i in range(len(lines) - 1, -1, -1):
            if re.match(r"^#{1,4}\s+", lines[i]):
                last_heading_idx = i
                break
        if last_heading_idx >= 0:
            after_heading = lines[last_heading_idx + 1:]
            # Check for paragraph text (non-empty, non-table, non-list, non-heading)
            trailing_text_lines = []
            in_content = False
            for line in after_heading:
                stripped = line.strip()
                if not stripped:
                    if in_content:
                        trailing_text_lines.append(line)
                    continue
                if stripped.startswith("|") or stripped.startswith("- ") or stripped.startswith("#"):
                    in_content = True
                    continue
                in_content = True
                # This is a text line — check if it's a table/list or plain paragraph
                if not stripped.startswith("|") and not stripped.startswith("- "):
                    trailing_text_lines.append(stripped)

            # Filter out section content (tables, lists are already excluded)
            # Remaining lines are plain paragraph text after the last section
            paragraph_lines = []
            for line in trailing_text_lines:
                # Skip lines that are part of structured content
                if re.match(r"^(Step \d+:|Reference file:|File:|Reason:|Similarity:)", line):
                    continue
                paragraph_lines.append(line)

            if paragraph_lines:
                findings.append({
                    "level": "FAIL",
                    "code": "UNSTRUCTURED_TRAILING_TEXT",
                    "message": f"Unstructured text after last section: '{paragraph_lines[0][:80]}'",
                })

    return findings


def main() -> None:
    parser = argparse.ArgumentParser(description="Agent output validator")
    parser.add_argument("--agent", required=True, help="Agent name (e.g. code-mapper)")
    parser.add_argument("--input", required=True, type=Path, help="Path to agent output file")
    parser.add_argument("--target-file", action="append", default=[], help="Expected target file path (repeatable)")
    parser.add_argument("--json", action="store_true", help="Output as JSON")
    args = parser.parse_args()

    # Load schema
    try:
        schema = load_schema(args.agent)
    except FileNotFoundError as e:
        print(f"FAIL: {e}")
        sys.exit(2)
    except json.JSONDecodeError as e:
        print(f"FAIL: Malformed schema: {e}")
        sys.exit(2)

    # Load input
    input_path: Path = args.input
    if not input_path.is_file():
        print(f"FAIL: Input file not found: {input_path}")
        sys.exit(2)

    text = input_path.read_text(encoding="utf-8")

    # Validate
    findings = validate_output(text, schema, args.target_file or None)

    status = "FAIL" if any(f["level"] == "FAIL" for f in findings) else "OK"

    if args.json:
        output = {
            "status": status,
            "agent": args.agent,
            "findings": findings,
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))
    else:
        if not findings:
            print(f"OK: Agent '{args.agent}' output is valid.")
        else:
            fails = [f for f in findings if f["level"] == "FAIL"]
            warns = [f for f in findings if f["level"] == "WARN"]
            if fails:
                print(f"FAIL: {len(fails)} issue(s)")
                for f in fails:
                    print(f"  [{f['code']}] {f['message']}")
            if warns:
                print(f"WARN: {len(warns)} issue(s)")
                for f in warns:
                    print(f"  [{f['code']}] {f['message']}")

    sys.exit(1 if status == "FAIL" else 0)


if __name__ == "__main__":
    main()
