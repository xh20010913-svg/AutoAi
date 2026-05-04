"""
AutoAi Planner — 从 task_spec.md + feature_list.json 自动生成 task_graph.json

读取任务规格、功能列表和角色定义，输出带有角色推荐、
写入路径、依赖关系和验收标准的任务图。

用法:
    python -m autoai.planner [--project-dir DIR]
"""

import json
import re
from pathlib import Path

# ─── 路径常量 ──────────────────────────────────────────────────────────────────

DEFAULT_SPEC = "task_spec.md"
DEFAULT_FEATURES = "feature_list.json"
DEFAULT_ROLES = ".autoai/roles.json"
DEFAULT_OUTPUT = ".autoai/task_graph.json"


# ─── IO 工具 ───────────────────────────────────────────────────────────────────

def read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def read_json(path: Path) -> dict | list:
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


# ─── 规格解析 ──────────────────────────────────────────────────────────────────

def parse_spec_sections(spec_text: str) -> list[dict]:
    """将 markdown 规格按 ## 标题拆分为段落。"""
    sections = []
    current_title = None
    current_lines = []

    for line in spec_text.split("\n"):
        if line.startswith("## "):
            if current_title is not None:
                sections.append({
                    "title": current_title.strip(),
                    "body": "\n".join(current_lines).strip(),
                })
            current_title = line[3:].strip()
            current_lines = []
        else:
            current_lines.append(line)

    if current_title is not None:
        sections.append({
            "title": current_title.strip(),
            "body": "\n".join(current_lines).strip(),
        })

    return sections


def extract_requirements(spec_text: str) -> list[str]:
    """从规格文本中提取所有需求列表项 (- 或 * 开头)。"""
    requirements = []
    for line in spec_text.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            requirements.append(stripped[2:].strip())
    return requirements


def extract_acceptance_from_body(body: str) -> list[str]:
    """从任务描述中提取验收标准（列表项）。"""
    criteria = []
    for line in body.split("\n"):
        stripped = line.strip()
        if stripped.startswith("- ") or stripped.startswith("* "):
            criteria.append(stripped[2:].strip())
    return criteria


# ─── 角色匹配 ──────────────────────────────────────────────────────────────────

# 角色 → 关键词映射（用于推断 suggested_role）
ROLE_KEYWORDS: dict[str, list[str]] = {
    "backend-developer": ["api", "endpoint", "backend", "model", "database", "server", "fastapi", "sqlalchemy", "websocket", "auth", "route", "schema", "pydantic", "crud",
                          "后端", "接口", "数据库", "模型", "认证", "服务端"],
    "frontend-developer": ["frontend", "react", "component", "ui", "page", "tsx", "css", "tailwind", "style", "theme", "button", "form", "layout", "sidebar", "board", "electron", "i18n", "pixel",
                           "前端", "组件", "页面", "主题", "像素"],
    "tester": ["test", "spec", "testing", "coverage", "integration", "e2e", "unit test", "vitest", "pytest",
               "测试", "覆盖", "用例"],
    "algorithm-engineer": ["algorithm", "scheduler", "orchestrat", "planner", "dispatch", "prompt", "template", "harness", "logic", "strategy",
                           "算法", "调度", "规划", "拆分"],
    "project-manager": ["doc", "readme", "roadmap", "architecture", "changelog", "progress",
                        "文档", "架构", "进度"],
}

# 角色 → 默认写入路径
ROLE_WRITE_PATHS: dict[str, list[str]] = {
    "backend-developer": ["backend/app/", "backend/tests/", "backend/alembic/"],
    "frontend-developer": ["frontend/src/", "frontend/public/", "frontend/tests/"],
    "tester": ["backend/tests/", "frontend/tests/", "tests/"],
    "algorithm-engineer": ["autoai/", "scripts/"],
    "project-manager": ["docs/", "*.md"],
}

