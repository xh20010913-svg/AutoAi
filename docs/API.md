# AutoAi API Reference v1.0

Base URL: `http://localhost:18765/api/v1`

## Health

### GET /health

```
Response 200:
{
  "status": "ok"
}
```

---

## Projects

### GET /projects

List all projects.

```
Response 200:
{
  "projects": [
    {
      "id": "uuid",
      "name": "My Project",
      "description": "...",
      "created_at": "2026-05-04T00:00:00Z",
      "updated_at": "2026-05-04T00:00:00Z"
    }
  ],
  "total": 1
}
```

### POST /projects

Create a project.

```
Request:
{
  "name": "My Project",
  "description": "Project description"   // optional
}

Response 201:
{
  "id": "uuid",
  "name": "My Project",
  "description": "...",
  "created_at": "2026-05-04T00:00:00Z",
  "updated_at": "2026-05-04T00:00:00Z"
}
```

### GET /projects/:id

Get project details.

```
Response 200:
{
  "id": "uuid",
  "name": "My Project",
  "description": "...",
  "created_at": "...",
  "updated_at": "..."
}
```

### DELETE /projects/:id

Delete a project and all its data.

```
Response 204
```

---

## Agents

### GET /projects/:id/agents

List agents in a project.

```
Response 200:
{
  "agents": [
    {
      "id": "uuid",
      "name": "Backend Developer",
      "role": "backend",
      "model": "claude-sonnet-4-6",
      "provider_id": "uuid",
      "status": "idle",
      "system_prompt": "...",
      "created_at": "..."
    }
  ],
  "total": 1
}
```

### POST /projects/:id/agents

Create an agent.

```
Request:
{
  "name": "Backend Developer",
  "role": "backend",          // pm | backend | frontend | algorithm | tester
  "model": "claude-sonnet-4-6",
  "provider_id": "uuid",      // optional
  "system_prompt": "..."      // optional
}

Response 201: agent object
```

### PATCH /projects/:id/agents/:aid

Update an agent.

```
Request (all fields optional):
{
  "name": "...",
  "model": "...",
  "provider_id": "...",
  "system_prompt": "..."
}

Response 200: agent object
```

### DELETE /projects/:id/agents/:aid

Delete an agent.

```
Response 204
```

---

## Tasks

### GET /projects/:id/tasks

List tasks. Supports filtering.

```
Query params:
  status    — todo | in_progress | in_review | done | blocked
  priority  — high | medium | low | none
  assignee  — agent_id
  search    — text search in title/description
  limit     — default 50
  offset    — default 0

Response 200:
{
  "tasks": [
    {
      "id": "uuid",
      "title": "Build backend scaffold",
      "description": "...",
      "status": "in_progress",
      "priority": "high",
      "assignee_id": "uuid",
      "parent_id": null,
      "position": 0,
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "total": 1
}
```

### POST /projects/:id/tasks

Create a task.

```
Request:
{
  "title": "Task title",
  "description": "...",         // optional
  "priority": "medium",         // optional, default medium
  "assignee_id": "uuid",        // optional
  "parent_id": "uuid"           // optional, for subtasks
}

Response 201: task object
```

### PATCH /projects/:id/tasks/:tid

Update a task.

```
Request (all fields optional):
{
  "title": "...",
  "description": "...",
  "status": "in_progress",
  "priority": "high",
  "assignee_id": "uuid",
  "position": 2
}

Response 200: task object
```

### DELETE /projects/:id/tasks/:tid

Delete a task.

```
Response 204
```

---

## Run

### POST /projects/:id/run

Start an agent run.

```
Request:
{
  "agent_id": "uuid",
  "task_id": "uuid",    // optional
  "command": "claude -p 'implement feature X'",
  "max_iterations": 3
}

Response 202:
{
  "run_id": "uuid",
  "status": "starting"
}
```

### POST /projects/:id/run/stop

Stop the current running agent.

```
Response 200:
{
  "run_id": "uuid",
  "status": "stopping"
}
```

### GET /projects/:id/runs

List run history.

