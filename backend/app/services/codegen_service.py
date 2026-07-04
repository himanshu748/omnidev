"""
Code Gen service — generate website/project code with Context7 docs.
Frameworks: Streamlit, React, Next.js, Node/Express, Python/FastAPI, etc.
Output is returned as bounded, safe relative files for browser preview or download.
"""

from __future__ import annotations

import json
import re
from pathlib import PurePosixPath
from typing import Any

from app.services.ai_service import AIResponseError, generate_structured
from app.services.context7_service import get_context

FRAMEWORK_CONTEXT7: dict[str, list[tuple[str, str]]] = {
    "react": [("react", "/facebook/react"), ("next.js", "/vercel/next.js")],
    "next": [("next.js", "/vercel/next.js")],
    "nextjs": [("next.js", "/vercel/next.js")],
    "streamlit": [("streamlit", "/streamlit/streamlit")],
    "node": [("express", "/expressjs/express")],
    "express": [("express", "/expressjs/express")],
    "python": [("fastapi", "/tiangolo/fastapi")],
    "fastapi": [("fastapi", "/tiangolo/fastapi")],
    "vue": [("vue", "/vuejs/core")],
    "svelte": [("svelte", "/sveltejs/svelte")],
    "astro": [("astro", "/withastro/astro")],
    "remix": [("remix", "/remix-run/remix")],
    "solid": [("solid", "/solidjs/solid")],
    "sveltekit": [("sveltekit", "/sveltejs/kit"), ("svelte", "/sveltejs/svelte")],
    "django": [("django", "/django/django")],
    "flask": [("flask", "/pallets/flask")],
    "go": [("go", "/golang/go")],
    "html": [],
}

SUPPORTED_FRAMEWORKS = set(FRAMEWORK_CONTEXT7)
MAX_PROMPT_CHARS = 4000
MAX_FILES = 40
MAX_FILE_BYTES = 200_000
MAX_TOTAL_BYTES = 1_000_000
MAX_PATH_LENGTH = 160
MAX_INSTRUCTIONS_BYTES = 20_000
BLOCKED_EXACT_PATHS = {".env", ".env.local", ".env.production", ".npmrc", ".pypirc"}
BLOCKED_PATH_PARTS = {".git", ".ssh", "node_modules", "__pycache__", ".next", "dist", "build"}
BLOCKED_FILENAMES = {
    "credentials.json",
    "id_rsa",
    "id_dsa",
    "id_ecdsa",
    "id_ed25519",
    "private.key",
    "secrets.json",
    "service-account.json",
}
BLOCKED_NPM_LIFECYCLE_SCRIPTS = {
    "preinstall",
    "install",
    "postinstall",
    "prepublish",
    "prepublishOnly",
    "prepare",
}
BLOCKED_NPM_SCRIPT_FRAGMENTS = ("|", "&", ";", "`", "$(", ">", "<", "\n", "\r")
BLOCKED_NPM_SCRIPT_PATTERNS = (
    re.compile(
        r"(^|[\s&|;])(?:bash|sh|zsh|fish|powershell|pwsh|curl|wget|nc|ncat|netcat|ssh|scp|rsync|sudo|chmod|chown|openssl)\b",
        re.IGNORECASE,
    ),
    re.compile(r"\b(?:node|python|python3|ruby|perl|php)\s+-[ce]\b", re.IGNORECASE),
    re.compile(r"\bbase64\s+(?:-d|--decode)\b", re.IGNORECASE),
)
PRIVATE_KEY_MARKERS = (
    "-----BEGIN RSA PRIVATE KEY-----",
    "-----BEGIN OPENSSH PRIVATE KEY-----",
    "-----BEGIN EC PRIVATE KEY-----",
    "-----BEGIN PRIVATE KEY-----",
)
SECRET_ASSIGNMENT_PATTERN = re.compile(
    r"\b(?:api[_-]?key|secret|token|password)\b\s*[:=]\s*[\"']?(?!your[_-]|example|placeholder|replace[_-]|changeme|xxx|<)[A-Za-z0-9_./+=-]{16,}",
    re.IGNORECASE,
)

MAX_REFINE_INSTRUCTION_CHARS = 2000
MAX_REFINE_INPUT_FILES = MAX_FILES

# Filenames that make a good "open me first" entry, in priority order. The first
# generated file whose basename matches (case-insensitive) wins; ties fall back
# to the shallowest path, then the first file.
ENTRY_FILE_PRIORITY = (
    "index.html",
    "app.tsx",
    "app.jsx",
    "app.vue",
    "app.svelte",
    "app.py",
    "main.py",
    "main.go",
    "main.ts",
    "main.tsx",
    "main.js",
    "app.js",
    "app.ts",
    "index.tsx",
    "index.jsx",
    "index.ts",
    "index.js",
    "streamlit_app.py",
    "server.py",
    "server.js",
    "readme.md",
)