# 角色 → 精确写入路径（基于任务类型关键词）
SPECIFIC_PATHS: dict[str, list[str]] = {
    "api": ["backend/app/api/", "backend/app/schemas/"],
    "后端": ["backend/app/api/", "backend/app/schemas/"],
    "model": ["backend/app/models/"],
    "模型": ["backend/app/models/"],
    "auth": ["backend/app/auth.py", "backend/app/api/auth.py", "backend/app/schemas/auth.py"],
    "认证": ["backend/app/auth.py", "backend/app/api/auth.py", "backend/app/schemas/auth.py"],
    "database": ["backend/app/database.py", "backend/app/config.py"],
    "数据库": ["backend/app/database.py", "backend/app/config.py"],
    "websocket": ["backend/app/ws/", "backend/app/api/"],
    "component": ["frontend/src/components/"],
    "组件": ["frontend/src/components/"],
    "page": ["frontend/src/pages/"],
    "页面": ["frontend/src/pages/"],
    "style": ["frontend/src/index.css", "frontend/src/styles/"],
    "electron": ["frontend/electron/"],
    "测试": ["backend/tests/", "frontend/tests/"],
}


def suggest_role(title: str, description: str, roles: list[dict]) -> str:
    """根据任务标题和描述关键词推荐最匹配的角色。"""
    text = (title + " " + description).lower()
    title_lower = title.lower()
    scores: dict[str, int] = {}

    TITLE_WEIGHT = 3
    for role_name, keywords in ROLE_KEYWORDS.items():
        score = 0
        for kw in keywords:
            if kw in text:
                score += 1
            # 标题中出现的关键词权重更高
            if kw in title_lower:
                score += TITLE_WEIGHT
        if score > 0:
            scores[role_name] = score

    if not scores:
        return "backend-developer"

    best = max(scores, key=scores.get)

    # 验证推荐角色在 roles 列表中存在
    available = {r.get("name", "") for r in roles}
    if available and best not in available:
        # 回退：找一个在列表中存在的角色
        for fallback in ["backend-developer", "frontend-developer", "tester"]:
            if fallback in available:
                return fallback

    return best


def get_allowed_write_paths(role_name: str, title: str, description: str) -> list[str]:
    """根据角色和任务内容推断允许写入的路径。"""
    text = (title + " " + description).lower()
    paths = list(ROLE_WRITE_PATHS.get(role_name, []))

    # 基于任务类型精确化路径
    for kw, specific in SPECIFIC_PATHS.items():
        if kw in text:
            paths.extend(specific)

    # 去重并保持顺序
    seen = set()
    result = []
    for p in paths:
        if p not in seen:
            seen.add(p)
            result.append(p)

    return result


# ─── 依赖推断 ──────────────────────────────────────────────────────────────────

# 依赖类型 → 前置条件类型
DEPENDENCY_RULES: list[tuple[str, str]] = [
    # (任务类型关键词, 必须先完成的任务类型关键词)
    ("api", "model"),
    ("后端", "模型"),
    ("后端", "model"),
    ("frontend", "api"),
    ("前端", "api"),
    ("前端", "后端"),
    ("component", "api"),
    ("组件", "api"),
    ("page", "api"),
    ("页面", "api"),
    ("test", "api"),
    ("测试", "api"),
    ("测试", "后端"),
    ("test", "model"),
    ("测试", "模型"),
    ("integration", "api"),
    ("websocket", "model"),
    ("board", "api"),
]


def infer_dependencies(
    task: dict,
    all_tasks: list[dict],
) -> list[str]:
    """根据任务类型推断依赖关系。"""
    text = (task["title"] + " " + task["description"]).lower()
    deps = []

    for task_kw, dep_kw in DEPENDENCY_RULES:
        if task_kw not in text:
            continue
        for other in all_tasks:
            if other["id"] == task["id"]:
                continue
            other_text = (other["title"] + " " + other["description"]).lower()
            if dep_kw in other_text and other["id"] not in deps:
                deps.append(other["id"])

    return deps


# ─── 任务生成 ──────────────────────────────────────────────────────────────────

def make_task_id(feature_name: str) -> str:
    """将功能名称转换为合法的任务 ID。"""
    tid = re.sub(r"[^a-z0-9]+", "-", feature_name.lower()).strip("-")
    return tid or "task"


