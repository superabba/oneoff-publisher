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
   확인 못 한 것은 글에 넣지 않고(블로그에 '확인하지 못한 것' 절을 적지 않는다, 사용자 요청 2026-11-02) 사용자에게 보고할 때만 알린다.
   직접 계산한 숫자는 "제 계산"으로 표시한다.
4. 게시 전에 `python -m oneoff preview`로 만든 미리보기를 **직접 눈으로** 확인한다.
5. 같은 게시물을 두 번 올리지 않는다. `published.json`의 `posts`에 있는 플랫폼은 코드가 자동으로 건너뛴다 —
   이 파일을 손으로 지우지 말 것.
6. 계정을 헷갈리지 않는다. 경제주막 콘텐츠는 **경제주막 계정에만** 올린다.
   Uplika `superabba`(슈퍼아빠) 워크스페이스의 채널(인스타 super_abba_, 네이버 클립 '스노우볼23' 등)에 올리지 않는다.
8. 숏폼 영상·슬라이드 디자인은 **사용자가 준 행사 사진의 이미지와 같거나 비슷하게** 만든다 (사용자 요청, 2026-11-01).
   배경색·글자색·큰 숫자 글꼴·사진 속 상품/카드 이미지를 따르고, 노랑·검정·빨강 기본 테마(`theme`)는 사진에 맞는 색이 없을 때만 쓴다.
   사진을 보고 `spec.json`의 `theme`(bg·ink·accent·card)와 `photo` 블록을 사진 분위기에 맞춘다.
9. 블로그 글 맨 끝에는 사용자가 준 **사진 원본**(자르지 않은 것)을 전부 넣는다 (사용자 요청, 2026-11-02).
   원본은 받은 파일을 **다시 저장하지 않고 그대로 복사**해 넣고(화질 유지), 한 줄 정리 바로 다음에 설명 문구 없이 사진만 둔다.
   사진은 **문서 너비**(`{.fit}`)로 넣는다 (사용자 요청, 2026-11-04).
   세로 4,000px 넘는 긴 원본은 `tools/slice_original.py`로 이어지는 PNG 조각으로 나눠 붙여 넣는다 (네이버가 긴 JPEG를 1,600px로 줄이기 때문, 사용자 선택 2026-11-05).
10. 사진에 캐릭터·상품·카드·키비주얼 같은 **상징적인 이미지**가 있으면 잘라 내서 영상(첫·마지막 장면)과 블로그에 같이 쓴다.
    글자 캡처만 쓰지 않는다 (사용자 요청, 2026-11-02).
11. 글 말투는 **글쓴이가 내용을 다 알고 독자에게 설명하는 식**으로 쓴다. "안내 화면에 적혀 있어요"처럼 사진을 설명하는 말투는 쓰지 않는다
    (사용자 요청, 2026-11-04). 규칙 3(사진에 있는 사실만)은 그대로다.
12. 글자 위주 캡처는 **구간별로 잘라 블로그 본문의 해당 위치에 넣고**, 통짜 원본은 글 맨 끝에 둔다 (사용자 요청, 2026-11-05).
    원본은 원래 해상도로 연다 (대화창 사진은 세로 2,000px로 줄어드니 긴 캡처는 구글드라이브로 받는다). 상세 방법은 스킬 2단계.
