from __future__ import annotations

from pathlib import Path

from .models import EndpointPlan, ProjectIndex, RepoProfile, RouteInfo, ScenarioSpec


ACTION_SEGMENTS = {
    "login",
    "logout",
    "register",
    "verify",
    "resend",
    "assign",
    "status",
    "accept",
    "reject",
    "toggle",
}

SERVICE_HINTS = {
    "twilio": ("twilio", "send_otp", "check_otp", "otp"),
    "cloudinary": ("cloudinary",),
    "requests": ("requests.",),
    "socketio": ("socketio",),
    "webhooks": ("webhook", "dispatch_webhook"),
}


class ScenarioPlanner:
    def __init__(self, profile: RepoProfile, index: ProjectIndex):
        self.profile = profile
        self.index = index

    def build_plan(self) -> tuple[EndpointPlan, ...]:
        plans = [self._plan_route(route) for route in self.index.routes]
        return tuple(plans)

    def _plan_route(self, route: RouteInfo) -> EndpointPlan:
        route_kind = self._classify_route_kind(route)

        scenarios = []
        scenarios.extend(self._seed_scenarios(route, route_kind))
        scenarios.extend(self._source_based_scenarios(route, route_kind))
        scenarios = self._dedupe_scenarios(scenarios)

        return EndpointPlan(
            method=route.method,
            path=route.full_path,
            handler_name=route.handler_name,
            file_path=route.file_path,
            scenarios=tuple(scenarios),
        )

    def _classify_route_kind(self, route: RouteInfo) -> str:
        segments = self._path_segments(route.full_path)
        last_segment = segments[-1] if segments else ""
        has_params = self._has_path_params(route.full_path)

        if last_segment in ACTION_SEGMENTS:
            return "action"

        if route.method == "GET":
            return "detail" if has_params else "list"

        if route.method == "POST":
            return "create" if not has_params else "action"

        if route.method in {"PUT", "PATCH"}:
            return "update"

        if route.method == "DELETE":
            return "delete"

        return "custom"

    def _seed_scenarios(self, route: RouteInfo, route_kind: str) -> list[ScenarioSpec]:
        scenarios = [
            ScenarioSpec(
                name="happy_path",
                reason="Every endpoint needs a baseline success case",
                priority="high",
            )
        ]

        # This is still coarse because we intentionally skipped auth_optional for now.
        if route.auth_decorators:
            scenarios.append(
                ScenarioSpec(
                    name="unauthorized",
                    reason="Route has auth decorators",
                    priority="high",
                )
            )

        if route_kind == "list":
            scenarios.append(
                ScenarioSpec(
                    name="empty_list",
                    reason="List endpoints should handle zero records",
                    priority="medium",
                )
            )

        if route_kind == "detail":
            scenarios.append(
                ScenarioSpec(
                    name="not_found",
                    reason="Detail endpoints should handle missing resources",
                    priority="high",
                )
            )

        if route_kind == "create":
            scenarios.append(
                ScenarioSpec(
                    name="invalid_json",
                    reason="Create endpoints should reject malformed payloads",
                    priority="medium",
                )
            )
            scenarios.append(
                ScenarioSpec(
                    name="missing_required_fields",
                    reason="Create endpoints usually validate required fields",
                    priority="high",
                )
            )

        if route_kind == "update":
            scenarios.append(
                ScenarioSpec(
                    name="not_found",
                    reason="Update endpoints should handle missing resources",
                    priority="high",
                )
            )
            scenarios.append(
                ScenarioSpec(
                    name="invalid_json",
                    reason="Update endpoints should reject malformed payloads",
                    priority="medium",
                )
            )

        if route_kind == "delete":
            scenarios.append(
                ScenarioSpec(
                    name="not_found",
                    reason="Delete endpoints should handle missing resources",
                    priority="high",
                )
            )

        if route_kind == "action":
            if self._has_path_params(route.full_path):
                scenarios.append(
                    ScenarioSpec(
                        name="not_found",
                        reason="Action endpoint targets a specific resource",
                        priority="high",
                    )
                )

            if route.method in {"POST", "PUT", "PATCH"}:
                scenarios.append(
                    ScenarioSpec(
                        name="invalid_action_input",
                        reason="Workflow endpoints often validate action-specific input or state",
                        priority="medium",
                    )
                )

        return scenarios

    def _source_based_scenarios(self, route: RouteInfo, route_kind: str) -> list[ScenarioSpec]:
        source = self._read_route_file(route)
        scenarios: list[ScenarioSpec] = []

        if not source:
            return scenarios

        if any(token in source for token in ("already exists", "integrityerror", "409")):
            scenarios.append(
                ScenarioSpec(
                    name="conflict",
                    reason="Handler appears to have duplicate/conflict branches",
                    priority="medium",
                )
            )

        for service_name, hints in SERVICE_HINTS.items():
            if service_name not in self.profile.service_markers:
                continue

            if any(hint in source for hint in hints):
                scenarios.append(
                    ScenarioSpec(
                        name=f"{service_name}_failure",
                        reason=f"Route appears to depend on {service_name}",
                        priority="high" if service_name in {"twilio", "webhooks"} else "medium",
                    )
                )

        if route_kind == "action" and any(
            token in source
            for token in ("status", "accept", "reject", "assign", "verify")
        ):
            scenarios.append(
                ScenarioSpec(
                    name="invalid_state_transition",
                    reason="Workflow/action route may have state-specific failure paths",
                    priority="medium",
                )
            )

        return scenarios

    def _read_route_file(self, route: RouteInfo) -> str:
        path = Path(self.index.repo_root) / route.file_path
        try:
            return path.read_text(encoding="utf-8").lower()
        except OSError:
            return ""

    def _dedupe_scenarios(self, scenarios: list[ScenarioSpec]) -> list[ScenarioSpec]:
        seen = set()
        result = []

        for scenario in scenarios:
            if scenario.name in seen:
                continue
            seen.add(scenario.name)
            result.append(scenario)

        return result

    @staticmethod
    def _path_segments(path: str) -> list[str]:
        return [segment for segment in path.strip("/").split("/") if segment]

    @staticmethod
    def _has_path_params(path: str) -> bool:
        return "<" in path and ">" in path
