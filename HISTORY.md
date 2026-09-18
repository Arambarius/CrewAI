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
- GitHub 저장소로의 자동 push는 fine-grained PAT(해당 레포 한정,
  Contents: Read and write 권한)를 받은 뒤 진행 예정.