PROJECT_SCHEMA: dict[str, Any] = {
    "type": "object",
    "properties": {
        "files": {
            "type": "array",
            "description": "List of project files",
            "items": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "File content"},
                },
                "required": ["path", "content"],
            },
        },
        "instructions": {
            "type": "string",
            "description": "Instructions on how to run the project",
        },
    },
    "required": ["files", "instructions"],
}


async def _fetch_docs_for_framework(framework: str, prompt: str) -> str:
    key = framework.lower().replace(" ", "")
    libs = FRAMEWORK_CONTEXT7.get(key)
    if libs is None:
        libs = [(key, f"/{key}/{key}")]
    combined = []
    for lib_name, lib_id in libs[:2]:
        try:
            ctx = await get_context(lib_id, prompt, as_text=True)
            if ctx:
                combined.append(f"--- Docs for {lib_name} ---\n{ctx[:8000]}")
        except Exception:
            pass
    return "\n\n".join(combined) if combined else ""


def _normalize_framework(framework: str) -> str:
    key = framework.lower().strip().replace(" ", "")
    if key not in SUPPORTED_FRAMEWORKS:
        allowed = ", ".join(sorted(SUPPORTED_FRAMEWORKS))
        raise ValueError(f"Unsupported framework {framework!r}. Supported frameworks: {allowed}")
    return key


def _safe_file_path(raw_path: Any) -> str:
    if not isinstance(raw_path, str):
        raise ValueError("Generated file path must be a string")
    path = raw_path.strip()
    if not path or len(path) > MAX_PATH_LENGTH:
        raise ValueError(f"Unsafe generated file path: {raw_path!r}")
    if "\\" in path or "\x00" in path or path.startswith(("/", "~")):
        raise ValueError(f"Unsafe generated file path: {raw_path!r}")

    normalized = PurePosixPath(path)
    parts = normalized.parts
    if not parts or any(part in {"", ".", ".."} for part in parts):
        raise ValueError(f"Unsafe generated file path: {raw_path!r}")
    lowered_parts = {part.lower() for part in parts}
    lowered_path = normalized.as_posix().lower()
    if lowered_path in BLOCKED_EXACT_PATHS:
        raise ValueError(f"Blocked generated file path: {raw_path!r}")
    if parts[-1].lower() in BLOCKED_EXACT_PATHS:
        raise ValueError(f"Blocked generated file path: {raw_path!r}")
    if lowered_parts & BLOCKED_PATH_PARTS:
        raise ValueError(f"Blocked generated file path: {raw_path!r}")
    if parts[-1].lower() in BLOCKED_FILENAMES:
        raise ValueError(f"Blocked generated file path: {raw_path!r}")
    return normalized.as_posix()


def _sanitize_file_entries(files: Any) -> list[dict[str, str]]:
    if not isinstance(files, list):
        raise ValueError("Generated files must be a list")
    if len(files) > MAX_FILES:
        raise ValueError(f"Generated project exceeds the maximum allowed file count of {MAX_FILES}")

    sanitized: list[dict[str, str]] = []
    seen: set[str] = set()
    total_bytes = 0

    for item in files:
        if not isinstance(item, dict):
            raise ValueError("Each generated file entry must be an object")
        path = _safe_file_path(item.get("path"))
        content = item.get("content")
        if not isinstance(content, str):
            raise ValueError(f"Generated content for {path!r} must be a string")
        path_key = path.casefold()
        if path_key in seen:
            raise ValueError(f"Generated project includes duplicate file path {path!r}")
        if any(marker in content for marker in PRIVATE_KEY_MARKERS):
            raise ValueError(f"Generated content for {path!r} includes a private-key block")
        if SECRET_ASSIGNMENT_PATTERN.search(content):
            raise ValueError(f"Generated content for {path!r} appears to include a hard-coded secret")
        if PurePosixPath(path).parts[-1].lower() == "package.json":
            _validate_package_json(content)

        content_bytes = len(content.encode("utf-8"))
        if content_bytes > MAX_FILE_BYTES:
            raise ValueError(f"Generated file {path!r} exceeds {MAX_FILE_BYTES} bytes")
        if total_bytes + content_bytes > MAX_TOTAL_BYTES:
            raise ValueError("Generated project exceeds the maximum allowed output size")

        seen.add(path_key)
        total_bytes += content_bytes
        sanitized.append({"path": path, "content": content})

    if not sanitized:
        raise ValueError("Generated project did not include any safe files")
    return sanitized


