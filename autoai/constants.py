from pathlib import Path


CONTROL_DIR = ".autoai"
SESSION_DIR = "sessions"
CONFIG_FILE = "config.json"
STATE_FILE = "run_state.json"
FEATURE_BASELINE_FILE = "feature_list.baseline.json"
SPEC_FILE = "task_spec.md"
FEATURE_FILE = "feature_list.json"
PROGRESS_FILE = "autoai-progress.md"
VERIFICATION_DIR = "verification"
CLAUDE_DIR = ".claude"
CLAUDE_AGENTS_DIR = "agents"


def control_dir(project_dir: Path) -> Path:
    return project_dir / CONTROL_DIR


def session_dir(project_dir: Path) -> Path:
    return control_dir(project_dir) / SESSION_DIR


def config_file(project_dir: Path) -> Path:
    return control_dir(project_dir) / CONFIG_FILE


def state_file(project_dir: Path) -> Path:
    return control_dir(project_dir) / STATE_FILE


def feature_baseline_file(project_dir: Path) -> Path:
    return control_dir(project_dir) / FEATURE_BASELINE_FILE


def claude_agents_dir(project_dir: Path) -> Path:
    return project_dir / CLAUDE_DIR / CLAUDE_AGENTS_DIR
