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
  - ✅ 20:47 경제주막 클립에 발행 (6번 참고).

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

## 6. 경제주막 네이버 클립 연결·발행, 분위기별 배경음악
**네이버 클립**
- 사용자가 Uplika economypub 워크스페이스에 클립 연결: `conn_efdce3d2f5b04bc8` (handle `economypub`,
  프로필 이름 **'경제주모'** — 사용자 확인: 오타 아니고 맞는 이름).
- 조이모바일 영상 발행 (20:47): 미리 올려 둔 `med_07e81f3e41c40730`, 슈퍼아빠 클립과 같은 설명·태그 5개,
  쇼핑 › 할인정보(`163`), 공개, 대가성 없음.
  https://clip.naver.com/contents?recType=CLIP_PC&recId=%7B%22targetProfileId%22%3A%22WPKyVfCd7OvsqZG8HyfC%22%2C%22open%22%3Atrue%7D&serviceType=CLIP&seedMediaId=0570D3A80A560E5EB3CA6F850D20745D59CD
- 앞으로 일회성 발행에 클립을 기본으로 포함 (스킬 7단계).

**분위기별 배경음악** (`oneoff/bgm.py`)
- 요청: 영상 만들 때 분위기에 맞는 음악을 같이 만들기. 그전에는 모든 영상이 카드뉴스봇과 같은 잔잔한 음악 하나.
- `music`: `calm`(잔잔, 기존 music.py 그대로) / `warm` 따뜻 / `bright` 경쾌 / `upbeat` 신나는 / `tense` 주의 / `auto` / `none`.
  auto는 제목·장면 글자의 단어(특가·할인 → bright, 사기·주의 → tense 등)로 고르고, 없으면 calm.
- `music.py`는 카드뉴스봇 복사본이라 고치지 않고 새 모듈에서 불러 씀.
- 체감 음량을 calm(−16.2 LUFS)에 맞춤: 분위기별 `level`로 보정해 seed 3개 모두 −15.8~−16.4 LUFS, 최대 −1.8dBFS 이하.
- 조이모바일 예시를 로컬에서 다시 렌더: auto → bright, 27.5초, −15.8 LUFS. 테스트 13개 통과 (UTF-8 모드).
- 사용자가 분위기별 샘플 5개와 다시 렌더한 조이모바일 영상을 듣고 "이대로 좋다"고 확인.
- Windows 기본 인코딩(cp949)에서는 기존 테스트 2개가 `read_text()` 인코딩 문제로 실패 → `PYTHONUTF8=1`로 돌림 (CI 리눅스는 영향 없음).

## 7. 배경음악 곡 라이브러리 (2026-11-01)
- 사용자: 합성 음악이 단조롭다 → 무료로 쓸 수 있는 음악·생성 모델 조사 → **실제 곡 라이브러리** 방향으로 결정.
- 생성 모델은 보류. 이 PC는 NVIDIA GPU가 없고(내장 Intel Arc), GitHub Actions도 CPU라서.
  공식 모델 카드 라이선스: ACE-Step 1.5 MIT(가장 유력, 나중에 GPU로 곡을 미리 만들어 라이브러리에 보탤 수 있음),
  MusicGen·MusicGen-Melody·MMAudio·AudioLDM2 = CC-BY-NC(상업 불가), Stable Audio Open = Stability Community License(가입 필요),
  VidMuse = CC-BY-4.0(영상→음악, GPU 필요).
- 곡 출처: Hugging Face `benjamin-paine/free-music-archive-full` (FMA 약 10만 곡, 524GB). 곡마다 license·instrumental·
  allow_commercial_use·allow_derivatives·require_share_alike 필드가 있어 **CC0·PD·CC BY 연주곡만** 거름.
- `tools/fma.py`: scan(곡 정보 열만 읽기, 972개 파일 451초) → 후보 **1,119곡** (CC0·PD 110곡, 옛 녹음 빼면 16곡).
  fetch는 100곡이 snappy로 묶인 parquet 페이지를 앞에서부터 그 곡까지만 풀어 mp3를 꺼냄 (pos 0 곡 4초, pos 7 곡 12초).
- 렌더: 분위기 곡이 `music/library.json`에 있으면 그 곡(70초 발췌, −16 LUFS), 없으면 합성. 영상이 더 길면 처음부터 반복.
  CC BY 곡은 `music.json`에 출처를 남기고 publish가 캡션(릴스·쇼츠) 끝에 `🎵 제목 - 작곡가 (CC BY x.x, 편집) 주소`를 붙임.
