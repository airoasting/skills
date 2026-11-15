#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""스킬 저장소 하나에 Codex 플러그인 파일을 만들거나, 어긋났는지 확인한다.

    python3 scripts/codex_sync.py <스킬 저장소 경로>            # 파일을 쓴다
    python3 scripts/codex_sync.py <스킬 저장소 경로> --check    # 어긋나면 종료 코드 1
    python3 scripts/codex_sync.py --marketplace [--check]       # 이 저장소의 Codex용 마켓플레이스 목록

정본은 셋이다. 스킬 저장소의 `.claude-plugin/plugin.json`과 `SKILL.md`, 그리고 이 스크립트 옆의
`codex_plugins.json`(Claude 매니페스트에 없는 값: MCP 서버에 넘길 환경변수, Codex 분류).
생성물에만 있는 값은 없다. 생성물을 지우고 다시 만들어도 같은 결과가 나와야 한다.

스킬 저장소에 만드는 파일.

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

`--marketplace`는 `.claude-plugin/marketplace.json`에서 `.agents/plugins/marketplace.json`을 만든다.
Codex 문서가 항목마다 넣으라고 한 `policy`와 `category`를 여기에만 넣는다. Claude 매니페스트에
넣으면 Claude Code 검증기가 모르는 필드라고 경고한다. Codex는 두 파일이 다 있으면 `.agents` 쪽을 읽는다.
"""
from __future__ import annotations

import argparse
import json
import shutil
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent

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


def load_json(path: Path) -> dict:
    """깨진 파일은 어느 파일이 왜 깨졌는지 말하고 멈춘다."""
    try:
        return json.loads(path.read_text(encoding="utf-8-sig"))
    except FileNotFoundError:
        raise SystemExit(f"파일이 없다: {path}")
    except json.JSONDecodeError as err:
        raise SystemExit(f"JSON이 깨졌다: {path} ({err.lineno}행 {err.colno}열, {err.msg})")


def settings() -> dict:
    return load_json(HERE / "codex_plugins.json")


def dump(obj) -> str:
    return json.dumps(obj, ensure_ascii=False, indent=2) + "\n"


def frontmatter(skill_text: str) -> str:
    """'---'로 감싼 머리말을 구분선까지 포함해 그대로 돌려준다."""
    skill_text = skill_text.lstrip("\ufeff")
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


def build(repo: Path) -> dict[str, str]:
    """만들어야 할 파일의 {상대 경로: 내용}."""
    claude = load_json(repo / ".claude-plugin" / "plugin.json")
    name = claude.get("name")
    if not name:
        raise SystemExit(f"{repo}/.claude-plugin/plugin.json에 name이 없다")
    extra_env_vars = list(settings()["plugins"].get(name, {}).get("env_vars", []))
    files: dict[str, str] = {}
    manifest = {k: claude[k] for k in COPY_KEYS if k in claude}

    root_skill = repo / "SKILL.md"
    if root_skill.is_file():
        head = frontmatter(root_skill.read_text(encoding="utf-8-sig"))
        files[f"{STUB_DIR}/{name}/SKILL.md"] = head + "\n" + STUB_BODY.format(name=name)
        manifest["skills"] = f"./{STUB_DIR}/"
    elif (repo / "skills").is_dir() and any((repo / "skills").glob("*/SKILL.md")):
        manifest["skills"] = "./skills/"
    else:
        raise SystemExit(f"{repo}: SKILL.md도 skills/<이름>/SKILL.md도 없다")

    servers = claude.get("mcpServers")
    if isinstance(servers, dict) and servers:
        files["codex.mcp.json"] = dump({"mcpServers": {
            key: codex_server(value, extra_env_vars) for key, value in servers.items()
        }})
        manifest["mcpServers"] = "./codex.mcp.json"

    files[".codex-plugin/plugin.json"] = dump(manifest)
    return files


def leftovers(repo: Path, files: dict[str, str]) -> list[str]:
    """이 스크립트가 예전에 만들었지만 지금은 만들지 않는 것. 이름을 바꾸면 옛 진입 스킬이 남는다."""
    found = []
    stub_root = repo / STUB_DIR
    if stub_root.is_dir():
        keep = {Path(p).parts[2] for p in files if p.startswith(STUB_DIR + "/")}
        found += [f"{STUB_DIR}/{d.name}/" for d in sorted(stub_root.iterdir()) if d.is_dir() and d.name not in keep]
    if "codex.mcp.json" not in files and (repo / "codex.mcp.json").is_file():
        found.append("codex.mcp.json")
    return found


def build_marketplace(repo: Path) -> dict[str, str]:
    conf = settings()
    source = load_json(repo / ".claude-plugin" / "marketplace.json")
    plugins = []
    for entry in source["plugins"]:
        plugins.append({
            "name": entry["name"],
            "source": entry["source"],
            "policy": {"installation": "AVAILABLE", "authentication": "ON_INSTALL"},
            "category": conf["plugins"].get(entry["name"], {}).get("category", conf["default_category"]),
        })
    unknown = sorted(set(conf["plugins"]) - {p["name"] for p in plugins})
    if unknown:
        raise SystemExit(f"codex_plugins.json에 마켓플레이스에 없는 이름이 있다: {', '.join(unknown)}")
    return {".agents/plugins/marketplace.json": dump({
        "name": source["name"],
        "interface": {"displayName": source.get("owner", {}).get("name", source["name"])},
        "plugins": plugins,
    })}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("repo", type=Path, nargs="?", help="스킬 저장소 경로")
    parser.add_argument("--marketplace", action="store_true", help="이 저장소의 Codex용 마켓플레이스 목록을 만든다")
    parser.add_argument("--check", action="store_true", help="쓰지 않고 어긋났는지만 본다")
    args = parser.parse_args()
    if args.marketplace == bool(args.repo):
        parser.error("스킬 저장소 경로와 --marketplace 가운데 하나만 준다")

    repo = HERE.parent if args.marketplace else args.repo
    files = build_marketplace(repo) if args.marketplace else build(repo)
    stale = []
    for rel_path, content in files.items():
        path = repo / rel_path
        if path.is_file() and path.read_text(encoding="utf-8") == content:
            continue
        stale.append(rel_path)
        if not args.check:
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(content, encoding="utf-8")
    for rel_path in ([] if args.marketplace else leftovers(repo, files)):
        stale.append(rel_path + " (남은 옛 파일)")
        if not args.check:
            target = repo / rel_path
            shutil.rmtree(target) if target.is_dir() else target.unlink()
    label = repo.resolve().name
    if args.check and stale:
        print(f"{label}: 어긋남 → {', '.join(stale)}")
        return 1
    print(f"{label}: " + ("일치" if not stale else f"갱신 → {', '.join(stale)}"))
    return 0


if __name__ == "__main__":
    sys.exit(main())