def _validate_package_json(content: str) -> None:
    try:
        package = json.loads(content)
    except json.JSONDecodeError as exc:
        raise ValueError("Generated package.json is not valid JSON") from exc
    scripts = package.get("scripts", {})
    if not isinstance(scripts, dict):
        raise ValueError("Generated package.json scripts field must be an object")
    blocked = sorted(BLOCKED_NPM_LIFECYCLE_SCRIPTS & set(scripts))
    if blocked:
        blocked_list = ", ".join(blocked)
        raise ValueError(f"Generated package.json includes blocked npm lifecycle script(s): {blocked_list}")
    for name, command in scripts.items():
        if not isinstance(command, str):
            raise ValueError(f"Generated package.json script {name!r} must be a string")
        if any(fragment in command for fragment in BLOCKED_NPM_SCRIPT_FRAGMENTS) or any(
            pattern.search(command) for pattern in BLOCKED_NPM_SCRIPT_PATTERNS
        ):
            raise ValueError(f"Generated package.json script {name!r} contains a blocked shell command")


def _safe_failure_project(message: str) -> dict[str, Any]:
    return {
        "files": [
            {
                "path": "README.md",
                "content": (
                    "# Code generation did not return valid project files\n\n"
                    f"{message}\n\n"
                    "Try again with a narrower prompt. OmniDev did not execute or expose the raw model output."
                ),
            }
        ],
        "instructions": "Try generation again with a narrower prompt.",
        "summary": "Generation did not return a valid project.",
        "entry": "README.md",
    }


def _safe_instructions(value: Any) -> str:
    if not isinstance(value, str) or not value.strip():
        return "Review the generated files, install dependencies in an isolated directory, then run the usual command for the framework."
    if any(marker in value for marker in PRIVATE_KEY_MARKERS) or SECRET_ASSIGNMENT_PATTERN.search(value):
        return "Review the generated files, install dependencies in an isolated directory, then run the usual command for the framework."
    encoded = value.encode("utf-8")
    if len(encoded) <= MAX_INSTRUCTIONS_BYTES:
        return value
    return encoded[:MAX_INSTRUCTIONS_BYTES].decode("utf-8", errors="ignore") + "\n\n[Instructions truncated]"


def _detect_entry_file(files: list[dict[str, str]]) -> str:
    """Pick the file a user should open first. Never raises; always returns a path."""
    if not files:
        return ""
    by_basename: dict[str, list[dict[str, str]]] = {}
    for entry in files:
        basename = PurePosixPath(entry["path"]).name.lower()
        by_basename.setdefault(basename, []).append(entry)
    for candidate in ENTRY_FILE_PRIORITY:
        matches = by_basename.get(candidate)
        if matches:
            # Prefer the shallowest match (fewest path segments) for the entry.
            return min(matches, key=lambda e: len(PurePosixPath(e["path"]).parts))["path"]
    return files[0]["path"]


def _build_summary(files: list[dict[str, str]], framework_key: str) -> str:
    count = len(files)
    noun = "file" if count == 1 else "files"
    return f"Generated a {framework_key} project with {count} {noun}."


async def generate_project(prompt: str, framework: str) -> dict[str, Any]:
    """
    Generate a full project (multiple files) for the given prompt and framework.
    Uses Context7 docs when CONTEXT7_API_KEY is set.
    """
    if len(prompt) > MAX_PROMPT_CHARS:
        raise ValueError(
            f"Prompt is too long ({len(prompt)} chars). Maximum allowed is {MAX_PROMPT_CHARS} characters."
        )
    framework_key = _normalize_framework(framework)
    docs_block = await _fetch_docs_for_framework(framework_key, prompt)
    system = """You are an expert full-stack developer. Generate a complete, runnable project based on the user's request and the framework they chose.

Rules:
- Create all necessary files (package.json, main entry, components, etc.) for the chosen framework.
- ALWAYS include a .gitignore file appropriate for the framework (node_modules, .env, dist, __pycache__, etc.) so the project is Git-ready.
- Return only safe relative project file paths. Never use absolute paths, parent directory segments, backslashes, .env files, SSH keys, node_modules, build artifacts, or secret-bearing files.
- Do not include real credentials, tokens, private keys, or executable install hooks that fetch unknown remote scripts.
- If the user's request suggests a hero section, landing page, or background imagery, include a placeholder (e.g. CSS gradient, commented image tag, or a simple SVG/placeholder) that they can replace later.
- Use the provided documentation excerpts when present to follow best practices and correct APIs.
- Return the result by calling the return_project tool. Do not answer in plain text."""

    user = f"Framework: {framework_key}\n\nUser request: {prompt}\n\n"
    if docs_block:
        user += f"Relevant documentation (use for correct APIs and patterns):\n\n{docs_block}\n\n"
    user += "Generate the project now."

    try:
        data = await generate_structured(
            user,
            system=system,
            schema=PROJECT_SCHEMA,
            tool_name="return_project",
            tool_description="Return the generated project files and run instructions.",
            max_tokens=8192,
        )
    except AIResponseError:
        return _safe_failure_project("The model returned text that could not be parsed as a project payload.")
    if not isinstance(data, dict):
        return _safe_failure_project("The model returned an unexpected payload shape.")
    files = _sanitize_file_entries(data.get("files") or [])
    instructions = _safe_instructions(data.get("instructions"))
    instructions = (
        f"{instructions}\n\n"
        "Safety: OmniDev does not execute generated code on the backend. "
        "Review files first; web previews run in StackBlitz, and downloads contain only validated relative paths."
    )
    return {
        "files": files,
        "instructions": instructions,
        "summary": _build_summary(files, framework_key),
        "entry": _detect_entry_file(files),
    }


