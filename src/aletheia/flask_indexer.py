

from pathlib import Path
import ast
from .models import BlueprintInfo , ProjectIndex,RouteInfo

SKIP_PARTS = {".git", ".venv", "__pycache__", "node_modules"}

HTTP_METHOD_ALIASES = {
    "get": "GET",
    "post": "POST",
    "put": "PUT",
    "patch": "PATCH",
    "delete": "DELETE",
}

AUTH_DECORATOR_NAMES = {"jwt_required", "login_required"}


class FlaskRouteIndexer:
    def __init__(self , repo_root):
        self.repo_root = Path(repo_root).resolve()

    def build_index(self):
        trees = self._load_python_tress()
        blueprints = self._collect_blueprints(trees)
        routes = self._collect_routes(trees,blueprints)


        return ProjectIndex(
            framework="flask",
            repo_root=str(self.repo_root),
            blueprints=tuple(blueprints.values()),
            routes=tuple(routes),
        )
    
    def _collect_routes(self,trees, blueprints):
        routes = []
        for file_path , tree in trees.items():
            for node in ast.walk(tree):
                if not isinstance(node , ast.FunctionDef):
                    continue
                route_specs = self._extract_route_specs(node.decorator_list)
                if not route_specs:
                    continue
                decorators = tuple(
                    name for name in (self._decorator_name(d) for d in node.decorator_list)
                    if name
                )
                auth_decorators = tuple(name for name in decorators if name in AUTH_DECORATOR_NAMES or name.endswith("_required"))
                
                for blueprint_variable , rule , method in route_specs:
                    blueprint = blueprints.get(blueprint_variable)
                    url_prefix = blueprint.url_prefix if blueprint else ""
                    blueprint_name = blueprint.blueprint_name if blueprint else None

                    routes.append(
                        RouteInfo(method = method,
                        rule=rule,
                        full_path = self._join_url_paths(url_prefix,rule),
                        handler_name = node.name,
                        blueprint_variable = blueprint_variable,
                        blueprint_name = blueprint_name,
                        url_prefix = url_prefix,
                        decorators = decorators,
                        auth_decorators = auth_decorators,
                        file_path = str(file_path.relative_to(self.repo_root)),
                        line_number = node.lineno,
                    )
                    )
        return routes
    
    def _extract_route_specs(self , decorators):
        specs = []

        for decorator in decorators:
            if not isinstance(decorator , ast.Call):
                continue
            if not isinstance(decorator.func, ast.Attribute):
                continue
            if not isinstance(decorator.func.value , ast.Name):
                continue
            blueprint_variable = decorator.func.value.id
            attr_name = decorator.func.attr
            if attr_name not in HTTP_METHOD_ALIASES:
                continue
            rule = self._string_literal(decorator.args[0]) if decorator.args else None
            if rule is None:
                continue

            specs.append((blueprint_variable,rule, HTTP_METHOD_ALIASES[attr_name]))
        return specs
    
    def _decorator_name(self , decorator):
        target = decorator.func if isinstance(decorator,ast.Call) else decorator

        if isinstance(target, ast.Name):
            return target.id
        if isinstance(target,ast.Attribute):
            return target.attr
        return None
    
    def _join_url_paths(self ,prefix , rule):
        prefix = prefix or ""
        rule = rule or ""

        if not prefix:
            return rule if rule.startswith("/") else f'/{rule}'
        if not rule:
            return prefix if prefix.startswith("/") else f'/{prefix}'

        return f"{prefix.rstrip('/')}/{rule.lstrip('/')}"


    def _load_python_tress(self):
        trees = {}
        for file_path in self.repo_root.rglob("*.py"):
            if any(part in SKIP_PARTS for part in file_path.parts):
                continue
            try:
                source = file_path.read_text(encoding="utf-8")
                trees[file_path] = ast.parse(source,filename=str(file_path))
            except (OSError, SyntaxError):
                continue
        return trees
    
    def _collect_blueprints(self, trees):
        found = {}
        for file_path , tree in trees.items():
            for node in ast.walk(tree):
                if not isinstance(node , ast.Assign):
                    continue
                blueprint = self._parse_blueprint_assignment(node, file_path)
                if blueprint is not None:
                    found[blueprint.variable_name] = blueprint
        return found
    
    def _parse_blueprint_assignment(self, node: ast.Assign, file_path: Path):
        if len(node.targets) != 1:
            return None

        target = node.targets[0]
        if not isinstance(target, ast.Name):
            return None

        if not isinstance(node.value, ast.Call):
            return None

        call = node.value
        if not self._is_blueprint_call(call):
            return None

        blueprint_name = self._string_literal(call.args[0]) if call.args else None
        if blueprint_name is None:
            return None

        url_prefix = ""
        for keyword in call.keywords:
            if keyword.arg == "url_prefix":
                url_prefix = self._string_literal(keyword.value) or ""
                break

        return BlueprintInfo(
            variable_name=target.id,
            blueprint_name=blueprint_name,
            url_prefix=url_prefix,
            file_path=str(file_path.relative_to(self.repo_root)),
        )
    def _is_blueprint_call(self , call):
        func = call.func
        return isinstance(func , ast.Name) and func.id == "Blueprint"
    def _string_literal(self , node):
        if isinstance(node , ast.Constant) and isinstance(node.value , str):
            return node.value
        return None

# if __name__=="__main__":
#     print(FlaskRouteIndexer("/Users/amiteshgangrade/Desktop/aahar/aahar").build_index().routes)
