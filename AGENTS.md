# AGENTS.md — 이 저장소에서 일하는 AI 에이전트(Claude Code 등)용 규칙

## 이 저장소가 하는 일
사용자(Snow)가 준 주제·사진으로 **인스타 릴스 · 스레드 · 유튜브 쇼츠**를 만들어 게시한다. 일회성, 수동 실행.
- 네이버 블로그(경제주막, 경제 카테고리)와 네이버 클립 발행은 이 저장소 밖에서 **Uplika**로 한다.
- 전체 절차: `skills/oneoff-publish/SKILL.md` / 지금까지의 경과: `WORKLOG.md`

## 절대 규칙
1. **카드뉴스봇(`superabba/my-site`)을 건드리지 않는다.** `cardbot-data` 브랜치, `data/cardbot.db`,
   `cardnews.yml`을 읽거나 쓰지 않는다. 예외는 `my-site/.github/workflows/oneoff-secrets-sync.yml`
   (게시 계정 시크릿을 이 저장소로 복사하는 전용 워크플로) 하나.
   - 이유: 카드뉴스봇은 "오늘 DB에 게시 기록이 있으면 정기 실행(매일 15:05 KST)을 건너뛴다". 일회성 게시가
     그 DB에 섞이면 정기 루틴이 멈춘다. 이 저장소를 따로 만든 이유가 이것이다.
2. 이 저장소에 예약 실행(`schedule`)을 넣지 않는다. 사람이 요청할 때만 돈다.
3. 사실이 아닌 내용을 원고에 넣지 않는다. 사진·사용자 말·확인한 공식 페이지에 있는 것만 쓴다.
   확인 못 한 것은 "확인하지 못함", 직접 계산한 숫자는 "제 계산"으로 표시한다.
4. 게시 전에 `python -m oneoff preview`로 만든 미리보기를 **직접 눈으로** 확인한다.
5. 같은 게시물을 두 번 올리지 않는다. `published.json`의 `posts`에 있는 플랫폼은 코드가 자동으로 건너뛴다 —
   이 파일을 손으로 지우지 말 것.
6. 계정을 헷갈리지 않는다. 경제주막 콘텐츠는 **경제주막 계정에만** 올린다.
   Uplika `superabba`(슈퍼아빠) 워크스페이스의 채널(인스타 super_abba_, 네이버 클립 '스노우볼23' 등)에 올리지 않는다.
7. 광고·협찬(대가성)은 기본 **없음**. 사용자가 있다고 말할 때만 블로그·캡션 맨 앞과 클립 `adDisclosure`에 표기.

## 계정·고정값
| 항목 | 값 |
|---|---|
| Uplika 워크스페이스 (경제주막) | `ws_3a45040ee5856407` (economypub) |
| 네이버 블로그 | `conn_4229412d79bc99ce`, 경제 카테고리 `categoryId "2"` |
| 네이버 클립 (경제주막) | `conn_efdce3d2f5b04bc8` (handle `economypub`, 프로필 이름 '경제주모' — 오타 아님), 특가·할인은 `categoryId "163"` (쇼핑 › 할인정보) |
| 인스타·스레드·유튜브 (이 저장소 게시용) | GitHub Secrets (카드뉴스봇 값 복사) |
| 네이버 발행 브라우저 | 사용자 PC의 Edge + Uplika 확장. 꺼져 있으면 대기열(최대 7일) |

## 브랜치
- `main`: 코드·문서만. 게시물을 커밋하지 않는다 (`.gitignore`에 `posts/`).
- `data`: `posts/<id>/`(원고·사진·결과물·published.json), `media/`(공개 호스팅용, 자동), `log.jsonl`.

## 코드 지도
| 파일 | 역할 |
|---|---|
| `oneoff/spec.py` | `spec.json` 읽기·검사 (글자 수, 사진 존재, 블록 형식) |
| `oneoff/render.py` | 블록(label·headline·text·photo·card·pill·spacer) 배치 → 1080x1920 장면 / 1080x1350 슬라이드 |
| `oneoff/video.py` | 등장 애니메이션·줌·진행 바 → 장면별 mp4 → concat → 배경음악 |
| `oneoff/bgm.py` | 분위기별 배경음악 합성 (calm·warm·bright·upbeat·tense, auto는 원고 단어로 선택). calm은 `music.py` 그대로 |
| `oneoff/publish.py` | 게시 (DB 없이 `published.json`·`log.jsonl`에 기록) |
| `oneoff/publishers.py`, `youtube.py`, `hosting.py`, `music.py` | 카드뉴스봇에서 **그대로 복사** (원본 `my-site/cardnews-bot/cardbot/`) |
| `.github/workflows/publish.yml` | 수동 실행: `post`, `action`(publish/render/render-publish), `platforms` |

## 코드 규칙
- 복사해 온 4개 파일은 카드뉴스봇 쪽에서 API 대응이 바뀌면 같이 맞춘다.
- 렌더 스타일을 바꾸면 `examples/joym-5500`으로 `preview`를 다시 만들어 보고 `pytest`를 돌린다.
- 영상: 30fps, 장면별 mp4 → concat `-c copy` → 음원 `-c:v copy`. 장면 파일은 `.part.mp4`로 쓰고 성공 시 이름 변경.
- 배경음악 분위기를 추가·수정하면 ffmpeg `ebur128`로 재서 다른 분위기와 체감 음량(약 −16 LUFS)을 맞춘다 (`bgm.py`의 `level`).
- 커밋 메시지·주석·문서는 한국어.

## 이 세션 환경에서 막혀 있는 것 (클라우드 Claude 기준)
- GitHub 저장소 생성, Actions 시크릿·변수 API → 사용자 PC의 Claude Code나 GitHub 화면에서 한다.
- 네이버 클립 크리에이터(clipcreators.naver.com)는 내장 브라우저에서 열리지 않는다 → 클립 수정·삭제는 사용자가 직접.

## 테스트
```bash
pip install -r requirements.txt pytest
python -m pytest -q tests
```