- 임시 라이브러리(20초 발췌)로 조이모바일 예시를 렌더해 확인: 27.5초 유지, 20초 뒤 끊김 없이 반복, music.json에 출처 기록.
- 후보 25곡(분위기별 5곡, 재생 수 위주, 옛 녹음·욕설 제목·안 맞는 장르 제외)을 30초 미리듣기로 보냄 → 사용자 "전부 넣어 줘".
  `music/`에 25곡 추가 (70초 발췌, −15.7~−16.4 LUFS, 35MB): CC0 1곡(Lee Rosevere – Red Danube), CC BY 24곡.
  곡별 출처는 `music/CREDITS.md` (공개 저장소에 발췌본을 두므로).
- 실제 라이브러리로 조이모바일 예시 렌더: auto → bright → Kevin MacLeod – Vibe Ace, 27.5초, −16.0 LUFS, 출처 줄 기록. 테스트 15개 통과.
- 확인 못 한 것: 곡들이 유튜브 Content ID에 등록돼 있는지 (CC BY여도 작곡가가 등록했으면 자동 신고가 붙을 수 있음),
  출처 줄의 FMA 곡 주소(데이터셋에 있던 옛 `http://` 주소)가 지금도 열리는지 (FMA가 명령줄 접속을 막아 확인 못 함).
- my-site(카드뉴스봇·영상 업로더)에도 같은 방식을 적용하는 일은 사용자가 다른 세션에서 진행하기로 함.

## 8. 첫 실제 발행: 신한 SOL트래블 체크 × CU 빼빼로아몬드 100원 (2026-11-01)
- 폴더 `20261101-pepero-100` (data 브랜치), 배경음악 bright → 라이브러리 곡 Kevin MacLeod – Vibe Ace (CC BY 3.0), 27.1초, −16.0 LUFS.
- 로컬 렌더 → data push → `publish.yml` `action=publish` **성공** (end-to-end 확인됨).
  - 릴스 https://www.instagram.com/reel/DfLgYD5N2gS/
  - 스레드 https://www.threads.com/@economypub/post/DfLggGSiR7x
  - 쇼츠 https://youtube.com/shorts/6DS1HgDpXxI
  - 릴스·쇼츠 설명 끝에 출처 줄이 자동으로 붙음 (스레드 글에는 이미 붙어 올라갔고, 11/1 요청으로 이후부터 제외).
- 블로그(경제): https://blog.naver.com/economypub/224460877075 (Uplika에 네이버 로그인이 풀려 있다는 안내가 떴지만 01:03에 발행됨)
- 네이버 클립(경제주모, 쇼핑 › 할인정보): 같은 영상, 설명에 출처 줄 직접 포함(269자).
- 사용자 요청: 영상을 **사진의 이미지와 같거나 비슷하게** 만들어 달라 → 요청이 늦게 와서 이번엔 노란 카드 스타일 그대로 발행, **다음부터는 항상 사진 스타일** (AGENTS.md 8번, 스킬).
- 확인 못 한 것: 빼빼로아몬드 판매가·실제 결제액, 물량, 특수매장 목록, 카드 발급 조건 (글에 표시), 유튜브 Content ID 신고 여부.

## 9. 규칙 추가 (2026-11-04)
- 블로그 끝 원본 사진을 문서 너비(`{.fit}`)로, 말투는 글쓴이가 아는 내용을 독자에게 설명하는 식으로 (스킬·AGENTS.md).
- 릴스·쇼츠 영상 안전 영역: 진행 바 y300, 내용 350~1470, 계정명 1482~ (이전: 바 150, 내용 250~1590, 계정명 ~1755).
  조이모바일·빼빼로 예시로 미리보기를 다시 만들어 확인, 테스트 15개 통과. 이미 올라간 영상은 그대로 (옛 위치).

## 10. 애드포스트 수입 지급 글 (2026-11-05)
- 폴더 `20261105-adpost-payout` (data), 사용자가 구글드라이브 `oneoff` 폴더에 올린 원본 캡처 2장(가로 2,628px, 세로 5,280·11,192px)을 읽어 작성.
  대화창 사진은 세로 2,000px로 줄어들어 두 번째가 읽히지 않았음 → 드라이브로 받음(`download_file_content` 결과 파일 base64 디코딩).
- 발행 5곳: 블로그 https://blog.naver.com/economypub/224466070375 / 릴스 https://www.instagram.com/reel/DfWa0r6ttOs/ /
  스레드 https://www.threads.com/@economypub/post/DfWa8tYFlKP / 쇼츠 https://youtube.com/shorts/sLllDBCQk7g /
  클립(경제 › 재테크) 발행. 배경음악 calm Kai Engel – Low Horizon (CC BY 4.0), 출처 줄은 릴스·쇼츠·클립 설명에.