14. 사진 없는 정보성 주제는 `tools/illustrate.py`로 그린 일러스트 3장을 블로그에 넣는다 (인터넷 검색·API 없음). 그림 속 글자도 확인된 사실만 쓴다 (사용자 결정 2026-11-09, 스킬 2단계).
15. 사진 없이 글만 받으면 주제에 맞는 스타일(`iso` 등각·`swiss` 스위스·`riso` 리소그래프, lemo-opuscar)을 하나 골라 `tools/make_pictures.py`로 그림 3장을 만들어 블로그에 넣고, 영상의 `theme`·첫 장면 그림도 같은 스타일로 맞춘다 (사용자 결정 2026-11-10, 스킬 2단계). 그림 속 글자도 확인된 사실만.
13. 사용자가 사진 없이 글만 줘도 블로그에는 사진을 넣는다. 영상 렌더 결과(`slide_*.jpg`, `reel_cover.jpg`)를 쓰고, 인터넷에서 사진을 검색해 넣지 않는다 (사용자 요청 2026-11-09, 스킬 2단계).
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
| `oneoff/bgm.py` | 분위기별 배경음악 (calm·warm·bright·upbeat·tense, auto는 원고 단어로 선택). 곡 라이브러리 → 없으면 합성(calm은 `music.py` 그대로). CC BY 출처 표기 |
| `music/` | 배경음악 라이브러리: `library.json` + `<분위기>/*.m4a` (70초 발췌, −16 LUFS) |
| `tools/illustrate.py` | 사진 없는 정보성 주제용 일러스트(달력·서류·계산기·동전 등)를 Pillow로 그림. API 없음 |
| `tools/make_pictures.py` | 글만 받은 주제용: 스타일(iso·swiss·riso) 그림 3장 + 영상 theme. `tools/render_iso.py`(Chrome 캡처), `tools/iso/`·`tools/styles/`(페이지), `tools/vendor/lemo-opuscar/`(MIT 엔진) |
| `tools/slice_original.py` | 긴 캡처 원본을 이어지는 PNG 조각(조각당 1.8MB 안)으로 나눔. 블로그 끝 원본용 |
| `tools/fma.py` | Free Music Archive(HF 데이터셋)에서 라이브러리 곡 찾기(scan)·받기(fetch)·넣기(add). 이 PC에서만 실행 |
| `oneoff/publish.py` | 게시 (DB 없이 `published.json`·`log.jsonl`에 기록) |
| `oneoff/publishers.py`, `youtube.py`, `hosting.py`, `music.py` | 카드뉴스봇에서 **그대로 복사** (원본 `my-site/cardnews-bot/cardbot/`) |
| `.github/workflows/publish.yml` | 수동 실행: `post`, `action`(publish/render/render-publish), `platforms` |

## 코드 규칙
- 복사해 온 4개 파일은 카드뉴스봇 쪽에서 API 대응이 바뀌면 같이 맞춘다.
- 렌더 스타일을 바꾸면 `examples/joym-5500`으로 `preview`를 다시 만들어 보고 `pytest`를 돌린다.
- 릴스·쇼츠 영상은 위아래가 잘리지 않게 **진행 바·내용·계정명을 모두 y 285~1535 안에** 둔다 (`render.py`의 `VIDEO` 캔버스, `video.py`의 `BAR_Y`).
  릴스·쇼츠 상단/하단 UI가 위 약 290px·아래 약 390px를 가리고, 프로필 격자 미리보기(3:4·4:5)도 위아래를 잘라 낸다 (사용자 요청, 2026-11-04).
  내용 영역은 350~1470이라 이전(250~1590)보다 좁다. 글자가 많으면 자동으로 줄어든다.
- 영상: 30fps, 장면별 mp4 → concat `-c copy` → 음원 `-c:v copy`. 장면 파일은 `.part.mp4`로 쓰고 성공 시 이름 변경.
- 배경음악 분위기를 추가·수정하면 ffmpeg `ebur128`로 재서 다른 분위기와 체감 음량(약 −16 LUFS)을 맞춘다 (`bgm.py`의 `level`).
- 곡 라이브러리에는 **CC0·Public Domain Mark·CC BY만** 넣는다 (ND·SA·NC 금지 — 영상에 입히면 2차적 저작물, 계정은 수익 목적).
  `tools/fma.py`가 이 조건으로 거른다. 새 곡은 사용자가 직접 들어 보고 고른 것만 넣는다.
- CC BY 곡의 출처 표기(`music.json`의 `credit`)는 지우지 않는다. 네이버 클립 설명에도 넣는다.
- 커밋 메시지·주석·문서는 한국어.

## 이 세션 환경에서 막혀 있는 것 (클라우드 Claude 기준)
- GitHub 저장소 생성, Actions 시크릿·변수 API → 사용자 PC의 Claude Code나 GitHub 화면에서 한다.
- 네이버 클립 크리에이터(clipcreators.naver.com)는 내장 브라우저에서 열리지 않는다 → 클립 수정·삭제는 사용자가 직접.

## 테스트
```bash
pip install -r requirements.txt pytest
python -m pytest -q tests
```
