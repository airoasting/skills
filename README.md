# airoasting 스킬 마켓플레이스

목표부터 검증까지 한 흐름으로 잇는 열세 가지 스킬을 **명령 두 줄로 한 번에 설치**하는 Claude Code 플러그인 마켓플레이스.

- 5color (클로드 프로젝트 지침 생성)
- casting (에이전트 팀 빌더)
- council (25인 자문단)
- slide_library (형식·슬라이드 템플릿)
- korean (한국어 윤문)
- hound (16개 채널 추적 검색)
- strategy (컨설팅 전략 프레임워크)
- find-skills (스킬 탐색·검증·설치)
- dart (DART 공시 리포트·조회)
- korean-law (법률 인용 검증 게이트)
- seoul-data (서울 공공데이터 실시간 조회·집계)
- edgar (미국 SEC 공시 조회)
- jpx (일본 상장사 결산단신 조회)

## 설치 (사용자)

Claude Code(터미널)에서:

```
/plugin marketplace add airoasting/skills
/plugin install @airoasting
```

- 첫 줄: 이 마켓플레이스를 등록합니다(저장소 이름은 아래 "게시"에서 정한 곳으로 바꿉니다).
- 둘째 줄: 마켓플레이스의 열세 개 플러그인을 전부 설치합니다.

하나만 설치하려면 `/plugin install casting@airoasting` 처럼 씁니다.
설치 확인은 `/plugin list`, 최신화는 `/plugin marketplace update airoasting`.

### Codex에서 설치

Codex CLI(터미널)에서:

```
codex plugin marketplace add airoasting/skills
codex plugin add casting@airoasting
```

Codex는 한 번에 전부 설치하는 명령이 없어 플러그인마다 `codex plugin add <이름>@airoasting`을 씁니다. 설치 확인은 `codex plugin list`, 최신화는 `codex plugin marketplace upgrade airoasting`.

MCP 서버가 붙은 스킬은 인증키를 환경변수로 받습니다(Codex에는 설치할 때 값을 묻는 기능이 없습니다). `korean-law`는 `KOREAN_LAW_OC`, `dart`는 `DART_API_KEY`를 셸에 넣어 둡니다. `edgar`, `jpx`, `seoul-data`는 키 없이 시작합니다.

## 구조

이 저장소(마켓플레이스)는 `.claude-plugin/marketplace.json` 하나만 있으면 됩니다. 실제 스킬 코드는 각자의 저장소(github.com/airoasting/<이름>)에 그대로 두고, 마켓플레이스는 그 저장소들을 플러그인으로 가리킵니다. 스킬은 중복 저장하지 않으며, 각 저장소가 계속 source of truth입니다.

## 게시 (관리자 절차)

### 1. 각 스킬 저장소에 plugin.json 추가

저장소 열세 개 각각에 `.claude-plugin/plugin.json` 파일 하나만 넣고 커밋합니다. 내용은 이 저장소의 `skill-repo-plugin-json/<이름>__plugin.json`에 준비해 뒀습니다. 열세 개 저장소 모두 이 단계를 마쳤습니다.

`korean-law`도 다른 스킬과 같은 구조입니다(2026-10-04 정리). 저장소 루트에 `SKILL.md`와 `.claude-plugin/plugin.json`이 있고, MCP 서버(`mcp/`)와 평가(`evals/`)는 같은 저장소의 하위 폴더에 있습니다. 다만 이 스킬은 법제처 MCP 연결이 있어야 동작합니다. 플러그인 설치는 스킬만 넣으므로, MCP 서버 연결과 인증키(OC)는 korean-law 저장소 README의 설치 절차를 따로 따릅니다.

`seoul-data`는 `dart`와 같은 구조입니다(2026-11-15 추가). 플러그인을 설치하면 MCP 서버가 함께 붙고, 인증키가 없어도 체험 모드로 동작합니다. 무료 인증키는 seoul-data 저장소 README의 절차로 넣습니다.

