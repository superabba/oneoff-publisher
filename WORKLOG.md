# WORKLOG — 경제주막 일회성 발행 & oneoff-publisher

시각은 모두 2026-10-31(토) 한국 시간 기준.

---

## 1. 팝팝(POPPOP) 회원가입 이벤트 — 완료
- 네이버 블로그(경제주막·경제): https://blog.naver.com/economypub/224459751855
- 카드뉴스봇을 빌려 숏폼 발행
  - 릴스 https://www.instagram.com/reel/DfIa9Znv4rm/
  - 스레드 https://www.threads.com/@economypub/post/DfIbGwkHTMS
  - 쇼츠 https://youtube.com/shorts/5qrkfZoKR6E
- 뒷정리: 카드뉴스봇 이력 DB(`cardbot.db`)에서 이 게시 기록을 지워 정기 루틴(15:05)이 건너뛰지 않게 함.
- 교훈: 일회성 게시를 카드뉴스봇에 섞으면 매번 DB 뒷정리가 필요 → 별도 저장소를 만들기로 함 (5번).

## 2. 릴스쇼츠생성기 vs 카드뉴스봇 비교 — 검토만
- 게시·커밋 없이 비교만 하고, 릴스쇼츠생성기로 만들었을 때를 가정한 썸네일 1장 제작.

## 3. 조이모바일 JOY 500분 20GB 월 5,500원 — 대부분 완료
- 네이버 블로그(경제주막·경제): https://blog.naver.com/economypub/224460327155
  - 17:06 작성 → Edge(네이버 확장) 꺼져 있어 대기 → 18:55 발행됨.
- 영상: 카드뉴스 스타일 대신 노랑·검정·빨강 큰 글자 + 사진 카드 (6장면, 24.5초)
  - 릴스 https://www.instagram.com/reel/DfJsIocMF1b/
  - 스레드 https://www.threads.com/@economypub/post/DfJsPPZFsM9
  - 쇼츠 https://youtube.com/shorts/QtwhS_ameb8
  - 인스타 피드 캐러셀은 요청대로 제외.
- 뒷정리: 카드뉴스봇 DB에서 이 게시 기록 3건(149~151) 삭제·push. 폴더 이름을 날짜로 시작하지 않게
  (`oneoff-20261031-joym-5500`) 해서 15:20 블로그 자동 발행 루틴이 다시 올리지 않게 함.
- 확인하지 못한 것(글에도 표시): '평생' 요금 조건, 이벤트 기간·가입 조건, 초과 과금 차단 설정 유무.
  직접 계산: 20GB 소진 후 약 0.9GB(19,800 ÷ 22.53 ≈ 879MB)면 상한 도달, 월 최대 25,300원.
- 네이버 클립
  - ❌ 실수: Uplika에 연결된 유일한 클립인 **슈퍼아빠 워크스페이스 '스노우볼23'**에 올림 (19:01, 쇼핑 › 할인정보).
    → 사용자가 경제주막 클립을 원함. Uplika는 클립 삭제를 지원하지 않고, 내장 브라우저에서 clipcreators.naver.com이
    차단돼 있어 **사용자가 직접 삭제해야 함**.
  - 경제주막 워크스페이스에는 클립 연결이 없음 → **연결 후 발행 대기**.
    영상은 경제주막 워크스페이스에 미리 올려 둠: `med_07e81f3e41c40730` (11/2 19:02까지 유효).
    설명(277자, 태그 5개)·카테고리는 슈퍼아빠 클립에 올린 것과 같게.

## 4. 설정 변경
- 대가성(광고·협찬)은 기본 **없음**으로 보고 묻지 않음 (사용자가 있을 때만 말해 줌). 스킬·AGENTS.md에 반영.

## 5. oneoff-publisher 저장소 — 저장소 생성·시크릿 복사·테스트 렌더 완료, 첫 실제 게시 대기
**목적**: 일회성 주제를 카드뉴스봇과 완전히 분리해서 발행. 카드뉴스봇의 '오늘 이미 게시' 판단에 끼어들 일이 없다.

**만든 것**
- 카드뉴스봇에서 복사: `publishers.py`(인스타·스레드), `youtube.py`, `hosting.py`(GitHub 공개 URL), `music.py`.
- 새로 작성: `spec.py`(원고 형식), `render.py`(블록 배치 렌더러), `video.py`(등장 애니메이션·줌·진행 바),
  `publish.py`(카드뉴스봇 `Pipeline.publish`를 DB 없이 다시 씀), CLI(check/preview/render/publish),
  워크플로 `publish.yml`(수동 실행만), 테스트 6개(통과).
- 조이모바일 예시(`examples/joym-5500`)로 확인: 6장면 27.5초, 1080x1920 30fps H.264+AAC, 렌더 약 30초.
- 첫 장면은 0프레임부터 헤드라인이 보이게 함 (피드 자동 재생 때 빈 화면이 먼저 보이면 넘겨 버리므로).
- 블록 크기 자동 조정: 넘치면 축소, 화면의 78% 미만이면 최대 1.35배 확대. 그림자 여백은 배치 높이에서 제외.
- 문서: README.md, AGENTS.md, WORKLOG.md, `skills/oneoff-publish/SKILL.md`.

**my-site 쪽 변경 (유일한 예외)**
- `oneoff-secrets-sync.yml` 추가 — PR #37, 병합됨. 카드뉴스봇 시크릿(인스타·스레드·유튜브)을 이 저장소로 복사.
  수동 실행 + 매달 1일 09:50(토큰 갱신 09:20의 30분 뒤). 권한이 없으면 경고만 남기고 실패하지 않음.
  카드뉴스봇 워크플로·코드·`cardbot-data`는 건드리지 않음.