```
Query params:
  agent_id  — filter by agent
  limit     — default 20

Response 200:
{
  "runs": [
    {
      "id": "uuid",
      "agent_id": "uuid",
      "status": "completed",     // starting | running | completed | failed | stopped
      "started_at": "...",
      "finished_at": "...",
      "iteration_count": 3
    }
  ],
  "total": 1
}
```

### GET /projects/:id/runs/:rid

Get run detail with all events.

```
Response 200:
{
  "id": "uuid",
  "agent_id": "uuid",
  "status": "completed",
  "started_at": "...",
  "finished_at": "...",
  "events": [
    {
      "seq": 1,
      "type": "stdout",
      "data": "Installing dependencies...\n",
      "timestamp": "..."
    },
    {
      "seq": 2,
      "type": "stderr",
      "data": "Warning: deprecated package\n",
      "timestamp": "..."
    }
  ]
}
```

---

## Providers

### GET /projects/:id/providers

List model providers.

```
Response 200:
{
  "providers": [
    {
      "id": "uuid",
      "name": "Anthropic",
      "type": "anthropic",
      "base_url": "https://api.anthropic.com",
      "models": ["claude-sonnet-4-6", "claude-haiku-4-5"],
      "has_api_key": true,
      "created_at": "..."
    }
  ],
  "total": 1
}
```

### POST /projects/:id/providers

Add a provider.

```
Request:
{
  "name": "Anthropic",
  "type": "anthropic",          // anthropic | openai | deepseek | custom
  "base_url": "https://api.anthropic.com",
  "api_key": "sk-ant-...",
  "models": ["claude-sonnet-4-6"]
}

Response 201: provider object (api_key masked)
```

### PATCH /projects/:id/providers/:pid

Update a provider.

```
Request (all fields optional):
{
  "name": "...",
  "base_url": "...",
  "api_key": "...",
  "models": [...]
}

Response 200: provider object
```

### DELETE /projects/:id/providers/:pid

Delete a provider.

```
Response 204
```

---

## Sessions

### GET /projects/:id/sessions

List run sessions (grouped run history per agent).

```
Query params:
  agent_id  — filter by agent
  limit     — default 20

Response 200:
{
  "sessions": [
    {
      "id": "uuid",
      "agent_id": "uuid",
      "agent_name": "Backend Developer",
      "task_id": "uuid",
      "status": "completed",
      "run_count": 3,
      "started_at": "...",
      "finished_at": "..."
    }
  ],
  "total": 1
}
```

### GET /projects/:id/sessions/:sid

Get session detail with all run events.

```
Response 200:
{
  "id": "uuid",
  "agent_id": "uuid",
  "status": "completed",
  "runs": [
    {
      "id": "uuid",
      "status": "completed",
      "started_at": "...",
      "finished_at": "...",
      "events": [...]
    }
  ]
}
```

---

## WebSocket Events

Connect: `ws://localhost:18765/ws/:project_id`

### Server → Client

```
// Task events
{"type": "task_created",     "data": {...task}}
{"type": "task_updated",     "data": {...task}}
{"type": "task_deleted",     "data": {"id": "uuid"}}

// Agent events
{"type": "agent_status",     "data": {"agent_id": "uuid", "status": "running"}}

// Run events
{"type": "run_started",      "data": {"run_id": "uuid", "agent_id": "uuid"}}
{"type": "stdout",           "data": {"run_id": "uuid", "text": "..."}}
{"type": "stderr",           "data": {"run_id": "uuid", "text": "..."}}
{"type": "run_finished",     "data": {"run_id": "uuid", "status": "completed"}}
{"type": "run_error",        "data": {"run_id": "uuid", "error": "..."}}

// Connection
{"type": "connected",        "data": {"project_id": "uuid"}}
```

### Client → Server

```
// Subscribe to specific event types
{"type": "subscribe",   "events": ["stdout", "stderr", "task_updated"]}

// Ping/keepalive
{"type": "ping"}
```

## Error Responses

```
400 Bad Request:
{
  "error": "validation_error",
  "message": "title is required",
  "details": [{"field": "title", "issue": "missing"}]
}

404 Not Found:
{
  "error": "not_found",
  "message": "Project not found"
}

500 Internal Error:
{
  "error": "internal_error",
  "message": "Something went wrong"
}
```