예: `airoasting/casting` 저장소에

```
casting/
└── .claude-plugin/
    └── plugin.json     ← skill-repo-plugin-json/casting__plugin.json 내용
```

`SKILL.md`는 지금처럼 저장소 루트에 그대로 둡니다(단일 스킬 플러그인은 루트 SKILL.md를 인식합니다. 기존 `git clone → ~/.claude/skills/<이름>` 방식도 그대로 동작합니다).

### 2. 마켓플레이스 저장소 게시

이 폴더(`.claude-plugin/marketplace.json` 포함)를 새 저장소로 올립니다. 권장 이름은 `airoasting/skills`입니다(원하면 기존 `airoasting/skill_library`에 `.claude-plugin/marketplace.json`만 추가해 그 저장소를 마켓플레이스로 써도 됩니다. 그 경우 설치 첫 줄은 `/plugin marketplace add airoasting/skill_library`).

```
git init
git add .
git commit -m "airoasting skills marketplace"
git remote add origin https://github.com/airoasting/skills.git
git push -u origin main
```

### 3. 검증

게시 후 실제로 `/plugin marketplace add airoasting/skills` → `/plugin install @airoasting`를 한 번 돌려 열세 가지 스킬이 다 뜨는지 확인합니다. 만약 특정 스킬이 로드되지 않으면, 그 저장소의 `SKILL.md`를 `skills/<이름>/SKILL.md`로 옮기고 plugin.json은 그대로 두면 됩니다(다중 스킬 표준 레이아웃).

### 4. Codex 플러그인 파일 동기화

Codex는 같은 `.claude-plugin/marketplace.json`을 읽지만, 스킬 저장소 쪽에는 Codex용 파일이 따로 있어야 스킬과 MCP가 잡힙니다(codex-cli 0.159.3에서 확인, 2026-11-15). 그 파일은 손으로 쓰지 않고 `scripts/codex_sync.py`가 정본(`.claude-plugin/plugin.json`, 루트 `SKILL.md`)에서 만듭니다.

```
python3 scripts/codex_sync.py <스킬 저장소 경로>            # 파일을 쓴다
python3 scripts/codex_sync.py <스킬 저장소 경로> --check    # 어긋나면 종료 코드 1
```

만드는 파일은 셋입니다. `.codex-plugin/plugin.json`(매니페스트), `.codex-plugin/skills/<이름>/SKILL.md`(루트 본문을 읽게 하는 진입 스킬), `codex.mcp.json`(MCP가 있을 때). 루트 `SKILL.md`와 폴더 구조는 건드리지 않으므로 `git clone → ~/.claude/skills/<이름>` 설치는 그대로 동작합니다. 왜 이렇게 나눴는지는 스크립트 머리말에 적혀 있습니다.

**버전이나 스킬 설명(`SKILL.md` 머리말)을 바꿀 때마다 이 스크립트를 다시 돌리고 함께 커밋합니다.** 돌리지 않으면 Codex 쪽만 옛 버전과 옛 설명으로 남습니다. MCP 서버에 넘길 환경변수가 늘면 `--env-var 이름`을 붙여 한 번 돌리면 되고, 이후에는 `codex.mcp.json`에 남아 유지됩니다.

실패 조건. Codex가 숨김 폴더 아래 스킬을 읽지 않게 바뀌면 진입 스킬이 사라집니다. Codex를 올린 뒤 `codex plugin add` 후 스킬이 안 보이면 이 가정부터 확인합니다.

## 파일

```
.claude-plugin/marketplace.json     ← 마켓플레이스 매니페스트 (게시 대상)
skill-repo-plugin-json/             ← 각 스킬 저장소에 넣을 plugin.json 13개 (참고용, 게시 대상 아님)
scripts/codex_sync.py               ← 스킬 저장소에 Codex 플러그인 파일을 만들고 검사하는 스크립트
README.md
```
