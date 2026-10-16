"""Workflow state validator.

Determines the current workflow state from git branch, spec file, and
stage markers. Reports whether a requested skill is allowed, what the
next expected skill is, and any blocking issues or warnings.

The validator checks declared (observable) workflow state — not whether
tests were actually run or code was actually written.

Usage:
    python scripts/validate_workflow_state.py --step implement-spec-stage [--json] [--repo DIR]
    python scripts/validate_workflow_state.py --help
"""

import argparse
import json
import re
import subprocess
import sys
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path

# ── Route ──────────────────────────────────────────────────────────

class Route(str, Enum):
    MAIN = "main"
    SPEC = "spec"
    SMALL_FIX = "small_fix"
    UNKNOWN = "unknown"


def detect_route(branch: str) -> Route:
    """Determine route from current branch name."""
    if branch in ("main", "master"):
        return Route.MAIN
    if branch.startswith("feature/") or branch.startswith("bugfix/"):
        return Route.SPEC
    if branch.startswith("fix/"):
        return Route.SMALL_FIX
    return Route.UNKNOWN


# ── Spec resolution ────────────────────────────────────────────────

def branch_to_spec_filename(branch: str) -> str:
    """Convert branch name to expected spec filename.

    ``feature/v0.6.0-workflow-state-validation`` →
    ``feature-v0.6.0-workflow-state-validation.md``
    """
    return branch.replace("/", "-") + ".md"


def find_spec(repo: Path, branch: str) -> Path | None:
    """Find spec file matching the current branch."""
    filename = branch_to_spec_filename(branch)
    spec_path = repo / ".ai" / "specs" / filename
    return spec_path if spec_path.is_file() else None


# ── Version extraction ─────────────────────────────────────────────

def extract_version_from_branch(branch: str) -> str | None:
    """Extract SemVer version from branch name.

    ``feature/v0.6.0-workflow-state-validation`` → ``0.6.0``
    """
    m = re.search(r"v(\d+\.\d+\.\d+)", branch)
    return m.group(1) if m else None


def extract_version_from_h1(spec_text: str) -> str | None:
    """Extract version from first H1 heading.

    ``# Workflow State Validation — Specification (v0.6.0)`` → ``0.6.0``
    """
    for line in spec_text.splitlines():
        if line.startswith("# "):
            m = re.search(r"v(\d+\.\d+\.\d+)", line)
            return m.group(1) if m else None
    return None


def extract_branch_metadata(spec_text: str) -> str | None:
    """Extract branch name from spec metadata line.

    ``> **Ветка:** `feature/v0.6.0-workflow-state-validation``` → branch name
    """
    m = re.search(r"\*\*Ветка:\*\*\s*`([^`]+)`", spec_text)
    return m.group(1) if m else None


# ── Emoji contract ─────────────────────────────────────────────────

EMOJI_DONE = "✅"     # ✅
EMOJI_TODO = "⬜"     # ⬜
EMOJI_ACTIVE = "\U0001F504"  # 🔄

VALID_EMOJI_STATUSES = {EMOJI_DONE, EMOJI_TODO, EMOJI_ACTIVE}


def parse_workflow_table(spec_text: str) -> dict[str, str]:
    """Parse workflow execution table from spec.

    Returns mapping of skill name to emoji status.
    Only accepts strict emoji format.
    """
    table: dict[str, str] = {}
    in_workflow = False
    for line in spec_text.splitlines():
        if "## Workflow выполнения" in line or "## Workflow" in line:
            in_workflow = True
            continue
        if in_workflow and line.startswith("## "):
            break
        if not in_workflow:
            continue
        # Parse table row: | а | ... | spec-creation | ✅ |
        cells = [c.strip() for c in line.strip("|").split("|")]
        if len(cells) >= 4:
            status_cell = cells[-1].strip()
            # Find skill name in one of the cells
            skill = None
            for cell in cells:
                for known in ("plan-release", "implement-spec-stage", "write-tests",
                              "integrate-release", "deploy-release"):
                    if known in cell:
                        skill = known
                        break
                if skill:
                    break
            if skill and status_cell in VALID_EMOJI_STATUSES:
                table[skill] = status_cell
    return table


def parse_stages(spec_text: str) -> list[dict]:
    """Parse implementation stages from spec.

    Returns list of {"index": int, "title": str, "status": str}.
    Status is one of the emoji constants or the raw text if non-standard.
    """
    stages: list[dict] = []
    in_stages = False
    stage_idx = 0
    for line in spec_text.splitlines():
        if "## Этапы реализации" in line:
            in_stages = True
            continue
        if in_stages and line.startswith("## "):
            break
        if not in_stages:
            continue
        # Match: ### ⬜ Этап 1: Title or ### 🔄 Этап 1: Title or ### ✅ Этап 1: Title
        m = re.match(r"^### (\S+)\s+Этап\s+(\d+):\s*(.+)$", line)
        if m:
            emoji = m.group(1)
            num = int(m.group(2))
            title = m.group(3).strip()
            if emoji not in VALID_EMOJI_STATUSES:
                # Non-standard status
                stages.append({"index": num, "title": title, "status": emoji, "valid": False})
            else:
                stages.append({"index": num, "title": title, "status": emoji, "valid": True})
            stage_idx += 1
    return stages


