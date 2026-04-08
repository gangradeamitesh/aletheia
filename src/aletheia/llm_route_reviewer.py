from .context_builder import ContextBuilder
from .llm_client import LLMClient
from .models import ProjectIndex , RepoProfile, ReviewFinding, RouteInfo, RouteReview
from .prompt import ROUTE_REVIEWER_SYSTEM_PROMPT , build_route_reviewer_prompt

class LLMRouteReviewer:

    def __init__(self, llm_client: LLMClient, profile: RepoProfile, index: ProjectIndex):
        self.llm_client = llm_client
        self.profile = profile
        self.index = index
        self.context_builder = ContextBuilder(index)

    def review_route(self, route: RouteInfo) -> RouteReview:
        prompt_context = self.context_builder.build_prompt_context(route)
        prompt = build_route_reviewer_prompt(self.profile,prompt_context=prompt_context)
        data = self.llm_client.chat_json(ROUTE_REVIEWER_SYSTEM_PROMPT,prompt)
        findings = self._parse_findings(route , data)

        return RouteReview(
            route_path=route.full_path,
            method=route.method,
            finding=findings,)
    
    def _parse_findings(self, route: RouteInfo, data: dict) -> tuple[ReviewFinding, ...]:
        raw_items = data.get("findings", [])
        findings = []

        for item in raw_items:
            severity = item.get("severity", "medium")
            finding_type = item.get("finding_type", "ambiguous_behavior")
            message = item.get("message")
            confidence = item.get("confidence", "medium")
            code_snippet = item.get("code_snippet")

            if not message:
                continue

            # if severity not in {"high", "medium", "low"}:
            #     severity = "medium"

            # if confidence not in {"high", "medium", "low"}:
            #     confidence = "medium"

            findings.append(
                ReviewFinding(
                    severity=severity,
                    finding_type=finding_type,
                    message=message,
                    confidence=confidence,
                    file_path=route.file_path,
                    code_snippet=code_snippet,
                )
            )

        return tuple(findings)    