def generate_acceptance(title: str, description: str) -> list[str]:
    """根据任务标题和描述生成验收标准。"""
    text = (title + " " + description).lower()
    criteria: list[str] = []

    # 先尝试从描述中提取验收标准
    body_criteria = extract_acceptance_from_body(description)
    if body_criteria:
        return body_criteria

    # 基于任务类型生成验收标准
    if "api" in text or "endpoint" in text or "crud" in text:
        criteria.append("所有端点返回正确的状态码和响应格式")
        criteria.append("请求参数校验和错误处理完善")
    if "model" in text:
        criteria.append("数据库模型字段完整且类型正确")
        criteria.append("模型关系和约束正确定义")
    if "test" in text:
        criteria.append("测试覆盖主要功能路径和边界条件")
        criteria.append("所有测试用例通过")
    if "component" in text or "page" in text or "ui" in text:
        criteria.append("组件正确渲染且交互正常")
        criteria.append("支持主题切换和响应式布局")
    if "websocket" in text or "real-time" in text or "实时" in text:
        criteria.append("WebSocket 连接建立和断开正常")
        criteria.append("事件正确广播到所有连接的客户端")
    if "auth" in text or "login" in text or "认证" in text:
        criteria.append("认证流程完整且安全")
        criteria.append("未授权请求被正确拒绝")
    if "planner" in text or "调度" in text or "dispatch" in text:
        criteria.append("输入文件正确解析")
        criteria.append("输出 JSON 结构完整且有效")
    if "i18n" in text or "多语言" in text or "国际化" in text:
        criteria.append("中英文切换正常")
        criteria.append("语言选择持久化到 localStorage")

    # 通用验收标准
    if not criteria:
        criteria.append(f"{title} 功能按规格实现")
        criteria.append("代码遵循项目架构约定")

    return criteria


def _text_contains_any(text: str, keywords: list[str]) -> bool:
    """检查文本是否包含任意关键词（支持中文）。"""
    text_lower = text.lower()
    return any(kw.lower() in text_lower for kw in keywords)


def _section_covered_by_features(section_title: str, section_body: str, features: list[dict]) -> bool:
    """检查 spec 段落是否已被 feature_list 中的任务覆盖。"""
    title_lower = section_title.lower()
    body_lower = section_body.lower()[:100]
    section_text = title_lower + " " + body_lower

    # 将标题拆分为有意义的词（英文按空格拆，中文按2字词组切分）
    raw_words = re.split(r"[\s　,，/、()（）]+", title_lower)
    title_words = [w for w in raw_words if len(w) >= 2]

    # 对中文标题额外生成2字滑动窗口词组（如"前端组件"→["前端","组件","端组"]）
    expanded_words = list(title_words)
    for w in title_words:
        if any(c > '一' for c in w):  # 包含中文
            for i in range(len(w) - 1):
                expanded_words.append(w[i:i+2])
    title_words = expanded_words

    for feat in features:
        name = (feat.get("name", "") + " " + feat.get("title", "")).lower()
        desc = feat.get("description", "").lower()
        feat_text = name + " " + desc

        # 方法1：标题关键词出现在 feature 中
        if title_words:
            matches = sum(1 for w in title_words if w in feat_text)
            if matches >= 1:  # 有一个匹配就认为覆盖
                return True

        # 方法2：feature 关键词出现在 section 中
        feat_raw = re.split(r"[\s　,，/、()（）]+", name)
        feat_words = [w for w in feat_raw if len(w) >= 2]
        if feat_words:
            matches = sum(1 for w in feat_words if w in section_text)
            if matches >= 1:
                return True

    return False


