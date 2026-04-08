from pathlib import Path

from pathlib import Path
from .models import RepoProfile


SERVICE_PATTERNS = {
    "twilio": "twilio",
    "cloudinary": "cloudinary",
    "requests": "requests.",
    "webhooks": "webhook",
    "socketio": "socketio",
}


class Ingestor:
    def __init__(self, root: str | Path):
        self.root = Path(root).resolve()

    def build_profile(self) -> RepoProfile:
        
        framework = self._detect_framework()
        requirement_files = self._find_requirements_files()
        entrypoint = self._find_entrypoints()
        service_markers = self._detect_service_markers()

        return RepoProfile(
            root=str(self.root),
            framework=framework,
            entrypoints=entrypoint,
            requirement_files=requirement_files,
            test_paths=(),
            service_markers=service_markers,
        )

    
    def _detect_framework(self):
        for file_path in self.root.rglob("*.py"):
            try:
                text = file_path.read_text(encoding="utf-8")
            except OSError:
                continue

            if "from flask import Flask" in text or "Blueprint(" in text:
                return "flask"
            if "FastAPI(" in text:
                return "fastapu"
        return None
    
    def _find_requirements_files(self):
        found = []
        wanted = {"requirements.txt" , "requirements-dev.txt"}
        for path in self.root.rglob("*"):
            if not path.is_file():
                continue
            if path.name not in wanted:
                continue

            found.append(str(path.relative_to(self.root)))
        return tuple(sorted(found))
    
    def _find_entrypoints(self):
        found = []
        for path in self.root.rglob("*.py"):
            try:
                text = path.read_text(encoding = "utf-8")
            except OSError:
                continue
            if path.name in {"app.py","wsgi.py","manage.py"}:
                found.append(str(path.relative_to(self.root)))
                continue
            if "create_app(" in text or "Flask(__name__)" in text:
                found.append(str(path.relative_to(self.root)))
        return tuple(sorted(set(found)))
    def _detect_service_markers(self):
        found = set()
        for path in self.root.rglob("*.py"):
            try:
                text = path.read_text(encoding="utf-8").lower()
            except OSError:
                continue
            for marker , pattern in SERVICE_PATTERNS.items():
                if pattern.lower() in text:
                    found.add(marker)
        return tuple(sorted(found))

     
# if __name__ == "__main__":
#     profile = Ingestor("/Users/amiteshgangrade/Desktop/aahar/aahar").build_profile()
#     print(profile)
#     print(profile.to_dict())