- 발행 뒤 사용자 요청으로 블로그에 **구간별로 자른 사진 6장**(PNG 무손실)을 본문 해당 위치에 추가(`update_post`), 끝의 통짜 원본 2장은 그대로.
  → 규칙 12·스킬 2단계에 반영.
- 확인 못 한 것: 11,192px 긴 원본이 네이버 글에서 잘리지 않고 보이는지, 유튜브 Content ID 신고 여부.
- 세금: 애드포스트 세금 글은 공식 자료를 읽지 못해 보류(2차 자료의 세율이 3.3%/8.8%로 엇갈림). 사용자가 화면 캡처를 주면 작성.

## 11. 아이즈모바일 SKT [S]그란데 월 10원 (2026-11-05)
- 폴더 `20261105-isemobile-10won`. 구글드라이브 `oneoff` 폴더의 캡처 3장(Screenshot_20261105_161855 / 161908 / 161917_NAVER.jpg, 가로 1,440px, 세로 7,694·5,923·6,816px)을
  사용자가 정한 순서(1855→1908→1917)대로 한 게시물로 발행.
- 블로그 https://blog.naver.com/economypub/224466126383 (구간별 사진 7장을 본문 해당 위치에, 통짜 원본 3장은 맨 끝에 문서 너비로)
- 릴스 https://www.instagram.com/reel/DfWfnSJhEZb/ / 스레드 https://www.threads.com/@economypub/post/DfWfwhRETK5 /
  쇼츠 https://youtube.com/shorts/G0TnhbIIuqA / 클립(쇼핑 › 할인정보) 발행. 배경음악 bright Josh Woodward – Under the Stairs (CC BY 3.0).
