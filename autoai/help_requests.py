from __future__ import annotations

import json
import uuid
from pathlib import Path
from typing import Any

from .db import ensure_db, get_session
from .models import HelpRequest, Message
from .time_utils import utc_now_iso


VALID_HELP_STATUSES = {"open", "answered", "closed"}
VALID_HELP_SEVERITIES = {"low", "medium", "high", "blocking"}


def list_help_requests(project_dir: Path) -> list[dict[str, Any]]:
    ensure_db(project_dir)
    with get_session() as session:
        items = session.query(HelpRequest).order_by(HelpRequest.created_at).all()
        return [item.to_dict() for item in items]


def open_help_requests(project_dir: Path) -> list[dict[str, Any]]:
    return [item for item in list_help_requests(project_dir) if item["status"] == "open"]


def create_help_request(
    project_dir: Path,
    title: str,
    detail: str = "",
    severity: str = "blocking",
    task_id: str = "",
    role_id: str = "",
    session_id: str = "",
) -> dict[str, Any]:
    title = title.strip()
    if not title:
        raise ValueError("Help request title is required.")
    _validate_severity(severity)
    ensure_db(project_dir)
    now = utc_now_iso()
    request = HelpRequest(
        id="H-" + uuid.uuid4().hex[:8],
        title=title,
        detail=detail.strip(),
        severity=severity,
        task_id=task_id.strip(),
        role_id=role_id.strip(),
        session_id=session_id.strip(),
        created_at=now,
        updated_at=now,
    )
    with get_session() as session:
        session.add(request)
        session.commit()
        payload = request.to_dict()
    append_message(project_dir, "help-request", "agent", "human", payload)
    return payload


def answer_help_request(project_dir: Path, request_id: str, answer: str) -> dict[str, Any]:
    answer = answer.strip()
    if not answer:
        raise ValueError("Answer is required.")
    ensure_db(project_dir)
    with get_session() as session:
        item = session.query(HelpRequest).filter(HelpRequest.id == request_id).first()
        if not item:
            raise ValueError(f"Help request not found: {request_id}")
        item.status = "answered"
        item.answer = answer
        item.updated_at = utc_now_iso()
        session.commit()
        payload = item.to_dict()
    append_message(project_dir, "human-answer", "human", payload.get("role_id") or "agent", payload)
    return payload


def close_help_request(project_dir: Path, request_id: str) -> dict[str, Any]:
    ensure_db(project_dir)
    with get_session() as session:
        item = session.query(HelpRequest).filter(HelpRequest.id == request_id).first()
        if not item:
            raise ValueError(f"Help request not found: {request_id}")
        item.status = "closed"
        item.updated_at = utc_now_iso()
        session.commit()
        payload = item.to_dict()
    append_message(project_dir, "help-closed", "human", payload.get("role_id") or "agent", payload)
    return payload


def append_message(
    project_dir: Path,
    message_type: str,
    sender: str,
    recipient: str,
    payload: dict[str, Any],
) -> None:
    ensure_db(project_dir)
    msg = Message(
        id="M-" + uuid.uuid4().hex[:10],
        time=utc_now_iso(),
        type=message_type,
        sender=sender,
        recipient=recipient,
        payload_json=json.dumps(payload, ensure_ascii=False),
    )
    with get_session() as session:
        session.add(msg)
        session.commit()


def help_context_summary(project_dir: Path, limit: int = 8) -> str:
    items = list_help_requests(project_dir)
    if not items:
        return (
            "No human help requests are recorded. If you are blocked by a permission, login, "
            "missing secret, external account action, ambiguity, or user decision, add an open "
            "request and stop."
        )

    open_items = [item for item in items if item["status"] == "open"]
    answered_items = [item for item in items if item["status"] == "answered"]
    lines = [
        "Human help protocol:",
        "- If you cannot proceed safely, create a help request with status `open`, then stop.",
        "- Do not guess secrets, credentials, account actions, legal/financial/medical choices, or risky approvals.",
        "- If a request below is answered, use the human answer and continue.",
        "",
    ]
    if open_items:
        lines.append("Open help requests waiting for the user:")
        for item in open_items[:limit]:
            lines.append(f"- {item['id']} [{item['severity']}] {item['title']}")
            if item["detail"]:
                lines.append(f"  Detail: {item['detail']}")
        lines.append("")
    if answered_items:
        lines.append("Answered help requests available for this session:")
        for item in answered_items[-limit:]:
            lines.append(f"- {item['id']} {item['title']}")
            lines.append(f"  Human answer: {item['answer']}")
    if not open_items and not answered_items:
        lines.append("Only closed help requests exist; no active human input is waiting.")
    return "\n".join(lines)


def _validate_severity(severity: str) -> None:
    if severity not in VALID_HELP_SEVERITIES:
        raise ValueError(f"Invalid help request severity: {severity}")
