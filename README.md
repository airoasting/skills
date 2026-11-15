# airoasting 스킬 마켓플레이스

목표부터 검증까지 한 흐름으로 잇는 열세 가지 스킬을 **명령 두 줄로 한 번에 설치**하는 Claude Code 플러그인 마켓플레이스.

- 5color (클로드 프로젝트 지침 생성)
- casting (에이전트 팀 빌더)
- council (25인 자문단)
- slide-library (형식·슬라이드 템플릿, 저장소 이름은 slide_library)
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

Codex CLI(터미널)에서 마켓플레이스를 한 번 등록합니다.

```
codex plugin marketplace add airoasting/skills
```

Codex에는 한 번에 전부 설치하는 명령이 없어 플러그인마다 한 줄씩 씁니다. 필요한 것만 골라도 됩니다.

```
codex plugin add 5color@airoasting
codex plugin add casting@airoasting
codex plugin add council@airoasting
codex plugin add slide-library@airoasting
codex plugin add korean@airoasting
codex plugin add hound@airoasting
codex plugin add strategy@airoasting
codex plugin add find-skills@airoasting
codex plugin add dart@airoasting
codex plugin add korean-law@airoasting
codex plugin add seoul-data@airoasting
codex plugin add edgar@airoasting
codex plugin add jpx@airoasting
```

설치한 뒤 Codex를 다시 켭니다. 평소처럼 요청하면 맞는 스킬이 발동합니다(예: "이 결정, 자문단 토론으로 봐 줘"). 스킬을 직접 고르려면 입력창에 `$`를 치고 목록에서 고릅니다. 목록에는 `council:council`처럼 `플러그인:스킬` 이름으로 보입니다.

- 설치 확인은 `codex plugin list`, 최신화는 `codex plugin marketplace upgrade airoasting`.
- `codex mcp list`의 Auth 열에 `Unsupported`라고 나오는 것은 정상입니다(로그인이 필요 없는 로컬 서버라는 뜻).
- 같은 스킬을 `~/.agents/skills/`나 `~/.codex/skills/`에 이미 복제해 두었다면 둘 중 하나만 남깁니다. 둘 다 있으면 목록에 두 번 나오고, 개별 저장소 README의 수동 설치(`install.sh --codex`, `codex mcp add`)까지 하면 MCP 서버도 두 벌이 됩니다.

**인증키.** Codex에는 설치할 때 값을 묻는 기능이 없어서, 키가 필요한 스킬은 환경변수로 받습니다. 아래 줄을 `~/.zshrc` 맨 끝에 붙여 넣고(`○○○○` 자리에 발급받은 키), 터미널과 Codex를 다시 켭니다.

```
export KOREAN_LAW_OC="○○○○"
export DART_API_KEY="○○○○"
```

