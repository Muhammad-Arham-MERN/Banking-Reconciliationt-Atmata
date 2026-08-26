# بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
"""
Nanonets Agents Platform - API integration reference.

Implements the exact flows from the official docs:

  * Run an agent:     https://agents.nanonets.com/docs/api-reference/agents/run-agent
  * Get task status:  https://agents.nanonets.com/docs/api-reference/tasks/get-task-status
  * Get task result:  https://agents.nanonets.com/docs/api-reference/tasks/get-task-result
  * Get task summary: https://agents.nanonets.com/docs/api-reference/tasks/get-task-summary
  * Sync extraction:  https://agents.nanonets.com/docs/api-reference/document-extraction/synchronous-extraction

A typical agent run is three calls:
  1. POST /api/v1/agents/{agent_id}/run          -> returns a task_id immediately
  2. Poll GET  /api/v1/tasks/{task_id}            until status is terminal
     (completed | failed | stopped), or reaches waiting_for_input
  3. GET  /api/v1/tasks/{task_id}/summary         -> final answer
     GET  /api/v1/tasks/{task_id}/result          -> full reasoning trace

Every API request is authenticated with a workspace API key as a Bearer token:
    Authorization: Bearer YOUR_API_KEY
Workspace API keys are minted from the web app under Settings -> API Keys.
Each key is scoped to a single workspace (requests for other workspaces -> 403).

Run:  uv run python tests/nanonets_agents_api.py
"""

import os
import time

import requests
from dotenv import load_dotenv

load_dotenv()

BASE_URL = "https://agents.nanonets.com"
EXTRACTION_URL = "https://extraction-api.nanonets.com"

# ---------------------------------------------------------------------------
# REQUIRED credentials/IDs - supply these (env vars or by editing below):
# ---------------------------------------------------------------------------
# 1. NANONETS_AGENTS_API_KEY - workspace API key (Settings -> API Keys)
API_KEY = os.getenv("NANONETS_AGENTS_API_KEY", "nn6aaeda7e1c5a5c3ea5b83d8656158e630a2f766499152935910887e57ea988dd")

# 2. AGENT_ID - UUID of the agent to run (Dashboard -> your agent -> URL/API tab)
AGENT_ID = os.getenv("NANONETS_AGENT_ID", "b4ad9686-e20a-4eb4-b7d0-618eff3fec89")

# 3. Optionally: a file to attach (PDF/Excel/image). The docs send it as
#    multipart form field "files.items" (or "file" for a single upload).
FILE_PATH = os.getenv("NANONETS_FILE", "../assets_dev/getjobid4620060.pdf")

# 4. Optionally: a saved extraction config URI ("config://<uuid>") for the
#    sync extraction endpoint.
CONFIG_ID = os.getenv("NANONETS_CONFIG_ID", "")


def _headers() -> dict:
    if not API_KEY:
        raise SystemExit("NANONETS_AGENTS_API_KEY is not set.")
    return {"Authorization": f"Bearer {API_KEY}"}


# ---------------------------------------------------------------------------
# Agent path (task-based, async)
# ---------------------------------------------------------------------------
def run_agent(
    query: str,
    file_path: str = "",
    output_config: str = "",
    version: int | None = None,
    source: str = "production",
) -> dict:
    """POST /api/v1/agents/{agent_id}/run

    Creates a task for the agent. Returns {task_id, agent_id, status, ...}.

    Args:
        query: Prompt text. Optional when one or more files are attached.
        file_path: Local file to attach (PDF, image, Word, Excel, ...).
        output_config: JSON-encoded TaskOutputConfig (output_schema/instructions).
        version: Optional published version number to run.
        source: "production" (default) or "test".
    """
    if not AGENT_ID:
        raise SystemExit("NANONETS_AGENT_ID is not set.")

    url = f"{BASE_URL}/api/v1/agents/{AGENT_ID}/run"
    payload = {"query": query}
    if output_config:
        payload["output_config"] = output_config
    if version is not None:
        payload["version"] = version
    if source:
        payload["source"] = source

    files = None
    if file_path:
        files = {"files.items": (os.path.basename(file_path), open(file_path, "rb"))}

    resp = requests.post(url, data=payload, files=files, headers=_headers(), timeout=60)
    resp.raise_for_status()
    return resp.json()


def get_task_status(task_id: str) -> dict:
    """GET /api/v1/tasks/{task_id}  (lightweight status, use for polling)."""
    url = f"{BASE_URL}/api/v1/tasks/{task_id}"
    resp = requests.get(url, headers=_headers(), timeout=60)
    resp.raise_for_status()
    return resp.json()