**저장소 설정 (사용자 PC의 Claude Code, 20:14~20:24)**
- `superabba/oneoff-publisher` 공개 저장소 생성, `main` push.
- 고아 브랜치 `data` 생성: README.md + `.gitignore`(`posts/*/_scenes/`)만. 작업 폴더의 추적 안 하는 파일
  (`SKILL.md`, `oneoff-publisher.zip`)이 섞이지 않게 임시 worktree에서 만들고 지움.
- 이 PC에는 git 전역 사용자 설정이 없음 → 커밋할 때 `-c user.name=... -c user.email=...`로 기존 커밋과 같은 작성자(superabba)를 지정.
- 시크릿 동기화 1차(20:14): 복사 0개, 9개 모두 `HTTP 403: Resource not accessible by personal access token`.
  `CARDBOT_ADMIN_TOKEN`은 fine-grained PAT **`cardbot-admin`**(만료 2027-10-09)이고 저장소 목록에 `my-site`만 있었음.
  → 사용자가 'Access on superabba' Edit에서 `oneoff-publisher` 추가.
- 시크릿 동기화 2차(20:23): **9개 모두 복사 완료**(IG·THREADS·YOUTUBE 7개 + `YOUTUBE_CHANNEL_ID`·`YOUTUBE_PRIVACY`),
  `gh secret list`로 저장소에 들어간 것 확인.
- 테스트 렌더(게시 없음, 20:15): `examples/joym-5500` → data `posts/20261031-joym-5500/`, `publish.yml` `action=render` 실행 #1 **성공**.
  6장면 27.5초, '게시' 단계 건너뜀, 결과물 8개가 data 브랜치에 자동 커밋, 아티팩트 `oneoff-20261031-joym-5500-1`(약 4.9MB, 11/14까지).
  Actions에서 만든 미리보기 jpg가 로컬에서 만든 것과 바이트 단위로 같음.

**막힌 것 (클라우드 Claude 세션 제약)**
- GitHub 저장소 생성 API 차단 → 사용자 PC의 Claude Code에서 생성함.
- Actions 시크릿·변수 API 차단 → 동기화 워크플로로 우회 (동작 확인).

**확인 안 된 것**
- 인스타 장기 토큰을 갱신하면 이전 토큰이 바로 무효가 되는지 → 동기화를 매달 갱신 직후에 돌려 대비.
- 실제 게시까지 한 번에 도는지(end-to-end) → 렌더까지만 확인. 다음 일회성 주제의 첫 게시에서 확인해야 함.

---

## 남은 일
- [x] (사용자) Claude Code에서 저장소 생성 + 코드 push — 아래 프롬프트
- [x] (사용자) `CARDBOT_ADMIN_TOKEN`(PAT `cardbot-admin`)의 저장소 목록에 `oneoff-publisher` 추가
- [x] 시크릿 동기화 실행(9개 복사) → 테스트 렌더(게시 없이) 성공
- [ ] 다음 일회성 주제에서 첫 실제 게시 (end-to-end 확인)
- [ ] (사용자) 2027-10-09 전에 `cardbot-admin` 토큰 만료 연장 — 만료되면 시크릿 동기화가 멈춤
- [ ] (사용자) 슈퍼아빠 클립(스노우볼23)의 조이모바일 영상 삭제 — clipcreators.naver.com
- [ ] (사용자) Uplika economypub 워크스페이스에 네이버 클립 연결 → Claude가 조이모바일 영상 발행

## Claude Code용 저장소 생성 프롬프트 (2026-10-31 실행 완료, 기록용)
`oneoff-publisher.zip`을 받아 압축을 푼 폴더에서 Claude Code를 열고 그대로 붙여 넣는다.

```
이 폴더는 superabba/oneoff-publisher 저장소의 코드야(이미 git 저장소, main에 커밋 있음).
먼저 AGENTS.md와 WORKLOG.md를 읽고 아래를 순서대로 해줘.

1. gh repo create superabba/oneoff-publisher --public --description "경제주막 일회성 발행기: 주제+사진 → 릴스·스레드·쇼츠 (카드뉴스봇과 분리)"
2. origin을 https://github.com/superabba/oneoff-publisher.git 으로 설정하고 main을 push.
3. 코드와 분리된 고아 브랜치 data를 만들어 README.md("일회성 발행 게시물·결과 저장 브랜치")와
   .gitignore("posts/*/_scenes/" 한 줄)만 커밋해서 push. 끝나면 main으로 돌아와.
4. gh workflow run oneoff-secrets-sync.yml --repo superabba/my-site 를 실행하고, 끝나면 로그에서
   '복사 완료'가 몇 개인지 알려줘. '쓰지 못했습니다' 경고가 나오면 CARDBOT_ADMIN_TOKEN 권한 문제라고 알려줘.
5. 테스트(게시 금지): examples/joym-5500 폴더 내용을 data 브랜치 posts/20261031-joym-5500/ 에 복사해 push하고
   gh workflow run publish.yml --repo superabba/oneoff-publisher -f post=20261031-joym-5500 -f action=render
   를 실행해. 끝나면 결과(성공/실패, 아티팩트)를 알려줘.

superabba/my-site의 카드뉴스봇 코드와 cardbot-data 브랜치는 절대 건드리지 마.
```