def _validate_refine_input_files(files: Any) -> list[dict[str, str]]:
    """Validate the caller-supplied existing file set before refining it.

    Reuses the same sanitizer/safety sets as generation so a client cannot smuggle
    unsafe paths or secret-bearing content back in through the refine loop.
    """
    if not isinstance(files, list) or not files:
        raise ValueError("Refine requires the existing project files")
    if len(files) > MAX_REFINE_INPUT_FILES:
        raise ValueError(f"Refine input exceeds the maximum allowed file count of {MAX_REFINE_INPUT_FILES}")
    return _sanitize_file_entries(files)


async def refine_project(
    files: Any, instruction: str, framework: str = "react"
) -> dict[str, Any]:
    """
    Iterate on an existing generated project: apply a natural-language instruction
    (e.g. "add auth", "convert to TypeScript") and return the modified file set.
    Runs the SAME validation/sanitization as generate on both input and output.
    """
    if not isinstance(instruction, str) or not instruction.strip():
        raise ValueError("Refine instruction must not be empty")
    if len(instruction) > MAX_REFINE_INSTRUCTION_CHARS:
        raise ValueError(
            f"Refine instruction is too long ({len(instruction)} chars). "
            f"Maximum allowed is {MAX_REFINE_INSTRUCTION_CHARS} characters."
        )
    framework_key = _normalize_framework(framework)
    existing = _validate_refine_input_files(files)
    docs_block = await _fetch_docs_for_framework(framework_key, instruction)

    system = """You are an expert full-stack developer refining an existing project. Apply the user's instruction to the provided files and return the COMPLETE updated project.

Rules:
- Return the full file set after your changes, not just a diff. Include every file that should exist in the refined project (keep unchanged files as-is, add new files, and drop files only when the instruction clearly requires it).
- Preserve the framework and keep the project runnable.
- Return only safe relative project file paths. Never use absolute paths, parent directory segments, backslashes, .env files, SSH keys, node_modules, build artifacts, or secret-bearing files.
- Do not include real credentials, tokens, private keys, or executable install hooks that fetch unknown remote scripts.
- Use the provided documentation excerpts when present to follow best practices and correct APIs.
- Return the result by calling the return_project tool. Do not answer in plain text."""

    existing_block = "\n\n".join(
        f"--- {entry['path']} ---\n{entry['content']}" for entry in existing
    )
    user = (
        f"Framework: {framework_key}\n\n"
        f"Refine instruction: {instruction}\n\n"
        f"Existing project files:\n\n{existing_block}\n\n"
    )
    if docs_block:
        user += f"Relevant documentation (use for correct APIs and patterns):\n\n{docs_block}\n\n"
    user += "Return the complete refined project now."

    try:
        data = await generate_structured(
            user,
            system=system,
            schema=PROJECT_SCHEMA,
            tool_name="return_project",
            tool_description="Return the refined project files and run instructions.",
            max_tokens=8192,
        )
    except AIResponseError:
        return _safe_failure_project("The model returned text that could not be parsed as a project payload.")
    if not isinstance(data, dict):
        return _safe_failure_project("The model returned an unexpected payload shape.")
    refined = _sanitize_file_entries(data.get("files") or [])
    instructions = _safe_instructions(data.get("instructions"))
    instructions = (
        f"{instructions}\n\n"
        "Safety: OmniDev does not execute generated code on the backend. "
        "Review files first; web previews run in StackBlitz, and downloads contain only validated relative paths."
    )
    return {
        "files": refined,
        "instructions": instructions,
        "summary": _build_summary(refined, framework_key),
        "entry": _detect_entry_file(refined),
    }
