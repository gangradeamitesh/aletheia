from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class BlueprintInfo:
    variable_name: str
    blueprint_name: str
    url_prefix: str
    file_path: str

    def to_dict(self) -> dict[str, str]:
        return {
            "variable_name": self.variable_name,
            "blueprint_name": self.blueprint_name,
            "url_prefix": self.url_prefix,
            "file_path": self.file_path,
        }


@dataclass(frozen=True)
class RouteInfo:
    method: str
    rule: str
    full_path: str
    handler_name: str
    blueprint_variable: str
    blueprint_name: str | None
    url_prefix: str
    decorators: tuple[str, ...]
    auth_decorators: tuple[str, ...]
    file_path: str
    line_number: int

    def to_dict(self) -> dict[str, object]:
        return {
            "method": self.method,
            "rule": self.rule,
            "full_path": self.full_path,
            "handler_name": self.handler_name,
            "blueprint_variable": self.blueprint_variable,
            "blueprint_name": self.blueprint_name,
            "url_prefix": self.url_prefix,
            "decorators": list(self.decorators),
            "auth_decorators": list(self.auth_decorators),
            "file_path": self.file_path,
            "line_number": self.line_number,
        }


@dataclass(frozen=True)
class ProjectIndex:
    framework: str
    repo_root: str
    blueprints: tuple[BlueprintInfo, ...]
    routes: tuple[RouteInfo, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "framework": self.framework,
            "repo_root": self.repo_root,
            "blueprints": [blueprint.to_dict() for blueprint in self.blueprints],
            "routes": [route.to_dict() for route in self.routes],
        }

@dataclass(frozen=True)
class RepoProfile:
    root: str
    framework: str | None
    entrypoints: tuple[str, ...]
    requirement_files: tuple[str, ...]
    test_paths: tuple[str, ...]
    service_markers: tuple[str, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "repo_root": self.root,
            "framework": self.framework,
            "entrypoints": list(self.entrypoints),
            "requirement_files": list(self.requirement_files),
            "test_paths": list(self.test_paths),
            "service_markers": list(self.service_markers),
        }

@dataclass(frozen=True)
class ScenarioSpec:
    name: str
    reason: str
    priority: str

    def to_dict(self) -> dict[str, str]:
        return {
            "name": self.name,
            "reason": self.reason,
            "priority": self.priority,
        }

@dataclass(frozen=True)
class EndpointPlan:
    method: str
    path: str
    handler_name: str
    file_path: str
    scenarios: tuple[ScenarioSpec, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "method": self.method,
            "path": self.path,
            "handler_name": self.handler_name,
            "file_path": self.file_path,
            "scenarios": [s.to_dict() for s in self.scenarios],
        }

@dataclass(frozen=True)
class DependencySnippet:
    symbol: str
    file_path : str
    source : str

    def to_dict(self) -> dict[str, str]:
        return {
            "symbol": self.symbol,
            "file_path": self.file_path,
            "source": self.source,
        }

@dataclass(frozen=True)
class RouteContext:
    route: RouteInfo
    handler_source: str
    dependencies: tuple[DependencySnippet, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "route": self.route.to_dict(),
            "handler_source": self.handler_source,
            "dependencies": [dep.to_dict() for dep in self.dependencies],
        }
    
@dataclass(frozen=True)
class PromptContext:
    route: RouteInfo
    handler_source: str
    relevant_calls: tuple[str, ...]
    dependency_snippets: tuple[DependencySnippet, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "route": self.route.to_dict(),
            "handler_source": self.handler_source,
            "relevant_calls": list(self.relevant_calls),
            "dependency_snippets": [snippet.to_dict() for snippet in self.dependency_snippets],
        }
@dataclass(frozen=True)
class SymbolReference:
    symbol: str
    file_path: str
    source: str

    def to_dict(self) -> dict[str, str]:
        return {
            "symbol": self.symbol,
            "file_path": self.file_path,
            "source": self.source,
        }

@dataclass(frozen=True)
class TestRunResult:
    passed: bool
    exit_code: int
    test_file_path: str
    stdout: str
    stderr: str

    def to_dict(self) -> dict[str, object]:
        return {
            "passed": self.passed,
            "exit_code": self.exit_code,
            "test_file_path": self.test_file_path,
            "stdout": self.stdout,
            "stderr": self.stderr,
        }

@dataclass(frozen=True)
class ReviewFinding:
    severity: str
    finding_type: str
    message: str
    confidence:str
    file_path :str
    code_snippet: str

    def to_dict(self) -> dict[str, object]:
        return {
            "severity": self.severity,
            "finding_type": self.finding_type,
            "message": self.message,
            "confidence": self.confidence,
            "file_path": self.file_path,
            "code_snippet": self.code_snippet,
        }
    
@dataclass(frozen=True)
class RouteReview:
    route_path: str
    method: str
    finding : tuple[ReviewFinding, ...]

    def to_dict(self) -> dict[str, object]:
        return {
            "route_path": self.route_path,
            "method": self.method,
            "finding": [f.to_dict() for f in self.finding],
        }
    