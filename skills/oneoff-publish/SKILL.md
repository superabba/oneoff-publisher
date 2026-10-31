---
name: oneoff-publish
description: 주제와 사진(이벤트·특가·혜택 캡처)을 주며 경제주막 네이버 블로그 발행 + 인스타 릴스·스레드·유튜브 쇼츠·네이버 클립 발행을 요청할 때. 카드뉴스봇과 분리된 superabba/oneoff-publisher로 실행.
---

# 일회성 발행 (블로그 + 릴스·스레드·쇼츠 + 클립)

사용자가 주제와 사진을 올리면, 경제주막 네이버 블로그(경제 카테고리)에 글을 발행하고
같은 내용을 인스타 릴스·스레드·유튜브 쇼츠와 경제주막 네이버 클립에 올린다.
영상에는 주제 분위기에 맞춘 배경음악을 합성해 넣는다.
영상은 카드뉴스 스타일이 아니라 노랑·검정·빨강의 큰 글자 + 사진 카드 스타일이다 (사진 스타일을 그대로 써도 됨).

**카드뉴스봇(superabba/my-site)은 쓰지도, 건드리지도 않는다.** 숏폼 게시는 전부
`superabba/oneoff-publisher` 저장소에서 한다. 그래서 카드뉴스봇 이력 DB를 지우는 뒷정리도 필요 없다.

## 고정값

- Uplika 워크스페이스: `ws_3a45040ee5856407` (economypub = 경제주막)
- 네이버 블로그 계정: `conn_4229412d79bc99ce`, 경제 카테고리 `categoryId: "2"`
- 네이버 클립: `conn_efdce3d2f5b04bc8` (handle `economypub`). **경제주막 워크스페이스에 연결된 클립 계정에만** 올린다. `superabba`(슈퍼아빠) 워크스페이스의
  클립('스노우볼23')에는 절대 올리지 않는다. 경제주막 클립이 연결돼 있지 않으면 올리지 말고
  https://uplika.com/dashboard/connections 에서 economypub 워크스페이스에 연결하라고 안내한다.
- 발행 저장소: `superabba/oneoff-publisher` (공개). 코드는 `main`, 게시물·결과는 `data` 브랜치 `posts/<id>/`
- 워크플로: `.github/workflows/publish.yml` (workflow_dispatch, 입력 `post`, `action`, `platforms`)

## 순서

### 0. 시작 전 확인 (한 번에 끝낸다)
- 광고·협찬(대가성)은 **기본적으로 없음**으로 보고 묻지 않는다. 사용자가 대가성이 있다고 말한 경우에만
  블로그 첫머리와 캡션 맨 앞에 "광고"·"협찬" 등 대가 내용을 표기하고, 클립은 `adDisclosure: true`.
- `add_repo`로 `superabba/oneoff-publisher`를 push 권한으로 붙이고 클론한다.
- Uplika `bridge_status`(workspaceId 경제주막)로 네이버 확장(Edge)이 켜져 있는지 본다. 꺼져 있으면 사용자 컴퓨터가
  연결돼 있을 때 `start msedge`로 깨워 보고, 안 되면 "Edge를 켜야 블로그 글이 나간다"고 미리 알린다.

### 1. 사실 정리
- 사진에서 읽은 내용, 사용자가 말한 내용만 사실로 쓴다. 웹에서 공식 페이지를 찾을 수 있으면 확인한다.
- 확인 못 한 것(기간, 조건, '평생'의 의미 등)은 "확인하지 못함"으로 따로 모은다. 지어내지 않는다.
- 직접 계산한 숫자는 "제 계산"이라고 표시한다.

### 2. 사진 준비
- 사진에서 앱 UI·개인정보 부분을 잘라 낸다 (Pillow). 잘라 낸 파일을 `posts/<id>/`에 영문 이름으로 저장.
- `<id>`는 `YYYYMMDD-영문키워드` (영문·숫자·`-`만; Meta가 한글 URL을 못 읽음).

### 3. 블로그 글 → 네이버 발행
- 구성: 도입 2~3문장 → 사진 → `## 한눈에 보기` 표 → `## 체크 ①②③` → 일상 비유 하나 → `## 가입(참여) 전 체크리스트`
  → `## 이 글에서 확인하지 못한 것` → `## 한 줄 정리` (인용). 해요체, 과장 금지.
- 사진은 data 브랜치에 먼저 push 한 뒤 raw URL(`https://raw.githubusercontent.com/superabba/oneoff-publisher/data/posts/<id>/<file>`)을
  Uplika `media_from_url`(workspaceId 경제주막)로 올리고, 본문에 `![설명](media:<id>)`로 넣는다.
- Uplika `publish` (workspaceId, `conn_4229412d79bc99ce`, options.naver_blog: title, categoryId "2", tags 10~12개,
  openType public, layout "as-is", seoKeywords), `wait: true`.
- 확장이 꺼져 있어 대기열에 들어가면 **발행됐다고 말하지 않는다.** userMessage를 그대로 전하고,
  나중에 `get_post`로 다시 확인해 링크를 알려 준다.