- 영상 색은 아이즈모바일 요금제 화면(남보라 버튼·연한 바탕)에 맞춤(바탕 #E7E4FF, 강조 #4326F5), 첫 장면에 요금제 카드 캡처를 넣음.
- 실수와 수정: 블로그 태그를 유니코드 코드값으로 적다가 '알뜰폰'이 '알뜩폰'으로 들어감 → `update_post`로 바로 고침(글 주소 그대로). 스킬에 주의점 추가.
- 영상 문구에서 `[S]그란데`의 대괄호가 강조 표시와 겹쳐 'S'만 강조되길래 영상에서는 '그란데'로 씀 (캡션·블로그는 `[S]그란데` 그대로).
- 확인 못 한 것: 유튜브 Content ID 신고 여부, 네이버 글에서 긴 구간 사진이 잘리지 않고 보이는지.

## 12. 모나(MONA) 11월 멤버십 혜택 (2026-11-05)
- 폴더 `20261105-mona-nov`. 구글드라이브 `oneoff` 폴더의 `모나카드.jpeg` 1장(가로 2,628px, 세로 20,217px의 긴 이벤트 페이지 캡처)을 읽고 발행.
  구간별로 자른 사진 8장(+영상용 카드 컷 1장)을 본문 해당 위치에, 통짜 원본 1장은 맨 끝에 문서 너비로.
- 블로그 https://blog.naver.com/economypub/224466489207 / 릴스 https://www.instagram.com/reel/DfXIOPrB6Q-/ /
  스레드 https://www.threads.com/@economypub/post/DfXIWnvGyCe / 쇼츠 https://youtube.com/shorts/hl4qGj6W_ps / 클립(쇼핑 › 할인정보) 발행.
  배경음악 bright Wake – Steppin (CC BY 3.0), 출처 줄은 릴스·쇼츠·클립 설명에.
- 영상 색은 모나 파랑(바탕 #E3EDFF, 강조 #0A5CFF), 첫 장면에 모나 멤버십 카드 컷.
- 실수와 수정: 블로그 비유 문장에 화면에 없는 내용('유심은 개통하는 순간부터 요금이 돌아가기 시작')을 넣었다가 발행 직후 쿠폰 비유로 고침.
  → 비유도 사진에 없는 사실을 단정하지 않는다.
- 확인 못 한 것: 유튜브 Content ID 신고 여부, 20,217px 원본이 네이버 글에서 잘리지 않고 보이는지, 이 곡의 렌더 결과가 true peak +0.3dBFS로 살짝 넘침(들어서는 큰 문제 없을 것으로 보지만 확인 못 함).

## 13. 긴 원본이 네이버에서 줄어드는 문제 (2026-11-05)
- 원인 조사: 같은 파일(모나카드.jpeg 2,628x20,217px)을 Uplika 확장으로 올리면 네이버가 208x1,600px로 줄이고, 사용자가 편집기에서 직접 올리면
  2,000x15,386px(w2000 기준)까지 줄지 않음. 우리 쪽(Drive→data→Uplika)은 바이트가 동일. 확장 경로의 긴 JPEG(세로 약 6,000px 이상)만 높이 1,600px로 줄고,
  구간별로 자른 PNG는 줄지 않음. 2MB 넘는 PNG는 네이버가 JPEG로 바꿔 다시 줄어듦. 경로 차이의 이유는 확인 못 함.
- 해결(사용자 선택 1번): 긴 원본은 `tools/slice_original.py`로 이어지는 PNG 조각으로 나눠 끝에 붙여 넣음 (스킬·규칙 9번에 반영).
  모나 원본은 7조각(0.58~1.75MB), 이으면 20,217px 그대로. 앞으로 발행부터 적용, 이미 발행한 글(모나·아이즈모바일·애드포스트)은 그대로.

## 14. 상징 이미지: 코드로 그린 일러스트 (2026-11-09)
- 요청: 사진 없이 글만 줘도 블로그에 사진을 넣고, 주제에 상징 이미지가 있으면 좋겠다. 검색·영상 캡처·직접 그리기 중 직접 그리기(B)로 결정.
- `tools/illustrate.py`: spec.json → 일러스트 PNG 1600x900 (아이콘 10종, palette 4종, 2배로 그려 줄여 부드럽게). Pillow만 사용, 인터넷·API·비용 없음.
  종합소득세 중간예납 시안 3장(달력→서류→동전 / 서류→계산기 / 폰·체크·경고)으로 확인.
- 시안의 '11월'·'1/2'는 공식 자료로 확인하지 않은 값이라 발행용이 아님 (규칙: 그림 속 글자도 확인된 사실만).
- 규칙 14번·스킬 2단계에 반영. 사진을 주는 주제, 브랜드·상품 주제에는 쓰지 않음.

---

## 남은 일
- [x] (사용자) Claude Code에서 저장소 생성 + 코드 push — 아래 프롬프트
- [x] (사용자) `CARDBOT_ADMIN_TOKEN`(PAT `cardbot-admin`)의 저장소 목록에 `oneoff-publisher` 추가
- [x] 시크릿 동기화 실행(9개 복사) → 테스트 렌더(게시 없이) 성공
- [x] 다음 일회성 주제에서 첫 실제 게시 (end-to-end 확인) — 11/1 빼빼로 100원, 성공
- [ ] (사용자) 2027-10-09 전에 `cardbot-admin` 토큰 만료 연장 — 만료되면 시크릿 동기화가 멈춤
- [ ] (사용자) 슈퍼아빠 클립(스노우볼23)의 조이모바일 영상 삭제 — clipcreators.naver.com
- [x] (사용자) Uplika economypub 워크스페이스에 네이버 클립 연결 → Claude가 조이모바일 영상 발행 (20:47)
- [x] (사용자) 배경음악 샘플 5개 듣고 확인 — 이대로 좋음
- [x] (사용자) 클립 프로필 이름 '경제주모' 확인 — 맞는 이름
- [ ] (사용자) claude.ai에 설치된 oneoff-publish 스킬을 새 `skills/oneoff-publish/SKILL.md`로 갱신
- [x] (사용자) 배경음악 후보 25곡 미리듣기 → 전부 라이브러리에 넣음
- [ ] (사용자) 출처 줄의 FMA 곡 주소가 열리는지 브라우저로 한두 개 확인 (`music/CREDITS.md`)
- [ ] (사용자, 다른 세션) my-site 카드뉴스봇·영상 업로더에 같은 배경음악 방식 적용 — 참고: oneoff-publisher `oneoff/bgm.py`, `tools/fma.py`

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

## 15. 글만 받은 주제의 스타일 그림·영상 (2026-11-10)
- lemo-opuscar(엔진 MIT) 중 등각 인포그래픽·스위스 모션·리소그래프 3가지를 채택. 주제에 맞춰 고르고 그림 3장 + 같은 배색의 영상을 만든다.
- 추가: `tools/make_pictures.py`, `tools/render_iso.py`(headless Chrome 캡처), `tools/iso/scene.html`, `tools/styles/{swiss,riso}.html`, `tools/vendor/lemo-opuscar/`.
- 영상은 장면 글자·배경을 스타일 색(`THEMES`)으로 바꾸고 그림을 photo 블록으로 넣는 방식. 영상 안에서 그림이 움직이지는 않는다.
- 이 PC의 Edge는 `--screenshot`이 동작하지 않아 Chrome을 우선 쓴다.
