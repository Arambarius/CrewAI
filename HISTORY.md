# 작업 히스토리

## 2026-09-19 — CrewAI 연구 자동화 스캐폴드 초기 구성

### 목적
연구 데이터 분석 자동화 및 관련 논문 확인을 위한 CrewAI 멀티에이전트
프로젝트의 초기 구조를 작성함.

### 구성한 내용

**에이전트 (`src/agents.yaml`)**
- `literature_reviewer`: 기후/대기과학 문헌 검토 전문가. 최신 논문의
  방법론·데이터셋·핵심 결과를 요약하고 사용자 연구와의 관련성을 짚음.
- `data_analyst`: 기후 데이터 분석가. 관측/모델 데이터(NetCDF, CSV)를 읽어
  기술통계와 물리적 타당성을 검토함.
- `report_writer`: 문헌 검토와 데이터 분석 결과를 통합해 학술적 문체로
  종합 보고서를 작성함.

**작업 (`src/tasks.yaml`)**
- `literature_review_task` → `literature_reviewer`
- `data_analysis_task` → `data_analyst`
- `synthesis_task` → `report_writer` (앞의 두 작업 결과를 context로 받음)

**도구 (`src/tools/tools.py`)**
- `ArxivSearchTool`: arXiv API로 논문 검색 (API 키 불필요). 제목·저자·요약·
  링크 반환.
- `DatasetSummaryTool`: CSV/NetCDF 파일을 읽어 변수별 평균·표준편차·
  최소/최대값을 요약.

**실행 진입점**
- `src/crew.py`: agents.yaml / tasks.yaml을 로드해 Agent, Task, Crew 객체를
  구성 (Process.sequential). LLM은 `MODEL` 환경변수로 지정 (기본값
  `anthropic/claude-sonnet-4-5`).
- `main.py`: 예시 inputs(topic, research_context, data_description,
  research_question)로 crew를 실행하는 진입점.

**기타**
- `requirements.txt`: crewai, crewai-tools, pandas, xarray, netCDF4,
  python-dotenv.
- `.env.example`: ANTHROPIC_API_KEY, (선택) SERPER_API_KEY / TAVILY_API_KEY.

### 확인/보류 사항
- `DatasetSummaryTool`은 범용 요약만 수행함. GRIMS 출력의 실제 변수명
  (토양수분, 지표 플럭스 등)에 맞춘 확장이 필요함.
- 문헌검색은 arXiv만 연결됨. 다른 데이터베이스(Web of Science 등) 연동은
  미구현.

### 2026-09-19 (2차) — 다중 LLM 제공사 + 계층적 위임 구조로 전환

**배경**: 사용자가 "여러 AI가 같이 작업"하는 구조를 요청함 (서로 다른
LLM 제공사가 각자 다른 역할을 맡아 실제로 협업하는 형태).

**변경 사항**
- 에이전트별로 다른 LLM 제공사를 배정 (`.env`의 환경변수로 결정):
  - `literature_reviewer` → Claude (`LITERATURE_MODEL`, 기본
    `anthropic/claude-sonnet-4-5`)
  - `data_analyst` → GPT-4o (`DATA_MODEL`, 기본 `openai/gpt-4o`)
  - `report_writer` → Gemini 1.5 Pro (`REPORT_MODEL`, 기본
    `gemini/gemini-1.5-pro`)
  - 매니저 AI → Claude Opus (`MANAGER_MODEL`, 기본
    `anthropic/claude-opus-4-1`) — 작업 배분·중재 담당
- 모든 에이전트에 `allow_delegation=True` 부여: 작업 도중 다른
  에이전트에게 실시간으로 되묻거나(ask question) 하위 작업을
  위임(delegate)할 수 있음. 이전에는 앞 에이전트의 출력이 텍스트로만
  넘어가는 고정 순서 파이프라인이었음.
- `Crew`의 `process`를 `Process.sequential` → `Process.hierarchical`로
  변경. 고정 순서 대신 매니저 AI가 실행 중에 어떤 에이전트에게 어떤
  작업을 맡길지 동적으로 결정.
- `tasks.yaml`에서 `agent:` 명시적 배정을 제거함 (계층 구조에서는
  매니저가 배정하므로 고정 지정 시 오히려 위임 로직과 충돌 가능).
- `.env.example`에 `OPENAI_API_KEY`, `GEMINI_API_KEY`, 에이전트별
  `*_MODEL` 변수 추가.

**주의할 점**
- 계층 구조는 매니저 AI가 중간에 판단/재조율하는 호출을 추가로
  발생시키므로, 순차 파이프라인보다 API 호출 수·비용·지연시간이 늘어남.
- 3개 제공사 키(Anthropic/OpenAI/Gemini)가 모두 필요함. 하나라도 없으면
  해당 에이전트가 있는 작업에서 실패함.
- 아직 실제 실행으로 위임 동작을 검증하지 않음 (다음 단계에서 확인 필요).

### 2026-09-19 (3차) — Streamlit Community Cloud 배포용 앱 추가

**배경**: 사용자가 Streamlit Community Cloud에서 직접 실행해보고 싶다고
요청함.

**추가한 파일**
- `app.py`: Streamlit UI. 연구 주제/배경/질문을 입력받고, CSV 또는
  NetCDF 데이터 파일을 업로드하면 임시 경로에 저장해 데이터 분석
  에이전트에게 넘김. "Crew 실행" 버튼을 누르면 `build_crew().kickoff()`를
  호출하고 결과를 화면에 출력.
- `.streamlit/secrets.toml.example`: Streamlit Cloud 배포 시 App settings
  → Secrets에 붙여넣을 키 목록 템플릿 (ANTHROPIC/OPENAI/GEMINI 키 +
  에이전트별 모델 지정).
- `requirements.txt`에 `streamlit` 추가.
- `.gitignore`에 `.streamlit/secrets.toml` 추가 (실제 키가 든 파일은
  절대 커밋되지 않도록).

**배포 방법 요약**
1. share.streamlit.io에서 GitHub 계정 연결, `Arambarius/CrewAI` 레포 선택
2. Main file path: `app.py`
3. App settings → Secrets에 `.streamlit/secrets.toml.example` 내용을
   실제 키로 채워 붙여넣기
4. Deploy

**주의할 점**
- Streamlit Community Cloud 앱은 기본적으로 공개 링크로 접근 가능함.
  링크를 아는 누구나 "Crew 실행"을 눌러 사용자의 API 키로 과금되는 호출을
  발생시킬 수 있으므로, 접근 제한(비공개 앱 설정 또는 간단한 비밀번호
  게이트)을 고려할 것.
- 무료 티어 리소스 제한으로 계층적 협업(매니저의 중재 호출까지 포함)이
  느리거나 타임아웃될 수 있음.

### 2026-09-19 (4차) — 배포 후 발견된 crewai 버전 이슈 수정

**증상**: Streamlit Cloud에서 실행 시
`ImportError: Anthropic native provider not available` 발생.

**원인**: `requirements.txt`에 `crewai>=0.86.0`으로만 지정해서, 실제로는
최신 버전(1.15.x대)이 설치됨. 이 버전부터 crewai가 provider별
"네이티브 클라이언트" 구조로 바뀌었고, Anthropic/Gemini는 각각
`anthropic`, `google-genai` extra를 명시적으로 설치해야 동작함
(OpenAI는 `openai` 패키지가 기본 의존성이라 추가 설치 없이 동작).

**수정**: `requirements.txt`를
`crewai[anthropic,google-genai]>=0.86.0`로 변경.