def build_tasks(
    features: list[dict],
    spec_sections: list[dict],
    roles: list[dict],
) -> list[dict]:
    """从功能列表和规格段落生成任务列表。"""
    tasks = []

    # 从 feature_list.json 生成任务
    for feat in features:
        name = feat.get("name", feat.get("title", ""))
        if not name:
            continue

        desc = feat.get("description", "")
        tid = feat.get("id", make_task_id(name))
        role = suggest_role(name, desc, roles)
        paths = get_allowed_write_paths(role, name, desc)

        tasks.append({
            "id": tid,
            "title": name,
            "description": desc,
            "suggested_role": role,
            "allowed_write_paths": paths,
            "depends_on": [],  # 后续推断
            "acceptance": generate_acceptance(name, desc),
        })

    # 从 spec 段落生成额外任务（仅当 feature_list 中没有对应任务时）
    for section in spec_sections:
        title = section["title"]
        body = section["body"]
        if not body:
            continue
        # 跳过已经在 feature_list 中覆盖的段落
        if _section_covered_by_features(title, body, features):
            continue

        tid = make_task_id(title)
        role = suggest_role(title, body, roles)
        paths = get_allowed_write_paths(role, title, body)

        tasks.append({
            "id": tid,
            "title": title,
            "description": body[:200],
            "suggested_role": role,
            "allowed_write_paths": paths,
            "depends_on": [],
            "acceptance": generate_acceptance(title, body),
        })

    # 推断依赖关系
    for task in tasks:
        task["depends_on"] = infer_dependencies(task, tasks)

    return tasks


# ─── 主入口 ────────────────────────────────────────────────────────────────────

def validate_task_graph(graph: dict) -> list[str]:
    """验证 task_graph 结构的完整性，返回错误列表。"""
    errors = []
    if not isinstance(graph, dict):
        return ["task_graph must be a JSON object"]
    if "tasks" not in graph:
        return ["task_graph must have a 'tasks' key"]

    task_ids = {t["id"] for t in graph["tasks"]}

    for i, task in enumerate(graph["tasks"]):
        prefix = f"tasks[{i}]"
        for field in ("id", "title", "suggested_role", "allowed_write_paths", "depends_on", "acceptance"):
            if field not in task:
                errors.append(f"{prefix} missing required field '{field}'")
        if not isinstance(task.get("allowed_write_paths", []), list):
            errors.append(f"{prefix}.allowed_write_paths must be a list")
        if not isinstance(task.get("depends_on", []), list):
            errors.append(f"{prefix}.depends_on must be a list")
        if not isinstance(task.get("acceptance", []), list):
            errors.append(f"{prefix}.acceptance must be a list")
        for dep in task.get("depends_on", []):
            if dep not in task_ids:
                errors.append(f"{prefix}.depends_on references unknown task '{dep}'")

    return errors


def plan(
    spec_path: Path,
    features_path: Path,
    roles_path: Path,
    output_path: Path | None = None,
) -> dict:
    """
    从规格文件生成任务图。

    Args:
        spec_path: task_spec.md 路径
        features_path: feature_list.json 路径
        roles_path: .autoai/roles.json 路径
        output_path: 输出路径（None 则不写文件）

    Returns:
        task_graph 字典
    """
    spec_text = read_text(spec_path)
    features = read_json(features_path)
    roles_data = read_json(roles_path)

    # roles.json 可以是 {"roles": [...]} 或直接 [...]
    if isinstance(roles_data, dict):
        roles = roles_data.get("roles", [])
    else:
        roles = roles_data

    spec_sections = parse_spec_sections(spec_text)
    tasks = build_tasks(features, spec_sections, roles)

    graph = {
        "tasks": tasks,
        "generated_from": {
            "spec": str(spec_path),
            "features": str(features_path),
            "roles": str(roles_path),
        },
    }

    if output_path:
        write_json(output_path, graph)

    return graph


def main():
    import argparse

    parser = argparse.ArgumentParser(description="AutoAi Planner — 生成 task_graph.json")
    parser.add_argument("--project-dir", default=".", help="项目根目录")
    parser.add_argument("--spec", default=DEFAULT_SPEC, help="任务规格文件")
    parser.add_argument("--features", default=DEFAULT_FEATURES, help="功能列表文件")
    parser.add_argument("--roles", default=DEFAULT_ROLES, help="角色定义文件")
    parser.add_argument("--output", default=DEFAULT_OUTPUT, help="输出文件路径")
    args = parser.parse_args()

    project = Path(args.project_dir)
    graph = plan(
        spec_path=project / args.spec,
        features_path=project / args.features,
        roles_path=project / args.roles,
        output_path=project / args.output,
    )

    errors = validate_task_graph(graph)
    if errors:
        print(f"Validation warnings: {len(errors)}")
        for e in errors:
            print(f"  - {e}")
    else:
        print(f"Task graph valid: {len(graph['tasks'])} tasks generated")


if __name__ == "__main__":
    main()