# ── Working tree ───────────────────────────────────────────────────

def is_dirty_tree(repo: Path) -> bool:
    """Check if working tree has uncommitted changes."""
    try:
        result = subprocess.run(
            ["git", "status", "--porcelain"],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return bool(result.stdout.strip())
    except (subprocess.SubprocessError, FileNotFoundError):
        return False


def get_current_branch(repo: Path) -> str:
    """Get current git branch name."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--abbrev-ref", "HEAD"],
            cwd=repo,
            capture_output=True,
            text=True,
            encoding="utf-8",
        )
        return result.stdout.strip()
    except (subprocess.SubprocessError, FileNotFoundError):
        return ""


# ── Issue / Warning helpers ────────────────────────────────────────

@dataclass
class Finding:
    code: str
    message: str


# ── Workflow state model ───────────────────────────────────────────

@dataclass
class WorkflowState:
    """Full workflow state as determined by the validator."""

    ok: bool = True
    route: str = "unknown"
    step: str | None = None
    branch: str = ""
    spec_path: str | None = None
    version: str | None = None
    current_stage: str | None = None
    allowed_current_skill: str | None = None
    expected_next_skill_after_exit: str | None = None
    issues: list[Finding] = field(default_factory=list)
    warnings: list[Finding] = field(default_factory=list)

    def add_issue(self, code: str, message: str) -> None:
        self.issues.append(Finding(code=code, message=message))
        self.ok = False

    def add_warning(self, code: str, message: str) -> None:
        self.warnings.append(Finding(code=code, message=message))

    def to_dict(self) -> dict:
        return {
            "ok": self.ok,
            "route": self.route,
            "step": self.step,
            "branch": self.branch,
            "spec_path": self.spec_path,
            "version": self.version,
            "current_stage": self.current_stage,
            "allowed_current_skill": self.allowed_current_skill,
            "expected_next_skill_after_exit": self.expected_next_skill_after_exit,
            "issues": [{"code": f.code, "message": f.message} for f in self.issues],
            "warnings": [{"code": f.code, "message": f.message} for f in self.warnings],
        }


# ── Pipeline order ─────────────────────────────────────────────────

PIPELINE = ["implement-spec-stage", "write-tests", "integrate-release", "deploy-release"]


def next_skill_in_pipeline(current: str) -> str | None:
    """Return the next skill after current, or None if ambiguous/end."""
    try:
        idx = PIPELINE.index(current)
    except ValueError:
        return None
    if idx + 1 < len(PIPELINE):
        return PIPELINE[idx + 1]
    return None


# ── Format helpers ─────────────────────────────────────────────────

def format_text_report(state: WorkflowState) -> str:
    """Format human-readable report."""
    lines = []
    status = "OK" if state.ok else "FAIL"
    lines.append(f"{status}: route={state.route} branch={state.branch}")
    if state.spec_path:
        lines.append(f"  spec: {state.spec_path}")
    if state.version:
        lines.append(f"  version: {state.version}")
    if state.current_stage:
        lines.append(f"  current_stage: {state.current_stage}")
    if state.step:
        allowed = "YES" if state.allowed_current_skill else "NO"
        lines.append(f"  step={state.step} allowed={allowed}")
    if state.expected_next_skill_after_exit:
        lines.append(f"  next: {state.expected_next_skill_after_exit}")
    for issue in state.issues:
        lines.append(f"  ISSUE [{issue.code}]: {issue.message}")
    for warning in state.warnings:
        lines.append(f"  WARN [{warning.code}]: {warning.message}")
    # integrate-release: declared vs evidence note
    if state.step == "integrate-release" and state.ok:
        lines.append("  NOTE: write-tests=✅ is declared state, not proof of actual test run.")
    return "\n".join(lines)


# ── CLI ────────────────────────────────────────────────────────────

VALID_STEPS = {"implement-spec-stage", "write-tests", "integrate-release", "deploy-release"}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Workflow state validator. "
                    "Checks declared workflow state and reports whether "
                    "the requested skill is allowed.",
    )
    parser.add_argument(
        "--step",
        choices=sorted(VALID_STEPS),
        help="Workflow skill to validate ENTRY conditions for.",
    )
    parser.add_argument(
        "--repo",
        type=Path,
        default=None,
        help="Path to repository root. Defaults to parent of scripts/.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        dest="json_output",
        help="Output as JSON.",
    )
    return parser


def main() -> None:
    parser = build_parser()
    args = parser.parse_args()

    repo = args.repo or Path(__file__).resolve().parent.parent

    if not repo.is_dir():
        print("Error: --repo path does not exist", file=sys.stderr)
        sys.exit(2)

    state = WorkflowState(step=args.step)

    # ── Branch & route ──
    state.branch = get_current_branch(repo)
    state.route = detect_route(state.branch).value

    # ── Route-level gate ──
    if state.route == "unknown" and args.step:
        state.add_issue("UNKNOWN_ROUTE", f"Branch '{state.branch}' does not match any known route.")
        _output(state, args.json_output)
        sys.exit(1)

    # ── Spec ──
    spec_file = find_spec(repo, state.branch)
    if spec_file:
        state.spec_path = spec_file.relative_to(repo).as_posix()
        spec_text = spec_file.read_text(encoding="utf-8")

        # Version
        state.version = extract_version_from_branch(state.branch)

        # Branch metadata consistency
        meta_branch = extract_branch_metadata(spec_text)
        if meta_branch and meta_branch != state.branch:
            state.add_issue(
                "BRANCH_MISMATCH",
                f"Spec says branch '{meta_branch}' but current branch is '{state.branch}'.",
            )

        # Version consistency
        h1_version = extract_version_from_h1(spec_text)
        branch_version = extract_version_from_branch(state.branch)
        if h1_version and branch_version and h1_version != branch_version:
            state.add_issue(
                "VERSION_MISMATCH",
                f"Branch version '{branch_version}' differs from H1 version '{h1_version}'.",
            )

        # Stages
        stages = parse_stages(spec_text)
        active = [s for s in stages if s["status"] == EMOJI_ACTIVE]
        todo = [s for s in stages if s["status"] == EMOJI_TODO]

        # Non-standard statuses
        invalid = [s for s in stages if not s.get("valid", True)]
        for s in invalid:
            state.add_issue(
                "INVALID_STAGE_FORMAT",
                f"Stage {s['index']}: non-standard status '{s['status']}'. "
                f"Expected one of: ✅ ⬜ 🔄",
            )

        # Multiple active stages
        if len(active) > 1:
            state.add_issue(
                "MULTIPLE_ACTIVE_STAGES",
                f"Found {len(active)} active (🔄) stages. Exactly one is allowed.",
            )

        # Current stage
        if active:
            current = active[0]
            state.current_stage = f"Этап {current['index']}: {current['title']}"
        elif todo:
            current = todo[0]
            state.current_stage = f"Этап {current['index']}: {current['title']}"
        else:
            state.current_stage = None  # all done

        # Workflow table
        wf_table = parse_workflow_table(spec_text)

        # ── Step-specific checks ──
        if args.step:
            dirty = is_dirty_tree(repo)

            if args.step == "implement-spec-stage":
                if not todo and not active:
                    state.add_issue("NO_AVAILABLE_STAGES", "No ⬜ or 🔄 stages available.")
                if dirty:
                    state.add_warning("DIRTY_TREE", "Working tree has uncommitted changes.")

            elif args.step == "write-tests":
                if stages and any(s["status"] != EMOJI_DONE for s in stages):
                    state.add_issue("INCOMPLETE_STAGES", "Not all implementation stages are ✅.")
                if dirty:
                    state.add_warning("DIRTY_TREE", "Working tree has uncommitted changes.")

            elif args.step == "integrate-release":
                if state.route == "main":
                    state.add_issue("ON_MAIN", "integrate-release must not run on main/master.")
                if dirty:
                    state.add_issue("DIRTY_TREE", "Working tree must be clean for merge.")
                tw_status = wf_table.get("write-tests")
                if tw_status != EMOJI_DONE:
                    state.add_issue(
                        "TEST_WRITER_NOT_DONE",
                        f"write-tests status is '{tw_status}', expected ✅.",
                    )
                else:
                    state.add_warning(
                        "TEST_EVIDENCE_DECLARED",
                        "write-tests=✅ is declared state; actual test execution "
                        "is the responsibility of integrate-release.",
                    )

            elif args.step == "deploy-release":
                if state.route != "main":
                    state.add_issue("NOT_ON_MAIN", f"deploy-release requires route 'main', got '{state.route}'.")
                if dirty:
                    state.add_issue("DIRTY_TREE", "Working tree must be clean for deploy.")

            # Determine allowed_current_skill
            state.allowed_current_skill = args.step if state.ok else None
            state.expected_next_skill_after_exit = next_skill_in_pipeline(args.step) if state.ok else None

    elif state.route == "main" and args.step == "deploy-release":
        # No spec on main after merge; route is main by construction, so only DIRTY_TREE applies
        if is_dirty_tree(repo):
            state.add_issue("DIRTY_TREE", "Working tree must be clean for deploy.")
        if state.ok:
            state.allowed_current_skill = args.step
            state.expected_next_skill_after_exit = next_skill_in_pipeline(args.step)

    elif state.route in ("spec",) and args.step:
        state.add_issue("MISSING_SPEC", f"No spec found for branch '{state.branch}'.")
        state.allowed_current_skill = None
    elif state.route == "small_fix" and args.step in ("implement-spec-stage", "write-tests"):
        state.add_issue("SMALL_FIX_NO_SPEC", f"Step '{args.step}' requires a spec; small-fix route has none.")

    _output(state, args.json_output)
    sys.exit(0 if state.ok else 1)


def _output(state: WorkflowState, as_json: bool) -> None:
    if as_json:
        print(json.dumps(state.to_dict(), indent=2, ensure_ascii=False))
    else:
        print(format_text_report(state))


if __name__ == "__main__":
    main()