### 4. 숏폼 원고 (spec.json)
`posts/<id>/spec.json`을 쓴다. 형식은 저장소 README의 'spec.json 형식', 예시는 `examples/joym-5500/spec.json`.
- 장면 5~7개, 장면당 블록 3~5개. 첫 장면 = 가장 센 숫자/질문 (첫 프레임부터 보임).
- 마지막 장면 = 체크리스트 + `"자세한 정리 · 네이버 블로그 '경제주막'"` (accent pill).
- `[ ]` 안 글자는 빨강 강조. 한 장면에 강조는 1~2곳만.
- caption(릴스·쇼츠 설명): 2,200자·해시태그 30개 이하, 실제로는 400~600자·해시태그 10개 안팎.
  "※ 안내 화면 기준 정리 · 가입 전 공식 페이지에서 꼭 확인하세요" 같은 단서 한 줄.
- threads: 500자 이하, 해시태그 1~2개.
- title: 유튜브 제목 100자 이하.
- music: 주제 분위기를 보고 직접 고른다 (README 'spec.json 형식'의 배경음악 표).
  `calm` 잔잔(정보 정리) / `warm` 따뜻(지원금·환급·생활 정보) / `bright` 경쾌(특가·할인·이벤트·혜택) /
  `upbeat` 신나는(선착순·마감 임박) / `tense` 주의(사기·피싱·손해). 사용자가 분위기를 말하면 그대로 따른다.
  비우면 `auto`(원고 단어로 선택). `check` 출력의 '배경음악' 줄로 확인한다.

### 5. 미리보기 확인 (필수)
```bash
cd oneoff-publisher && pip install -r requirements.txt --break-system-packages -q
python -m oneoff check posts/<id> && python -m oneoff preview posts/<id>
```
`posts/<id>/preview_video.jpg`, `preview_slides.jpg`를 Read로 직접 보고, 글자 넘침·겹침·빈 화면을 고친다.
필요하면 `python -m oneoff render posts/<id>`로 영상까지 만들어 0초·장면 중간 프레임을 확인한다.

### 6. 릴스·스레드·쇼츠 발행
- `data` 브랜치에 `posts/<id>/`(spec.json + 사진 + 렌더 결과물)를 커밋·push.
  로컬에서 render 했으면 결과물(reel.mp4 등)도 같이 올린다 → 본 그대로 게시된다.
- 커밋 메시지 끝에 세션이 지정한 Co-Authored-By / Claude-Session 줄을 붙인다.
- `gh workflow run publish.yml --repo superabba/oneoff-publisher -f post=<id> -f action=publish`
- `gh run list --workflow publish.yml --repo superabba/oneoff-publisher -L 1`로 run id를 찾아 `gh run watch <id> --exit-status`
  (백그라운드로 돌리고 끝나면 확인).
- 끝나면 data 브랜치 `posts/<id>/published.json`에서 링크를 읽는다. `errors`가 있으면 그 플랫폼만
  `-f platforms=<실패한 것>`으로 다시 돌린다 (성공한 플랫폼은 자동으로 건너뜀).

### 7. 네이버 클립 (기본으로 같이 올림)
- `list_accounts`(workspaceId 경제주막)에 `platform: naver_clip` 계정이 있는지 확인. 없으면 위 '고정값'대로 안내하고 멈춘다.
- 영상: data 브랜치 `posts/<id>/reel.mp4`의 raw URL을 `media_from_url`(workspaceId 경제주막, aiGenerated false)로 올린다.
- 설명: 스레드 글을 줄여 **설명 + 태그(#) 합계 300자 이하** (UTF-16 길이로 미리 계산). 태그는 최대 5개.
- `publish`: options.naver_clip = categoryId(2단계 id, 특가·할인은 `쇼핑 › 할인정보` 등 계정의 categories에서 선택),
  tags, visibility public, aiGenerated false, adDisclosure false(대가성 없을 때), `wait: true`.
- Uplika는 클립 수정·삭제를 못 한다 → 올린 뒤 고칠 일이 생기면 사용자가 clipcreators.naver.com에서 직접.
  그래서 계정·카테고리·설명을 **올리기 전에** 한 번 더 확인한다.

### 8. 보고
- 블로그 링크(또는 대기 중), 릴스·스레드·쇼츠·클립 링크, 확인하지 못한 사항, 직접 계산한 숫자.
- 카드뉴스봇은 건드리지 않았으므로 정리 작업 없음.

## 실패했을 때
- 인스타·스레드 토큰 오류(190, OAuthException): my-site의 '일회성 발행기 시크릿 동기화' 워크플로를 실행해
  최신 토큰을 다시 복사한다 (`gh workflow run oneoff-secrets-sync.yml --repo superabba/my-site`).
- 시크릿 복사가 안 되면: 사용자가 CARDBOT_ADMIN_TOKEN(PAT)에 oneoff-publisher 저장소를 추가해야 한다.
- 클라우드 세션에서는 저장소 생성, 시크릿·변수 API, 클립 크리에이터 접속이 막혀 있다. 사용자에게 화면에서 할 일을 안내한다.