| 스킬 | 환경변수 | 키 받는 곳 |
|---|---|---|
| korean-law | `KOREAN_LAW_OC` | [법제처 Open API](https://open.law.go.kr) (무료) |
| dart | `DART_API_KEY` | [DART 오픈API](https://opendart.fss.or.kr) (무료) |

`edgar`, `jpx`, `seoul-data`는 키 없이 시작합니다. 키가 없을 때 스킬이 `/plugin configure`나 `~/.claude/...` 경로를 안내할 수 있는데, 그것은 Claude Code용 안내입니다. Codex에서는 위 환경변수가 답입니다. `codex mcp list`는 키를 넣지 않아도 `DART_API_KEY=*****`로 표시하므로, 키가 들어갔는지는 스킬을 한 번 써 봐야 압니다.

## 구조

이 저장소(마켓플레이스)는 `.claude-plugin/marketplace.json` 하나만 있으면 됩니다. 실제 스킬 코드는 각자의 저장소(github.com/airoasting/<이름>)에 그대로 두고, 마켓플레이스는 그 저장소들을 플러그인으로 가리킵니다. 스킬은 중복 저장하지 않으며, 각 저장소가 계속 source of truth입니다.

## 게시 (관리자 절차)

### 1. 각 스킬 저장소에 plugin.json 추가

저장소 열세 개 각각에 `.claude-plugin/plugin.json` 파일 하나만 넣고 커밋합니다. 내용은 이 저장소의 `skill-repo-plugin-json/<이름>__plugin.json`에 준비해 뒀습니다. 열세 개 저장소 모두 이 단계를 마쳤습니다.

`korean-law`도 다른 스킬과 같은 구조입니다(2026-10-04 정리). 저장소 루트에 `SKILL.md`와 `.claude-plugin/plugin.json`이 있고, MCP 서버(`mcp/`)와 평가(`evals/`)는 같은 저장소의 하위 폴더에 있습니다. 이 스킬은 법제처 MCP 연결이 있어야 동작합니다. Claude Code 플러그인은 설치할 때 인증키(OC)를 묻고 MCP 서버를 함께 붙입니다. Codex 플러그인도 MCP 서버를 함께 붙이지만 인증키는 환경변수 `KOREAN_LAW_OC`로 받습니다.

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

Codex용 파일은 손으로 쓰지 않고 `scripts/codex_sync.py`가 정본에서 만듭니다(codex-cli 0.159.3에서 확인, 2026-11-15). 정본은 셋입니다.

- 스킬 저장소의 `.claude-plugin/plugin.json`(이름, 버전, 설명, MCP 서버)
- 스킬 저장소의 루트 `SKILL.md`(머리말)
- 이 저장소의 `scripts/codex_plugins.json`(Claude 매니페스트에 없는 값. MCP 서버에 넘길 환경변수와 Codex 분류)

```
python3 scripts/codex_sync.py <스킬 저장소 경로>            # 스킬 저장소에 Codex 파일을 쓴다
python3 scripts/codex_sync.py <스킬 저장소 경로> --check    # 어긋나면 종료 코드 1
python3 scripts/codex_sync.py --marketplace                 # 이 저장소의 Codex용 목록을 쓴다
python3 scripts/codex_sync.py --marketplace --check
```

스킬 저장소에 만드는 파일은 셋입니다. `.codex-plugin/plugin.json`(매니페스트), `.codex-plugin/skills/<이름>/SKILL.md`(루트 본문을 읽게 하는 진입 스킬), `codex.mcp.json`(MCP가 있을 때). 루트 `SKILL.md`와 폴더 구조는 건드리지 않으므로 `git clone → ~/.claude/skills/<이름>` 설치는 그대로 동작합니다. 이 저장소에는 `.agents/plugins/marketplace.json`을 만듭니다. Codex 문서가 항목마다 넣으라고 한 `policy`와 `category`가 여기에만 들어갑니다. 왜 이렇게 나눴는지는 스크립트 머리말에 적혀 있습니다.

언제 다시 돌리는가.

| 바꾼 것 | 돌릴 명령 |
|---|---|
| 스킬의 버전, 설명, `SKILL.md` 머리말, MCP 서버 선언 | `codex_sync.py <스킬 저장소>` 후 그 저장소에 함께 커밋 |
| MCP 서버가 읽는 환경변수가 늘었다 | `codex_plugins.json`에 적고 `codex_sync.py <스킬 저장소>` |
| 플러그인을 추가, 삭제하거나 순서를 바꿨다 | `codex_sync.py --marketplace` |

돌리지 않으면 Codex 쪽만 옛 버전과 옛 설명으로 남습니다. 버전 미러를 갱신할 때 `--check`를 같이 돌려 확인합니다.

실패 조건. 진입 스킬은 숨김 폴더(`.codex-plugin/skills/`)에 있습니다. Codex 소스 규칙상 허용되지만 공식 문서는 `.codex-plugin/` 안에 `plugin.json`만 두라고 권합니다. Codex를 올린 뒤에는 `codex plugin add` 후 `codex debug prompt-input "hi"` 출력에 스킬이 한 번씩만 보이는지 확인합니다. 안 보이면 이 가정이 깨진 것입니다.

## 파일

```
.claude-plugin/marketplace.json     ← 마켓플레이스 매니페스트 (게시 대상)
skill-repo-plugin-json/             ← 각 스킬 저장소에 넣을 plugin.json 13개 (참고용, 게시 대상 아님)
.agents/plugins/marketplace.json    ← Codex용 마켓플레이스 목록 (codex_sync.py --marketplace가 만든다)
scripts/codex_sync.py               ← Codex 플러그인 파일과 목록을 만들고 검사하는 스크립트
scripts/codex_plugins.json          ← 그 스크립트의 정본 (환경변수, Codex 분류)
README.md
```
