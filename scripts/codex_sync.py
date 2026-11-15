#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""스킬 저장소 하나에 Codex 플러그인 파일을 만들거나, 어긋났는지 확인한다.

    python3 scripts/codex_sync.py <스킬 저장소 경로>            # 파일을 쓴다
    python3 scripts/codex_sync.py <스킬 저장소 경로> --check    # 어긋나면 종료 코드 1
    python3 scripts/codex_sync.py <경로> --env-var DART_API_KEY  # MCP 서버에 넘길 환경변수 추가

정본은 `.claude-plugin/plugin.json`과 `SKILL.md`다. 이 스크립트는 그 둘에서 아래 파일을 만든다.

    .codex-plugin/plugin.json                 Codex 매니페스트 (이름, 버전, 설명은 정본과 같다)
    .codex-plugin/skills/<이름>/SKILL.md      Codex 진입 스킬 (루트 SKILL.md가 있을 때만)
    codex.mcp.json                            Codex용 MCP 선언 (mcpServers가 있을 때만)

왜 따로 만드는가 (codex-cli 0.159.3에서 확인, 2026-11-15).
- Codex는 플러그인 루트의 SKILL.md를 스킬로 잡지 않는다. 스킬 폴더 아래 `<이름>/SKILL.md`만 잡는다.
- 루트 SKILL.md를 옮기면 `git clone → ~/.claude/skills/<이름>` 설치와 본문의 상대 경로가 깨진다.
  그래서 루트는 그대로 두고, 머리말만 같은 진입 스킬이 루트 본문을 읽게 한다.
- 진입 스킬을 숨김 폴더(.codex-plugin) 아래에 두는 이유. 일반 폴더에 두면 저장소를 통째로
  `~/.agents/skills/`에 복제해 쓰는 사람에게 같은 스킬이 두 번 잡힌다.
- Codex는 Claude 형식 매니페스트의 `${CLAUDE_PLUGIN_ROOT}`를 풀지 않는다. 그래서 MCP는
  `cwd`를 플러그인 루트로 두고 상대 경로로 띄운다. `${user_config.*}`도 없으므로 그 값은
  `env_vars`(사용자 셸의 환경변수를 넘겨받는 목록)로 바꾼다.

스킬 본문이 이미 `skills/<이름>/SKILL.md`에 있는 저장소(seoul-data)는 진입 스킬 없이 그 폴더를 가리킨다.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT_VAR = "${CLAUDE_PLUGIN_ROOT}"
COPY_KEYS = ("name", "description", "version", "author", "homepage", "repository", "license", "keywords")
STUB_DIR = ".codex-plugin/skills"

STUB_BODY = """
# {name} (Codex 진입점)

이 파일은 Codex 플러그인용 진입점이다. 스킬 본문은 플러그인 루트의 `SKILL.md`에 있다.

1. 이 파일 기준 `../../../SKILL.md`를 처음부터 끝까지 읽고, 그 지침을 그대로 따른다.
2. 본문에 나오는 상대 경로(`references/`, `scripts/`, `assets/` 등)는 모두 플러그인 루트 기준이다. 플러그인 루트는 이 파일에서 세 단계 위 폴더다.

이 파일은 `codex_sync.py`가 만든다. 손으로 고치지 않는다. 머리말은 루트 `SKILL.md`와 같아야 한다.
"""


def dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def frontmatter(skill_text: str) -> str:
    """'---'로 감싼 머리말을 구분선까지 포함해 그대로 돌려준다."""
    if not skill_text.startswith("---"):
        raise SystemExit("SKILL.md가 머리말(---)로 시작하지 않는다")
    end = skill_text.find("\n---", 3)
    if end < 0:
        raise SystemExit("SKILL.md 머리말이 닫히지 않았다")
    return skill_text[: end + 4]


def codex_server(server: dict, extra_env_vars: list[str]) -> dict:
    """Claude 형식 MCP 서버 선언 하나를 Codex 형식으로 바꾼다."""
    def rel(value: str) -> str:
        if value.startswith(ROOT_VAR + "/"):
            return value[len(ROOT_VAR) + 1:]
        if ROOT_VAR in value:
            raise SystemExit(f"경로 중간에 있는 {ROOT_VAR}는 바꿀 수 없다: {value}")
        return value

    out: dict = {"command": rel(server["command"]), "args": [rel(a) for a in server.get("args", [])], "cwd": "."}
    env, env_vars = {}, []
    for key, value in (server.get("env") or {}).items():
        if isinstance(value, str) and "${user_config." in value:
            env_vars.append(key)            # 설치 때 묻는 값은 Codex에 없다. 환경변수로 받는다
        else:
            env[key] = rel(value) if isinstance(value, str) else value
    for name in extra_env_vars:
        if name not in env_vars:
            env_vars.append(name)
    if env:
        out["env"] = env
    if env_vars:
        out["env_vars"] = env_vars
    return out


def build(repo: Path, extra_env_vars: list[str]) -> dict[str, str]:
    """만들어야 할 파일의 {상대 경로: 내용}."""
    claude = json.loads((repo / ".claude-plugin" / "plugin.json").read_text(encoding="utf-8"))
    name = claude["name"]
    files: dict[str, str] = {}
    manifest = {k: claude[k] for k in COPY_KEYS if k in claude}

    root_skill = repo / "SKILL.md"
    if root_skill.is_file():
        head = frontmatter(root_skill.read_text(encoding="utf-8"))
        files[f"{STUB_DIR}/{name}/SKILL.md"] = head + "\n" + STUB_BODY.format(name=name)
        manifest["skills"] = f"./{STUB_DIR}/"
    elif (repo / "skills").is_dir() and any((repo / "skills").glob("*/SKILL.md")):
        manifest["skills"] = "./skills/"
    else:
        raise SystemExit(f"{repo}: SKILL.md도 skills/<이름>/SKILL.md도 없다")

    servers = claude.get("mcpServers")
    if isinstance(servers, dict) and servers:
        existing = repo / "codex.mcp.json"
        kept: dict[str, list[str]] = {}
        if existing.is_file():                 # 손으로 넣은 env_vars는 다시 만들어도 남긴다
            for key, value in json.loads(existing.read_text(encoding="utf-8")).get("mcpServers", {}).items():
                kept[key] = list(value.get("env_vars", []))
        files["codex.mcp.json"] = dump({"mcpServers": {
            key: codex_server(value, kept.get(key, []) + extra_env_vars) for key, value in servers.items()
        }})
        manifest["mcpServers"] = "./codex.mcp.json"

    files[".codex-plugin/plugin.json"] = dump(manifest)
    return files


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo", type=Path)
    parser.add_argument("--check", action="store_true", help="쓰지 않고 어긋났는지만 본다")
    parser.add_argument("--env-var", action="append", default=[], metavar="NAME",
                        help="MCP 서버에 넘길 환경변수 이름 (여러 번 쓸 수 있다)")
    args = parser.parse_args()

    files = build(args.repo, args.env_var)
    stale = []
    for rel_path, content in files.items():
        path = args.repo / rel_path
        if path.is_file() and path.read_text(encoding="utf-8") == content:
            continue
        stale.append(rel_path)
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    label = args.repo.resolve().name
    if args.check and stale:
        print(f"{label}: 어긋남 → {', '.join(stale)}")
        return 1
    print(f"{label}: " + ("일치" if not stale else f"갱신 → {', '.join(stale)}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
