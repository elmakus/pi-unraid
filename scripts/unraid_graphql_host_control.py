#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import os
import re
import stat
import sys
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

ALLOWED_ACTIONS = ("start", "stop", "restart", "pause", "unpause")
KEY_PATTERN = re.compile(r"^[A-Za-z0-9_-]{16,}$")

READBACK_QUERY = """
query HostReadback {
  info {
    id
    time
    os {
      platform
      distro
      release
      kernel
      arch
      hostname
    }
  }
  docker {
    containers {
      id
      names
      image
      state
      status
    }
  }
}
"""

CONTAINER_QUERY = """
query ContainerState($id: PrefixedID!) {
  docker {
    container(id: $id) {
      id
      names
      image
      state
      status
    }
  }
}
"""


class HostControlError(RuntimeError):
    def __init__(self, kind: str, message: str, **details: object):
        super().__init__(message)
        self.kind = kind
        self.message = message
        self.details = details


def emit(payload: dict, *, stream=sys.stdout) -> None:
    print(json.dumps(payload, sort_keys=True), file=stream)


def endpoint_from_args(value: str | None) -> str:
    endpoint = value or os.environ.get("UNRAID_GRAPHQL_ENDPOINT", "")
    if not endpoint:
        raise HostControlError(
            "configuration",
            "GraphQL endpoint is required via --endpoint or UNRAID_GRAPHQL_ENDPOINT",
        )
    parsed = urllib.parse.urlparse(endpoint)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc or parsed.path != "/graphql":
        raise HostControlError(
            "configuration",
            "endpoint must be an explicit http(s) URL ending in /graphql",
        )
    if parsed.username or parsed.password:
        raise HostControlError("configuration", "credentials are forbidden in the endpoint URL")
    return endpoint


def load_api_key(path_value: str | None) -> str:
    raw_path = path_value or os.environ.get("UNRAID_API_KEY_FILE", "")
    if not raw_path:
        raise HostControlError(
            "credential",
            "API key file is required via --api-key-file or UNRAID_API_KEY_FILE",
        )
    path = Path(raw_path)
    if path.is_symlink():
        raise HostControlError("credential", "API key file must not be a symlink")
    try:
        st = path.stat()
    except FileNotFoundError as exc:
        raise HostControlError("credential", "API key file does not exist") from exc
    if not stat.S_ISREG(st.st_mode):
        raise HostControlError("credential", "API key path must be a regular file")
    mode = stat.S_IMODE(st.st_mode)
    if mode & 0o077:
        raise HostControlError(
            "credential",
            "API key file must not be readable or writable by group/other",
            mode=format(mode, "03o"),
        )
    key = path.read_text().strip()
    if not KEY_PATTERN.fullmatch(key):
        raise HostControlError("credential", "API key file has an invalid key format")
    return key


def graphql(endpoint: str, api_key: str, query: str, variables: dict | None = None) -> dict:
    payload = json.dumps({"query": query, "variables": variables or {}}).encode()
    request = urllib.request.Request(
        endpoint,
        data=payload,
        headers={
            "content-type": "application/json",
            "x-api-key": api_key,
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=15) as response:
            body = json.loads(response.read())
    except urllib.error.HTTPError as exc:
        raise HostControlError(
            "http",
            "GraphQL endpoint returned an HTTP error",
            status=exc.code,
        ) from exc
    except (urllib.error.URLError, TimeoutError) as exc:
        raise HostControlError("transport", "GraphQL endpoint is unreachable") from exc
    except json.JSONDecodeError as exc:
        raise HostControlError("protocol", "GraphQL endpoint returned invalid JSON") from exc

    errors = body.get("errors")
    if errors:
        messages = [
            str(item.get("message", "GraphQL error"))[:300]
            for item in errors
            if isinstance(item, dict)
        ]
        raise HostControlError("graphql", "GraphQL request failed", errors=messages)
    data = body.get("data")
    if not isinstance(data, dict):
        raise HostControlError("protocol", "GraphQL response did not contain a data object")
    return data


def container_state(endpoint: str, api_key: str, container_id: str) -> dict:
    data = graphql(endpoint, api_key, CONTAINER_QUERY, {"id": container_id})
    docker = data.get("docker")
    container = docker.get("container") if isinstance(docker, dict) else None
    if not isinstance(container, dict):
        raise HostControlError("not_found", "container was not returned by GraphQL")
    return container


def action_query(action: str) -> str:
    if action not in ALLOWED_ACTIONS:
        raise HostControlError(
            "policy",
            "unsupported Docker mutation",
            allowed=list(ALLOWED_ACTIONS),
        )
    return f"""
mutation ContainerAction($id: PrefixedID!) {{
  docker {{
    {action}(id: $id) {{
      id
      names
      image
      state
      status
    }}
  }}
}}
"""


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--endpoint")
    parser.add_argument("--api-key-file")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("readback")
    state = sub.add_parser("container-state")
    state.add_argument("--id", required=True)
    mutate = sub.add_parser("container-action")
    mutate.add_argument("--id", required=True)
    mutate.add_argument("--action", required=True, choices=ALLOWED_ACTIONS)
    args = parser.parse_args()

    try:
        endpoint = endpoint_from_args(args.endpoint)
        api_key = load_api_key(args.api_key_file)

        if args.command == "readback":
            data = graphql(endpoint, api_key, READBACK_QUERY)
            emit({"ok": True, "operation": "readback", "data": data})
            return 0

        if args.command == "container-state":
            current = container_state(endpoint, api_key, args.id)
            emit({"ok": True, "operation": "container-state", "container": current})
            return 0

        before = container_state(endpoint, api_key, args.id)
        mutation = graphql(endpoint, api_key, action_query(args.action), {"id": args.id})
        docker = mutation.get("docker")
        changed = docker.get(args.action) if isinstance(docker, dict) else None
        if not isinstance(changed, dict):
            raise HostControlError("protocol", "Docker mutation did not return a container")
        after = container_state(endpoint, api_key, args.id)
        emit(
            {
                "ok": True,
                "operation": "container-action",
                "action": args.action,
                "before": before,
                "mutation_result": changed,
                "after": after,
            }
        )
        return 0
    except HostControlError as exc:
        emit(
            {
                "ok": False,
                "error": exc.kind,
                "message": exc.message,
                **exc.details,
            },
            stream=sys.stderr,
        )
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
