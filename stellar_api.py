"""Small Stellar One OpenAPI client used by the report generator."""

from __future__ import annotations

import time
from typing import Any

import requests
from urllib3.exceptions import InsecureRequestWarning

import urllib3

from config import Settings


class StellarApiError(RuntimeError):
    """Raised when the Stellar One API request fails."""


class StellarOneClient:
    def __init__(self, settings: Settings) -> None:
        self.settings = settings
        self.session = requests.Session()
        self.session.verify = settings.verify_ssl
        if settings.verify_ssl is False:
            urllib3.disable_warnings(InsecureRequestWarning)
        self.session.headers.update(
            {
                "Authorization": settings.api_key,
                "Accept": "application/json",
                "Content-Type": "application/json",
            }
        )

    def _request(self, method: str, path: str, **kwargs: Any) -> dict[str, Any]:
        url = f"{self.settings.base_url}{path}"
        try:
            response = self.session.request(
                method,
                url,
                timeout=self.settings.timeout_seconds,
                **kwargs,
            )
        except requests.RequestException as exc:
            raise StellarApiError(f"API request failed: {exc}") from exc

        if response.status_code >= 400:
            request_id = response.headers.get("x-stellar-request-id", "unknown")
            message = response.text.strip() or response.reason
            raise StellarApiError(
                f"{method} {path} returned HTTP {response.status_code} "
                f"(request id: {request_id}): {message}"
            )

        if not response.content:
            return {}

        try:
            payload = response.json()
        except ValueError as exc:
            raise StellarApiError(f"{method} {path} did not return valid JSON.") from exc

        if not isinstance(payload, dict):
            raise StellarApiError(f"{method} {path} returned unexpected JSON type.")
        return payload

    def list_agents(self, limit: int = 200, max_pages: int = 20) -> list[dict[str, Any]]:
        return self._list_paginated_agents("/api/v1/agents", limit=limit, max_pages=max_pages)

    def list_groups(self, limit: int = 200, max_pages: int = 20) -> list[dict[str, Any]]:
        all_groups: list[dict[str, Any]] = []
        page = 1
        page_token: str | None = None

        while page <= max_pages:
            params: dict[str, Any] = {"limit": limit}
            if page_token:
                params["pageToken"] = page_token
            else:
                params["page"] = page

            payload = self._request("GET", "/api/v1/groups", params=params)
            groups = payload.get("groups", [])
            if not isinstance(groups, list):
                raise StellarApiError("GET /api/v1/groups returned an invalid groups list.")
            all_groups.extend(group for group in groups if isinstance(group, dict))

            pagination = payload.get("pagination", {})
            page_token = pagination.get("pageToken") if isinstance(pagination, dict) else None
            total = _safe_int(pagination.get("total")) if isinstance(pagination, dict) else None
            if page_token:
                page += 1
                continue
            if not groups or (total is not None and len(all_groups) >= total):
                break
            page += 1

        return all_groups

    def find_group_uuid_by_name(self, group_name: str) -> str:
        group_name_lower = group_name.casefold()
        for group in self.list_groups():
            if str(group.get("name", "")).casefold() == group_name_lower:
                group_uuid = group.get("groupUuid")
                if group_uuid:
                    return str(group_uuid)
        raise StellarApiError(f"No agent group found with name '{group_name}'.")

    def get_group(self, group_uuid: str) -> dict[str, Any]:
        payload = self._request("GET", f"/api/v1/groups/{group_uuid}")
        group = payload.get("group")
        if isinstance(group, dict):
            return group
        # Some deployments return the group object directly.
        return payload

    def list_group_agents(
        self,
        group_uuid: str,
        limit: int = 200,
        max_pages: int = 20,
    ) -> list[dict[str, Any]]:
        return self._list_paginated_agents(
            f"/api/v1/groups/{group_uuid}/agents",
            limit=limit,
            max_pages=max_pages,
        )

    def find_agent_uuid_by_ip(self, ip_address: str, agents: list[dict[str, Any]] | None = None) -> str:
        for agent in agents if agents is not None else self.list_agents():
            if _ip_matches(agent.get("ipAddress"), ip_address):
                agent_uuid = agent.get("agentUuid")
                if agent_uuid:
                    return str(agent_uuid)
        raise StellarApiError(f"No agent found with IP address '{ip_address}'.")

    def find_agent_uuid_by_name(
        self,
        hostname: str,
        agents: list[dict[str, Any]] | None = None,
    ) -> str:
        hostname_lower = hostname.casefold()
        for agent in agents if agents is not None else self.list_agents():
            if str(agent.get("hostname", "")).casefold() == hostname_lower:
                agent_uuid = agent.get("agentUuid")
                if agent_uuid:
                    return str(agent_uuid)
        raise StellarApiError(f"No agent found with hostname '{hostname}'.")

    def resolve_single_agent_in_group(self, group_uuid: str) -> str:
        agents = self.list_group_agents(group_uuid)
        if len(agents) == 1 and agents[0].get("agentUuid"):
            return str(agents[0]["agentUuid"])

        candidates = ", ".join(
            str(agent.get("hostname") or agent.get("ipAddress") or agent.get("agentUuid"))
            for agent in agents[:10]
        )
        detail = f" Candidates: {candidates}" if candidates else ""
        raise StellarApiError(
            f"Group contains {len(agents)} agents. Add --agent-name, --agent-ip, or --agent-uuid."
            f"{detail}"
        )

    def ensure_agent_in_group(self, agent_uuid: str, group_uuid: str) -> None:
        for agent in self.list_group_agents(group_uuid):
            if str(agent.get("agentUuid")) == agent_uuid:
                return
        raise StellarApiError(f"Agent '{agent_uuid}' was not found in group '{group_uuid}'.")

    def _list_paginated_agents(
        self,
        path: str,
        limit: int = 200,
        max_pages: int = 20,
    ) -> list[dict[str, Any]]:
        all_agents: list[dict[str, Any]] = []
        page = 1
        page_token: str | None = None

        while page <= max_pages:
            params: dict[str, Any] = {"limit": limit}
            if page_token:
                params["pageToken"] = page_token
            else:
                params["page"] = page

            payload = self._request("GET", path, params=params)
            agents = payload.get("agents", [])
            if not isinstance(agents, list):
                raise StellarApiError(f"GET {path} returned an invalid agents list.")
            all_agents.extend(agent for agent in agents if isinstance(agent, dict))

            pagination = payload.get("pagination", {})
            page_token = pagination.get("pageToken") if isinstance(pagination, dict) else None
            total = _safe_int(pagination.get("total")) if isinstance(pagination, dict) else None
            if page_token:
                page += 1
                continue
            if not agents or (total is not None and len(all_agents) >= total):
                break
            page += 1

        return all_agents

    def get_agent(self, agent_uuid: str) -> dict[str, Any]:
        payload = self._request("GET", f"/api/v1/agents/{agent_uuid}")
        agent = payload.get("agent")
        if not isinstance(agent, dict):
            raise StellarApiError("GET agent response did not contain an agent object.")
        return agent

    def get_agent_policy(self, agent_uuid: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/policy/agents/{agent_uuid}")

    def start_scan_now(self, agent_uuid: str, product_code: str | None = None) -> dict[str, Any]:
        scan_config = self._build_scan_config(product_code)
        payload = {
            "agentUuids": [agent_uuid],
            "scanConfig": scan_config,
        }
        return self._request("POST", "/api/v1/task/scan-now", json=payload)

    def start_group_scan_now(self, group_uuid: str) -> dict[str, Any]:
        payload = {
            "groupUuids": [group_uuid],
            "scanConfig": self._build_scan_config(None),
        }
        return self._request("POST", "/api/v1/task/scan-now", json=payload)

    def get_task_status(self, task_id_or_uuid: str) -> dict[str, Any]:
        return self._request("GET", f"/api/v1/task/{task_id_or_uuid}/status")

    def wait_for_task(
        self,
        task_id_or_uuid: str,
        poll_seconds: int = 5,
        timeout_seconds: int = 300,
    ) -> dict[str, Any]:
        deadline = time.monotonic() + timeout_seconds
        last_status: dict[str, Any] = {}

        while time.monotonic() < deadline:
            last_status = self.get_task_status(task_id_or_uuid)
            if _task_is_done(last_status):
                return last_status
            print(".", end="", flush=True)
            time.sleep(poll_seconds)

        print()
        raise StellarApiError(
            f"Timed out after {timeout_seconds}s waiting for task {task_id_or_uuid}."
        )

    @staticmethod
    def _build_scan_config(product_code: str | None) -> dict[str, Any]:
        scan_config: dict[str, Any] = {
            "scanTarget": {
                "scanFolder": {"folderType": "FOLDER_TYPE_DEFAULT"},
            },
            "cpuUsage": "CPU_USAGE_NORMAL",
        }

        normalized = (product_code or "").casefold()
        if normalized == "enforce":
            scan_config["protectLegacyModeScan"] = {
                "scanAction": "SCAN_ACTION_DEFAULT_ACTION",
                "scanRemovable": True,
            }
        elif normalized == "protect":
            scan_config["protectScan"] = {
                "scanAction": "SCAN_ACTION_QUARANTINE",
                "advancedThreatScan": True,
                "scanRemovable": True,
            }
        else:
            # Unknown or mixed estate: provide both Windows scan modes and let the API
            # select the applicable task for the target agent.
            scan_config["protectScan"] = {
                "scanAction": "SCAN_ACTION_QUARANTINE",
                "advancedThreatScan": True,
                "scanRemovable": True,
            }
            scan_config["protectLegacyModeScan"] = {
                "scanAction": "SCAN_ACTION_DEFAULT_ACTION",
                "scanRemovable": True,
            }

        return scan_config


def task_identifier(scan_response: dict[str, Any]) -> str | None:
    protect_task_id = scan_response.get("protectTaskId")
    legacy_task_uuid = scan_response.get("protectLegacyModeTaskUuid")
    if protect_task_id is not None:
        return str(protect_task_id)
    if legacy_task_uuid:
        return str(legacy_task_uuid)
    return None


def _task_is_done(status_response: dict[str, Any]) -> bool:
    tasks = status_response.get("tasks", [])
    if not isinstance(tasks, list) or not tasks:
        return False
    return all(task.get("taskStatus") == "TASK_STATUS_DONE" for task in tasks if isinstance(task, dict))


def _safe_int(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _ip_matches(agent_ip_value: Any, requested_ip: str) -> bool:
    values = str(agent_ip_value or "").replace(";", ",").split(",")
    return any(value.strip() == requested_ip for value in values)
