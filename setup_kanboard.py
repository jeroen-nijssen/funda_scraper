#!/usr/bin/env python3
"""Initialise Kanboard with the project and board columns the scraper expects.

This runs automatically as the `kanboard-init` service in docker-compose, and
can be re-run by hand with `./woningradar.sh setup`. It is idempotent: running
it against an already-configured Kanboard makes no destructive changes.
"""

import os
import sys
import time

import requests

# Board columns the scraper's triage workflow relies on.
DESIRED_COLUMNS = ["New Listings", "Under Review", "Interested", "Not Interested"]


def wait_for_kanboard(url: str, max_attempts: int = 30, delay: int = 2) -> bool:
    """Wait for Kanboard to respond to HTTP requests."""
    print(f"Waiting for Kanboard at {url} ...")
    for attempt in range(1, max_attempts + 1):
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print("Kanboard is ready!")
                return True
        except requests.RequestException:
            pass

        print(f"Attempt {attempt}/{max_attempts} - Kanboard not ready yet...")
        time.sleep(delay)

    return False


def kanboard_api_call(url: str, method: str, params: dict, username: str, password: str) -> dict:
    """Make a JSON-RPC API call to Kanboard."""
    payload = {
        "jsonrpc": "2.0",
        "method": method,
        "id": 1,
        "params": params,
    }

    response = requests.post(url, json=payload, auth=(username, password), timeout=10)

    if response.status_code != 200:
        raise RuntimeError(f"API call '{method}' failed: {response.status_code} - {response.text}")

    body = response.json()
    if "error" in body:
        raise RuntimeError(f"API call '{method}' returned an error: {body['error']}")

    return body


def find_project(api_url: str, name: str, username: str, password: str) -> dict | None:
    """Return the project with the given name, or None when it does not exist."""
    result = kanboard_api_call(api_url, "getAllProjects", {}, username, password)
    for project in result.get("result") or []:
        if project.get("name") == name:
            return project
    return None


def configure_columns(api_url: str, project_id: int, username: str, password: str) -> None:
    """Ensure the board has the columns the scraper expects.

    Kanboard's removeColumn deletes the tasks inside the column, so the board is
    only restructured while it is still empty. On a board that already holds
    tasks we add what is missing and leave everything else untouched.
    """
    result = kanboard_api_call(api_url, "getColumns", {"project_id": project_id}, username, password)
    columns = result.get("result") or []
    existing_names = [column["title"] for column in columns]

    if set(existing_names) == set(DESIRED_COLUMNS):
        print("Board columns are already configured correctly.")
        return

    tasks = kanboard_api_call(
        api_url, "getAllTasks", {"project_id": project_id, "status_id": 1}, username, password
    )
    task_count = len(tasks.get("result") or [])

    if task_count == 0:
        print("Board is empty - applying the standard column layout...")
        for column in columns:
            kanboard_api_call(
                api_url,
                "removeColumn",
                {"project_id": project_id, "column_id": int(column["id"])},
                username,
                password,
            )
        for column_name in DESIRED_COLUMNS:
            kanboard_api_call(
                api_url,
                "addColumn",
                {
                    "project_id": project_id,
                    "title": column_name,
                    "task_limit": 0,
                    "description": f"Column for {column_name.lower()}",
                },
                username,
                password,
            )
            print(f"Created column: {column_name}")
        return

    # The board is in use: only add what is missing, never remove.
    print(f"WARNING: board already holds {task_count} task(s).")
    print("WARNING: existing columns are left untouched to avoid deleting tasks.")
    for column_name in DESIRED_COLUMNS:
        if column_name in existing_names:
            continue
        kanboard_api_call(
            api_url,
            "addColumn",
            {
                "project_id": project_id,
                "title": column_name,
                "task_limit": 0,
                "description": f"Column for {column_name.lower()}",
            },
            username,
            password,
        )
        print(f"Added missing column: {column_name}")


def publish_project_id(project_id: int) -> None:
    """Write the resolved project ID to a file when KANBAN_PROJECT_ID_FILE is set."""
    target = os.getenv("KANBAN_PROJECT_ID_FILE")
    if not target:
        return
    try:
        with open(target, "w", encoding="utf-8") as handle:
            handle.write(str(project_id))
        print(f"Wrote project ID to {target}")
    except OSError as exc:
        print(f"WARNING: could not write project ID to {target}: {exc}")


def setup_kanboard() -> bool:
    """Set up Kanboard with the project and columns the scraper expects."""
    base_url = os.getenv("KANBAN_BASE_URL", "http://kanboard").rstrip("/")
    api_url = f"{base_url}/jsonrpc.php"
    username = os.getenv("KANBAN_USERNAME", "admin")
    password = os.getenv("KANBAN_PASSWORD", "admin")
    project_name = os.getenv("KANBAN_PROJECT_NAME", "Property Listings")

    if not wait_for_kanboard(base_url):
        print("ERROR: Kanboard failed to become available within the expected time")
        return False

    try:
        print("Setting up Kanboard...")

        project = find_project(api_url, project_name, username, password)

        if project is None:
            print(f"Creating '{project_name}' project...")
            created = kanboard_api_call(
                api_url,
                "createProject",
                {
                    "name": project_name,
                    "description": "Property listings collected from Funda, Huispedia and Pararius",
                },
                username,
                password,
            )
            new_id = created.get("result")
            if not new_id:
                print("ERROR: Failed to create project")
                return False
            project_id = int(new_id)
            print(f"Created project with ID: {project_id}")
        else:
            project_id = int(project["id"])
            print(f"Found existing '{project_name}' project (ID: {project_id})")

        configure_columns(api_url, project_id, username, password)
        publish_project_id(project_id)

        print("\n" + "=" * 50)
        print("Kanboard setup completed successfully!")
        print(f"Kanboard URL : {base_url}")
        print(f"Username     : {username}")
        print(f"Project      : {project_name}")
        print(f"Project ID   : {project_id}")
        print("=" * 50)
        print(f"\nSet KANBAN_PROJECT_ID={project_id} in your .env file so the")
        print("scraper writes listings to this project.")

        return True

    except Exception as exc:
        print(f"ERROR: Failed to setup Kanboard: {exc}")
        return False


if __name__ == "__main__":
    success = setup_kanboard()
    sys.exit(0 if success else 1)
