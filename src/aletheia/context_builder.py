import ast
from pathlib import Path

from .models import DependencySnippet , ProjectIndex , RouteContext , RouteInfo, PromptContext

IGNORED_CALLS = {
    "app.logger.info",
    "app.logger.debug",
    "app.logger.warning",
    "app.logger.error",
    "app.logger.critical",
    "app.logger.exception"
    "logger.info",
    "jsonify",
    "print",
    "requerst.get_json",
    "request.args.get",
    "payload.get",
}   

class ContextBuilder:

    def __init__(self,index: ProjectIndex):
        self.index = index
        self.repo_root = Path(index.repo_root)

    def build_route_context(self, route: RouteInfo): 
        file_path = self.repo_root / route.file_path
        source = file_path.read_text(encoding="utf-8") if file_path.exists() else ""
        if source == "":
            print("Warning: Could not read source for route:", route)
        tree = ast.parse(source, filename=str(file_path)) if source else None
        if not tree:
            print("Warning: Could not parse AST for route:", route)
        import_map = self._build_import_map(tree)
        function_node = self._find_function_node(tree, route.handler_name)
        called_symbols = self._extract_called_symbols(function_node)
        resolved_calls = self._resolve_direct_symbols(called_symbols, import_map)
        relevant_calls = self._filter_relevant_calls(resolved_calls)
        handler_source = self._extract_function_source(route.file_path, route.handler_name)

        return {
            "route": route,
            "called_symbols": called_symbols,
            "import_map": import_map,
            "resolved_calls": resolved_calls,
            "relevant_calls": relevant_calls,
            "handler_source": handler_source,

        }
    def _find_function_node(self, tree , function_name):
        for node in ast.walk(tree):
            if isinstance(node , ast.FunctionDef) and node.name == function_name:
                return node
        raise ValueError(f"Function not found: {function_name}")
    
    def _build_import_map(self, tree):
        import_map = {}
        for node in ast.iter_child_nodes(tree):
            if isinstance(node , ast.Import):
                for alias in node.names:
                    import_map[alias.asname or alias.name] = alias.name
            elif isinstance(node , ast.ImportFrom):
                module = node.module
                level_prefix = "." * node.level
                for alias in node.names:
                    local_name = alias.asname or alias.name
                    if module:
                        import_map[local_name] = f"{level_prefix}{module}.{alias.name}"
                    else:
                        import_map[local_name] = f"{level_prefix}.{alias.name}"

        return import_map
    
    def _extract_called_symbols(self, function_node):
        called = []
        for stmt in function_node.body:
            for node in ast.walk(stmt):
                if isinstance(node , ast.Call):
                    symbol = self._call_to_symbol(node.func)
                    if symbol:
                        called.append(symbol)
        
        seen = set()
        result = []
        for sym in called:
            if sym not in seen:
                seen.add(sym)
                result.append(sym)
        return result
    
    def _call_to_symbol(self, node):
        if isinstance(node , ast.Name):
            return node.id

        if isinstance(node , ast.Attribute):
            parts = []
            current = node
            while isinstance(current, ast.Attribute):
                parts.append(current.attr)
                current = current.value
            if isinstance(current, ast.Name):
                parts.append(current.id)
                parts.reverse()
                return ".".join(parts)
    
        return None
        
    def _resolve_direct_symbols(self, direct_calls, import_map):
        resolved = []
        for sym in direct_calls:
            root = sym.split(".")[0]
            imported_from = import_map.get(root)
            resolved.append({
                "call":sym,
                "root_symbol": root,
                "imported_from": imported_from or root,
            })
        return resolved
    
    def _is_relevant_call(self, symbol):
        for prefix in IGNORED_CALLS:
            if symbol.startswith(prefix):
                return False
        return True
    
    def _filter_relevant_calls(self, resolved_calls):
        return [
            item for item in resolved_calls
            if self._is_relevant_call(item["call"])
        ]
    
    def _extract_function_source(self , relative_file_path , function_name):
        file_path = self.repo_root / relative_file_path
        if not file_path.exists():
            print("Warning: File not found for function source extraction:", file_path)
            return ""
        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
        lines = source.splitlines()
        for node in ast.walk(tree):
            if isinstance(node , ast.FunctionDef) and node.name == function_name:
                start = node.lineno - 1
                end = getattr(node, "end_lineno", node.lineno)
                return "\n".join(lines[start:end])
        return ""
    
    def _file_path_to_module(self, relative_file_path: str) -> str:
        return relative_file_path.removesuffix(".py").replace("/", ".")
    
    def _resolve_import_path(self, route_file_path: str, imported_from: str) -> str | None:
        if not imported_from:
            return None

        if not imported_from.startswith("."):
            return imported_from

        current_module = self._file_path_to_module(route_file_path)
        current_parts = current_module.split(".")
        package_parts = current_parts[:-1]
        
        dot_count = len(imported_from) - len(imported_from.lstrip("."))
        suffix = imported_from.lstrip(".")

        if dot_count > len(package_parts):
            return None
        levels_up = max(dot_count-1, 0)
        base_parts = package_parts[: len(package_parts) - levels_up]
        if suffix:
            return ".".join(base_parts + suffix.split("."))
        return ".".join(base_parts)
    
    def _split_import_target(self, resolved_import: str) -> tuple[str, str] | None:
        if "." not in resolved_import:
            return None
        module_path, symbol_name = resolved_import.rsplit(".", 1)
        return module_path, symbol_name
    
    def _module_to_file_path(self, module_path: str) -> str:
        return module_path.replace(".", "/") + ".py"

    def _extract_function_source_from_file(self, relative_file_path: str, function_name: str) -> str | None:
        file_path = self.repo_root / relative_file_path
        if not file_path.exists():
            return None

        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
        lines = source.splitlines()

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                start = node.lineno - 1
                end = getattr(node, "end_lineno", node.lineno)
                return "\n".join(lines[start:end])

        return None
    
    def _extract_class_method_source(self, relative_file_path: str, class_name: str, method_name: str) -> str | None:
        file_path = self.repo_root / relative_file_path
        if not file_path.exists():
            return None

        source = file_path.read_text(encoding="utf-8")
        tree = ast.parse(source, filename=str(file_path))
        lines = source.splitlines()

        for node in ast.walk(tree):
            if not isinstance(node, ast.ClassDef) or node.name != class_name:
                continue

            for item in node.body:
                if isinstance(item, ast.FunctionDef) and item.name == method_name:
                    start = item.lineno - 1
                    end = getattr(item, "end_lineno", item.lineno)
                    return "\n".join(lines[start:end])

        return None
    def _resolve_prompt_dependencies(self, route: RouteInfo, relevant_calls):
        snippets = []
        seen = set()

        for item in relevant_calls:
            snippet = self._resolve_single_symbol(
                route,
                item["call"],
                item.get("imported_from"),
            )
            if snippet is None:
                continue
            if snippet.symbol in seen:
                continue

            seen.add(snippet.symbol)
            snippets.append(snippet)

        return snippets
    def _resolve_single_symbol(self, route: RouteInfo, call: str, imported_from: str | None):
        if not imported_from:
            return None

        resolved_import = self._resolve_import_path(route.file_path, imported_from)
        if not resolved_import:
            return None

        call_parts = call.split(".")
        split_target = self._split_import_target(resolved_import)
        if not split_target:
            return None

        module_path, imported_symbol = split_target
        file_path = self._module_to_file_path(module_path)

        if len(call_parts) == 1:
            function_name = call_parts[0]
            if function_name != imported_symbol:
                return None

            source = self._extract_function_source_from_file(file_path, function_name)
            if source:
                return DependencySnippet(symbol=call, file_path=file_path, source=source)

        if len(call_parts) == 2:
            root_symbol, member_name = call_parts
            if root_symbol != imported_symbol:
                return None

            source = self._extract_class_method_source(file_path, root_symbol, member_name)
            if source:
                return DependencySnippet(symbol=call, file_path=file_path, source=source)

        return None

    def build_prompt_context(self, route: RouteInfo) -> PromptContext:
        raw = self.build_route_context(route)
        # print("actual handler source:")
        # print(raw['handler_source'])
        dependency_snippets = self._resolve_prompt_dependencies(route, raw["relevant_calls"])

        return PromptContext(
            route=route,
            handler_source=raw["handler_source"],
            relevant_calls=tuple(item["call"] for item in raw["relevant_calls"]),
            dependency_snippets=tuple(dependency_snippets),
        )
    