def get_task_result(task_id: str) -> dict:
    """GET /api/v1/tasks/{task_id}/result

    Returns the task plus the complete feed of agent activity (tool calls,
    intermediate messages, final response).
    """
    url = f"{BASE_URL}/api/v1/tasks/{task_id}/result"
    resp = requests.get(url, headers=_headers(), timeout=60)
    resp.raise_for_status()
    return resp.json()


def get_task_summary(task_id: str) -> dict:
    """GET /api/v1/tasks/{task_id}/summary

    Returns the task's final answer without intermediate reasoning steps.
    """
    url = f"{BASE_URL}/api/v1/tasks/{task_id}/summary"
    resp = requests.get(url, headers=_headers(), timeout=60)
    resp.raise_for_status()
    return resp.json()


def run_agent_and_wait(
    query: str,
    file_path: str = "",
    output_config: str = "",
    poll_interval: float = 5.0,
    timeout: float = 300.0,
) -> dict:
    """Run an agent and poll until the task reaches a terminal state.

    Returns the final task result (full feed).
    """
    created = run_agent(query, file_path, output_config)
    task_id = created["task_id"]
    print(f"Task created: {task_id} (status={created.get('status')})")

    deadline = time.time() + timeout
    while time.time() < deadline:
        status = get_task_status(task_id)
        state = status["status"]
        print(f"  status={state}")
        if state in ("completed", "failed", "stopped"):
            break
        if state == "waiting_for_input":
            # Agent asked a question: POST /api/v1/tasks/{task_id}/message
            break
        time.sleep(poll_interval)
    else:
        raise TimeoutError(f"Task {task_id} did not reach a terminal state in {timeout}s")

    return get_task_result(task_id)


# ---------------------------------------------------------------------------
# Extraction path (structured document parser - no agent required)
# ---------------------------------------------------------------------------
def extract_sync(
    input_uri: str,
    output_format: str = "json",
    json_options: list | dict | str | None = None,
    csv_options: str = "",
    custom_instructions: str = "",
    include_metadata: str = "",
    config_id: str = "",
) -> dict:
    """POST /api/v2/extract/sync  (on extraction-api.nanonets.com)

    Extract structured data from a document synchronously as JSON or CSV.

    Args:
        input_uri: "file://<uuid>" URI (from POST /files) or a public URL.
        output_format: "json" (default) or "csv".
        json_options: field list ["field1", ...], JSON schema {...}, or keyword
            ("hierarchy_output", "table-of-contents").
        csv_options: "table" or "toc".
        custom_instructions: free-text extraction instructions (max 8000 chars).
        include_metadata: comma-separated "confidence_score,bounding_boxes".
        config_id: "config://<uuid>" of a saved extract config (alternative to
            repeating extraction_config).
    """
    body: dict = {"input": input_uri}
    if config_id:
        body["config_id"] = config_id
    if not config_id:
        cfg: dict = {"output_format": output_format}
        if json_options is not None:
            cfg["json_options"] = json_options
        if csv_options:
            cfg["csv_options"] = csv_options
        if custom_instructions:
            cfg["custom_instructions"] = custom_instructions
        if include_metadata:
            cfg["include_metadata"] = include_metadata
        body["extraction_config"] = cfg

    url = f"{EXTRACTION_URL}/api/v2/extract/sync"
    resp = requests.post(url, json=body, headers=_headers(), timeout=120)
    resp.raise_for_status()
    return resp.json()


# ---------------------------------------------------------------------------
# Demo / usage
# ---------------------------------------------------------------------------
def main() -> None:
    print("Nanonets Agents Platform - API reference demo")
    print("=" * 60)

    if not API_KEY:
        print("Set NANONETS_AGENTS_API_KEY to run the live calls.")
        return

    # 1. Agent path
    if AGENT_ID:
        result = run_agent_and_wait(
            query="Extract the transaction table from the attached PDF "
                  "and return it as JSON.",
            file_path=FILE_PATH,
        )
        print("\nTask result keys:", list(result.keys()))
        print("\nTask result (truncated):")
        print(str(result)[:2000])

    # 2. Extraction path (structured parser)
    # Requires a file:// URI or public URL. If you only have a local file,
    # upload it first via POST /files (see docs: file-upload/upload-file).
    #   example: extract_sync("https://example.com/report.pdf",
    #                         output_format="csv", csv_options="table")


if __name__ == "__main__":
    main()

# وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ
