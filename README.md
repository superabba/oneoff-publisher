# oneoff-publisher — 일회성 주제 발행기

주제와 사진(이벤트·특가·혜택 캡처 등)을 받아 **인스타 릴스 · 스레드 · 유튜브 쇼츠**에 올리는 저장소.
네이버 블로그(경제주막) 발행은 채팅의 Claude가 Uplika로 하고, 이 저장소는 숏폼 제작·게시를 맡는다.

카드뉴스봇(`superabba/my-site`의 `cardnews-bot/`)의 발행 코드를 본떴지만 **완전히 분리**돼 있다.

| | 카드뉴스봇 | 이 저장소 |
|---|---|---|
| 실행 | 매일 자동 (15:05 KST) | 요청할 때만 (예약 없음) |
| 주제 | 트렌드 자동 추천 | 사용자가 준 주제·사진 |
| 영상 스타일 | 카드 한 장 + 그라데이션 | 단색 배경 + 큰 글자 + 사진 카드 (시인성 우선) |
| 기록 | `cardbot-data` 브랜치 `cardbot.db` | 이 저장소 `data` 브랜치 `published.json`, `log.jsonl` |

→ 일회성 게시가 카드뉴스봇의 "오늘 이미 게시함" 판단에 끼어들 일이 없다.

## 쓰는 법 (채팅)

채팅에 사진을 올리고 이렇게 말하면 된다.

> 이 주제로 일회성 발행해줘. 블로그(경제) + 릴스·스레드·쇼츠 (+ 네이버 클립).

Claude는 `skills/oneoff-publish/SKILL.md` 순서대로 블로그 → 원고(spec.json) → 미리보기 확인 → 게시를 한다.
네이버 블로그·클립은 Uplika(경제주막 워크스페이스)로, 릴스·스레드·쇼츠는 이 저장소의 워크플로로 올라간다.

## 구조

```
oneoff/            코드
  spec.py          spec.json 읽기·검사
  render.py        장면 그리기 (블록 배치, 1080x1920 영상 장면 / 1080x1350 슬라이드)
  video.py         등장 애니메이션·줌·진행 바 → 장면별 mp4 → 이어 붙이기 → 배경음악
  publish.py       게시 (이미 올린 플랫폼은 건너뜀)
  publishers.py    인스타·스레드 API   ┐
  youtube.py       유튜브 업로드        ├ 카드뉴스봇에서 그대로 복사
  hosting.py       공개 URL 만들기      │
  music.py         배경음악 합성        ┘
fonts/             Pretendard (OFL)
examples/          예시 게시물 (조이모바일 알뜰폰 특가)
skills/            채팅 Claude가 따르는 절차 (SKILL.md)
.github/workflows/publish.yml   수동 실행 워크플로
```

`data` 브랜치 (코드와 분리된 고아 브랜치):
```
posts/<id>/        spec.json, 사진, reel.mp4, reel_cover.jpg, slide_XX.jpg, published.json
media/             인스타·스레드가 가져가는 공개 파일 (자동 업로드)
log.jsonl          게시 기록 한 줄씩
```

## 명령

```bash
pip install -r requirements.txt
python -m oneoff check   posts/<id>   # spec 검사 (글자 수 등)
python -m oneoff preview posts/<id>   # 정지 화면 미리보기 (1초)
python -m oneoff render  posts/<id>   # 영상까지 (30초 안팎)
python -m oneoff publish posts/<id> --platforms reels,threads,youtube
```

GitHub에서: Actions → **일회성 발행** → Run workflow → `post`에 폴더 이름.

## spec.json 형식

```json
{
  "id": "20261031-joym-5500",           // 영문·숫자·- 만 (폴더 이름과 같게)
  "title": "유튜브 제목 (100자 이하)",
  "caption": "릴스·쇼츠 설명 + #해시태그",
  "threads": "스레드 본문 (500자 이하)",
  "platforms": ["reels", "threads", "youtube"],
  "youtube_privacy": "public",           // 선택. 비우면 YOUTUBE_PRIVACY 시크릿, 그것도 없으면 public
  "handle": "@economypub",
  "theme": {"bg": "#FFD60A", "ink": "#111111", "accent": "#E22028", "card": "#FFFFFF"},
  "music": "auto",                       // auto=합성 배경음악, none=무음
  "scenes": [
    {"seconds": 4, "blocks": [ ... ]}     // seconds 생략하면 글자 수로 자동 (2.8~4.6초)
  ]
}
```

블록 (`[ ]`로 감싼 글자는 강조색):

| type | 예 | 모양 |
|---|---|---|
| `label` | `{"type":"label","text":"가입 전 체크 ①"}` | 작은 검정 알약 |
| `headline` | `{"type":"headline","text":"월 [5,500원]","size":150}` | 아주 큰 글자 |
| `text` | `{"type":"text","text":"알뜰폰, 괜찮을까?","size":84}` | 중간 글자 |
| `photo` | `{"type":"photo","src":"promo.jpg","width":700,"crop":[0,0,800,600]}` | 흰 테두리 사진 카드 |
| `card` | `{"type":"card","lines":["첫 줄","[강조 줄]"],"size":56}` | 흰 카드 안 여러 줄 |
| `pill` | `{"type":"pill","text":"20GB · 500분","style":"accent"}` | 검정(또는 빨강) 알약 |
| `spacer` | `{"type":"spacer","height":40}` | 빈 공간 |

글자가 넘치면 자동으로 줄이고, 화면이 비어 보이면 키운다 (블록 전체 비율 유지).

## 처음 한 번 설정

1. **시크릿** — 카드뉴스봇 저장소의 게시 계정 값을 복사해야 한다.
   - `CARDBOT_ADMIN_TOKEN`(fine-grained PAT) 설정에서 *Repository access*에 `oneoff-publisher`를 추가하고
     *Secrets: Read and write* 권한이 있는지 확인.
   - my-site Actions → **일회성 발행기 시크릿 동기화** → Run workflow.
     (매달 1일 토큰 갱신 30분 뒤에도 자동으로 다시 복사한다.)
   - 또는 이 저장소 Settings → Secrets에 직접: `IG_USER_ID`, `IG_ACCESS_TOKEN`, `THREADS_USER_ID`,
     `THREADS_ACCESS_TOKEN`, `YOUTUBE_CLIENT_ID`, `YOUTUBE_CLIENT_SECRET`, `YOUTUBE_REFRESH_TOKEN`,
     (선택) `YOUTUBE_CHANNEL_ID`, `YOUTUBE_PRIVACY`.
2. **Actions 권한** — 워크플로가 `permissions: contents: write`를 직접 요청하므로 보통 손댈 필요 없다.
   data 브랜치 푸시가 403으로 실패하면 Settings → Actions → General → Workflow permissions를 *Read and write*로.
3. 저장소는 **공개**여야 한다 — 인스타·스레드가 `raw.githubusercontent.com`/jsDelivr에서 파일을 가져간다.
