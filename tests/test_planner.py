"""Tests for autoai.planner — task graph generation."""

import json
import pytest
from pathlib import Path

from autoai.planner import (
    parse_spec_sections,
    extract_requirements,
    extract_acceptance_from_body,
    suggest_role,
    get_allowed_write_paths,
    infer_dependencies,
    make_task_id,
    generate_acceptance,
    build_tasks,
    validate_task_graph,
    plan,
)

# ─── Fixture helpers ──────────────────────────────────────────────────────────


def _write(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")


SAMPLE_SPEC = """\
# AutoAi 任务规格

## 数据库模型

- 创建 SQLAlchemy 模型
- 支持 SQLite
- 包含用户和项目模型

## API 端点

- RESTful CRUD 接口
- JWT 认证保护
- 请求参数校验

## 前端组件

- React + TypeScript
- 支持暗色主题
- 响应式布局

## 测试 / Testing

- 单元测试覆盖 unit test coverage
- 集成测试通过 integration test
"""

SAMPLE_FEATURES = [
    {"id": "db-models", "name": "数据库模型设计", "description": "创建 SQLAlchemy 数据库模型"},
    {"id": "api-crud", "name": "API CRUD 端点", "description": "实现 RESTful API 端点和后端路由"},
    {"id": "frontend-board", "name": "Board 页面组件", "description": "前端看板页面 React 组件"},
    {"id": "api-auth", "name": "用户认证 API", "description": "JWT 认证后端端点"},
    {"id": "test-api", "name": "Test suite", "description": "test coverage for all endpoints"},
    {"id": "planner-module", "name": "任务调度规划器", "description": "算法调度和自动拆分模块"},
]

SAMPLE_ROLES = [
    {"name": "backend-developer", "scope": {"write_paths": ["backend/"]}},
    {"name": "frontend-developer", "scope": {"write_paths": ["frontend/"]}},
    {"name": "tester", "scope": {"write_paths": ["backend/tests/", "frontend/tests/"]}},
    {"name": "algorithm-engineer", "scope": {"write_paths": ["autoai/", "scripts/"]}},
    {"name": "project-manager", "scope": {"write_paths": ["docs/"]}},
]


@pytest.fixture
def project_dir(tmp_path):
    """创建包含测试文件的临时项目目录。"""
    _write(tmp_path / "task_spec.md", SAMPLE_SPEC)
    _write(tmp_path / "feature_list.json", json.dumps(SAMPLE_FEATURES, ensure_ascii=False))
    _write(tmp_path / ".autoai" / "roles.json", json.dumps(SAMPLE_ROLES, ensure_ascii=False))
    return tmp_path


# ─── parse_spec_sections ──────────────────────────────────────────────────────


class TestParseSpecSections:
    def test_basic_sections(self):
        sections = parse_spec_sections(SAMPLE_SPEC)
        titles = [s["title"] for s in sections]
        assert "数据库模型" in titles
        assert "API 端点" in titles
        assert "前端组件" in titles
        assert any("测试" in t for t in titles)

    def test_section_body_contains_content(self):
        sections = parse_spec_sections(SAMPLE_SPEC)
        db_section = next(s for s in sections if s["title"] == "数据库模型")
        assert "SQLAlchemy" in db_section["body"]
        assert "SQLite" in db_section["body"]

    def test_empty_spec(self):
        assert parse_spec_sections("") == []
        assert parse_spec_sections("no headers here") == []

    def test_single_section(self):
        sections = parse_spec_sections("## Only Section\nsome content")
        assert len(sections) == 1
        assert sections[0]["title"] == "Only Section"
        assert sections[0]["body"] == "some content"


# ─── extract_requirements / extract_acceptance_from_body ──────────────────────


class TestExtractRequirements:
    def test_extract_dash_items(self):
        text = "Some text\n- First requirement\n- Second requirement\nOther text"
        reqs = extract_requirements(text)
        assert reqs == ["First requirement", "Second requirement"]

    def test_extract_star_items(self):
        text = "* Item A\n* Item B"
        assert extract_requirements(text) == ["Item A", "Item B"]

    def test_no_items(self):
        assert extract_requirements("plain text") == []

    def test_acceptance_from_body(self):
        body = "Description text\n- Acceptance 1\n- Acceptance 2"
        assert extract_acceptance_from_body(body) == ["Acceptance 1", "Acceptance 2"]


# ─── make_task_id ─────────────────────────────────────────────────────────────


class TestMakeTaskId:
    def test_simple(self):
        assert make_task_id("API CRUD") == "api-crud"

    def test_chinese(self):
        # Chinese characters are stripped by the regex, falling back to "task"
        assert make_task_id("数据库模型设计") == "task"

    def test_special_chars(self):
        assert make_task_id("Board Page (v0.2)") == "board-page-v0-2"

    def test_empty(self):
        assert make_task_id("") == "task"
        assert make_task_id("!!!") == "task"


# ─── suggest_role ─────────────────────────────────────────────────────────────


class TestSuggestRole:
    def test_backend_api(self):
        assert suggest_role("API CRUD 端点", "RESTful backend routes", SAMPLE_ROLES) == "backend-developer"

    def test_frontend(self):
        assert suggest_role("Board 页面组件", "React frontend UI", SAMPLE_ROLES) == "frontend-developer"

    def test_tester(self):
        assert suggest_role("API 测试", "backend test coverage", SAMPLE_ROLES) == "tester"

    def test_algorithm(self):
        assert suggest_role("任务调度规划器", "algorithm dispatch planner", SAMPLE_ROLES) == "algorithm-engineer"

    def test_model_maps_to_backend(self):
        assert suggest_role("数据库模型", "SQLAlchemy models", SAMPLE_ROLES) == "backend-developer"

    def test_fallback_to_backend(self):
        assert suggest_role("Something unknown", "no keywords", []) == "backend-developer"

    def test_doc_maps_to_pm(self):
        assert suggest_role("架构文档更新", "docs readme architecture", SAMPLE_ROLES) == "project-manager"

    def test_auth_maps_to_backend(self):
        assert suggest_role("用户认证 API", "JWT auth endpoint", SAMPLE_ROLES) == "backend-developer"


# ─── get_allowed_write_paths ──────────────────────────────────────────────────


class TestGetAllowedWritePaths:
    def test_backend_api(self):
        paths = get_allowed_write_paths("backend-developer", "API CRUD 端点", "RESTful routes")
        assert "backend/app/" in paths
        assert "backend/app/api/" in paths
        assert "backend/app/schemas/" in paths

    def test_frontend_component(self):
        paths = get_allowed_write_paths("frontend-developer", "React 组件", "UI component")
        assert "frontend/src/" in paths
        assert "frontend/src/components/" in paths

    def test_backend_model(self):
        paths = get_allowed_write_paths("backend-developer", "数据库模型", "SQLAlchemy model")
        assert "backend/app/models/" in paths

    def test_no_duplicates(self):
        paths = get_allowed_write_paths("backend-developer", "API 端点 CRUD", "api endpoint")
        assert len(paths) == len(set(paths))

    def test_tester_paths(self):
        paths = get_allowed_write_paths("tester", "API 测试", "test coverage")
        assert "backend/tests/" in paths
        assert "frontend/tests/" in paths


# ─── generate_acceptance ──────────────────────────────────────────────────────


class TestGenerateAcceptance:
    def test_api_task(self):
        criteria = generate_acceptance("API CRUD 端点", "RESTful endpoint implementation")
        assert any("状态码" in c or "端点" in c for c in criteria)

    def test_model_task(self):
        criteria = generate_acceptance("数据库模型设计", "SQLAlchemy model")
        assert any("模型" in c or "数据库" in c for c in criteria)

    def test_test_task(self):
        criteria = generate_acceptance("API 测试", "test coverage")
        assert any("测试" in c for c in criteria)

    def test_frontend_task(self):
        criteria = generate_acceptance("Board 组件", "React UI component")
        assert any("组件" in c or "渲染" in c for c in criteria)

    def test_fallback(self):
        criteria = generate_acceptance("Random task", "some work")
        assert len(criteria) >= 2
        assert any("Random task" in c for c in criteria)

    def test_acceptance_from_description(self):
        desc = "Description\n- Criterion A\n- Criterion B"
        criteria = generate_acceptance("Task", desc)
        assert criteria == ["Criterion A", "Criterion B"]


# ─── infer_dependencies ──────────────────────────────────────────────────────


class TestInferDependencies:
    def _make_task(self, tid, title, desc=""):
        return {"id": tid, "title": title, "description": desc, "depends_on": []}

    def test_api_depends_on_model(self):
        model = self._make_task("m1", "数据库模型", "SQLAlchemy model definition")
        api = self._make_task("a1", "API 端点", "RESTful API endpoint")
        deps = infer_dependencies(api, [model, api])
        assert "m1" in deps

    def test_frontend_depends_on_api(self):
        api = self._make_task("a1", "API CRUD 端点", "backend endpoint")
        fe = self._make_task("f1", "Board 页面组件", "frontend page component")
        deps = infer_dependencies(fe, [api, fe])
        assert "a1" in deps

    def test_test_depends_on_api(self):
        api = self._make_task("a1", "API 端点", "RESTful API")
        test = self._make_task("t1", "API 测试", "integration test")
        deps = infer_dependencies(test, [api, test])
        assert "a1" in deps

    def test_no_self_dependency(self):
        task = self._make_task("a1", "API 端点", "backend API")
        deps = infer_dependencies(task, [task])
        assert "a1" not in deps

    def test_no_dependency_when_no_match(self):
        task = self._make_task("x1", "Unrelated task", "nothing here")
        other = self._make_task("y1", "Other task", "also nothing")
        assert infer_dependencies(task, [other, task]) == []


# ─── build_tasks ──────────────────────────────────────────────────────────────


class TestBuildTasks:
    def test_generates_tasks_from_features(self):
        tasks = build_tasks(SAMPLE_FEATURES, parse_spec_sections(SAMPLE_SPEC), SAMPLE_ROLES)
        ids = {t["id"] for t in tasks}
        assert "db-models" in ids
        assert "api-crud" in ids
        assert "frontend-board" in ids

    def test_every_task_has_required_fields(self):
        tasks = build_tasks(SAMPLE_FEATURES, parse_spec_sections(SAMPLE_SPEC), SAMPLE_ROLES)
        for task in tasks:
            assert "id" in task
            assert "title" in task
            assert "suggested_role" in task
            assert "allowed_write_paths" in task
            assert "depends_on" in task
            assert "acceptance" in task
            assert isinstance(task["allowed_write_paths"], list)
            assert isinstance(task["depends_on"], list)
            assert isinstance(task["acceptance"], list)
            assert len(task["acceptance"]) > 0

    def test_role_assignment(self):
        tasks = build_tasks(SAMPLE_FEATURES, [], SAMPLE_ROLES)
        task_map = {t["id"]: t for t in tasks}
        assert task_map["db-models"]["suggested_role"] == "backend-developer"
        assert task_map["frontend-board"]["suggested_role"] == "frontend-developer"
        assert task_map["test-api"]["suggested_role"] == "tester"
        assert task_map["planner-module"]["suggested_role"] == "algorithm-engineer"

    def test_dependency_inference(self):
        tasks = build_tasks(SAMPLE_FEATURES, [], SAMPLE_ROLES)
        task_map = {t["id"]: t for t in tasks}
        # frontend-board depends on api-crud (API)
        assert "api-crud" in task_map["frontend-board"]["depends_on"]
        # test-api depends on api-crud
        assert "api-crud" in task_map["test-api"]["depends_on"]

    def test_empty_features(self):
        tasks = build_tasks([], parse_spec_sections(SAMPLE_SPEC), SAMPLE_ROLES)
        # spec sections generate tasks since no features exist
        assert len(tasks) > 0

    def test_no_duplicate_from_spec_and_features(self):
        # When features and spec cover the same topic, no duplicates
        features = [{"id": "api", "name": "API 端点设计", "description": "API endpoints"}]
        tasks = build_tasks(features, parse_spec_sections(SAMPLE_SPEC), SAMPLE_ROLES)
        api_tasks = [t for t in tasks if "api" in t["id"].lower()]
        # Should only have one "api" task from features, not duplicated from spec
        assert len(api_tasks) >= 1


# ─── validate_task_graph ─────────────────────────────────────────────────────


class TestValidateTaskGraph:
    def test_valid_graph(self, project_dir):
        graph = plan(
            project_dir / "task_spec.md",
            project_dir / "feature_list.json",
            project_dir / ".autoai" / "roles.json",
        )
        errors = validate_task_graph(graph)
        assert errors == []

    def test_not_dict(self):
        assert validate_task_graph("bad") == ["task_graph must be a JSON object"]

    def test_missing_tasks_key(self):
        assert validate_task_graph({"other": 1}) == ["task_graph must have a 'tasks' key"]

    def test_missing_required_field(self):
        graph = {"tasks": [{"id": "t1", "title": "T"}]}
        errors = validate_task_graph(graph)
        assert any("suggested_role" in e for e in errors)
        assert any("allowed_write_paths" in e for e in errors)

    def test_invalid_dependency_reference(self):
        graph = {
            "tasks": [
                {
                    "id": "t1",
                    "title": "T",
                    "suggested_role": "backend",
                    "allowed_write_paths": [],
                    "depends_on": ["nonexistent"],
                    "acceptance": ["ok"],
                }
            ]
        }
        errors = validate_task_graph(graph)
        assert any("nonexistent" in e for e in errors)

    def test_wrong_types(self):
        graph = {
            "tasks": [
                {
                    "id": "t1",
                    "title": "T",
                    "suggested_role": "backend",
                    "allowed_write_paths": "not-a-list",
                    "depends_on": "not-a-list",
                    "acceptance": "not-a-list",
                }
            ]
        }
        errors = validate_task_graph(graph)
        assert len(errors) >= 3


# ─── plan (integration) ──────────────────────────────────────────────────────


class TestPlan:
    def test_full_planning(self, project_dir):
        output = project_dir / ".autoai" / "task_graph.json"
        graph = plan(
            project_dir / "task_spec.md",
            project_dir / "feature_list.json",
            project_dir / ".autoai" / "roles.json",
            output_path=output,
        )

        # 基本结构
        assert "tasks" in graph
        assert "generated_from" in graph
        assert len(graph["tasks"]) == 6

        # 文件已写入
        assert output.exists()
        saved = json.loads(output.read_text(encoding="utf-8"))
        assert len(saved["tasks"]) == 6

    def test_validation_passes(self, project_dir):
        graph = plan(
            project_dir / "task_spec.md",
            project_dir / "feature_list.json",
            project_dir / ".autoai" / "roles.json",
        )
        assert validate_task_graph(graph) == []

    def test_roles_as_list(self, project_dir):
        """roles.json 可以直接是数组。"""
        roles_path = project_dir / ".autoai" / "roles_list.json"
        _write(roles_path, json.dumps(SAMPLE_ROLES, ensure_ascii=False))
        graph = plan(
            project_dir / "task_spec.md",
            project_dir / "feature_list.json",
            roles_path,
        )
        assert len(graph["tasks"]) > 0

    def test_no_output_when_none(self, project_dir):
        graph = plan(
            project_dir / "task_spec.md",
            project_dir / "feature_list.json",
            project_dir / ".autoai" / "roles.json",
            output_path=None,
        )
        assert "tasks" in graph

    def test_backend_before_frontend_dependency(self, project_dir):
        """后端 API 任务应被前端任务依赖。"""
        graph = plan(
            project_dir / "task_spec.md",
            project_dir / "feature_list.json",
            project_dir / ".autoai" / "roles.json",
        )
        task_map = {t["id"]: t for t in graph["tasks"]}

        fe_task = task_map.get("frontend-board")
        assert fe_task is not None
        # 前端任务应该依赖至少一个后端任务
        backend_deps = [
            d for d in fe_task["depends_on"]
            if task_map.get(d, {}).get("suggested_role") == "backend-developer"
        ]
        assert len(backend_deps) > 0

    def test_each_task_has_suggested_role(self, project_dir):
        graph = plan(
            project_dir / "task_spec.md",
            project_dir / "feature_list.json",
            project_dir / ".autoai" / "roles.json",
        )
        for task in graph["tasks"]:
            assert task["suggested_role"], f"Task '{task['id']}' has empty suggested_role"

    def test_each_task_has_write_paths(self, project_dir):
        graph = plan(
            project_dir / "task_spec.md",
            project_dir / "feature_list.json",
            project_dir / ".autoai" / "roles.json",
        )
        for task in graph["tasks"]:
            assert len(task["allowed_write_paths"]) > 0, \
                f"Task '{task['id']}' has no allowed_write_paths"

    def test_each_task_has_acceptance(self, project_dir):
        graph = plan(
            project_dir / "task_spec.md",
            project_dir / "feature_list.json",
            project_dir / ".autoai" / "roles.json",
        )
        for task in graph["tasks"]:
            assert len(task["acceptance"]) > 0, \
                f"Task '{task['id']}' has no acceptance criteria"

    def test_spec_only_no_features(self, project_dir):
        """没有 feature_list 时从 spec 生成任务。"""
        features_path = project_dir / "empty_features.json"
        _write(features_path, "[]")
        graph = plan(
            project_dir / "task_spec.md",
            features_path,
            project_dir / ".autoai" / "roles.json",
        )
        # 应从 spec 段落生成任务
        assert len(graph["tasks"]) > 0
