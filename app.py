import os
import sys
import tempfile
from pathlib import Path

import streamlit as st

sys.path.insert(0, str(Path(__file__).parent / "src"))

st.set_page_config(page_title="연구 자동화 Crew", page_icon="🛰️", layout="wide")

# --- Streamlit Community Cloud의 secrets를 환경변수로 반영 ---
# (App settings → Secrets 에 아래와 동일한 키로 값을 넣어두면 st.secrets에 채워짐)
_SECRET_KEYS = [
    "ANTHROPIC_API_KEY",
    "OPENAI_API_KEY",
    "GEMINI_API_KEY",
    "LITERATURE_MODEL",
    "DATA_MODEL",
    "REPORT_MODEL",
    "MANAGER_MODEL",
]
for key in _SECRET_KEYS:
    if key in st.secrets and not os.getenv(key):
        os.environ[key] = st.secrets[key]

st.title("🛰️ 연구 데이터 분석 · 문헌 검토 Crew")
st.caption(
    "문헌 검토(Claude) · 데이터 분석(GPT-4o) · 종합 작성(Gemini)이 "
    "매니저 AI(Claude)의 중재로 협업합니다."
)

missing = [k for k in ("ANTHROPIC_API_KEY", "OPENAI_API_KEY", "GEMINI_API_KEY") if not os.getenv(k)]
if missing:
    st.error(
        f"다음 API 키가 설정되지 않았습니다: {', '.join(missing)}\n\n"
        "App settings → Secrets 에서 채워주세요."
    )
    st.stop()

with st.form("crew_form"):
    topic = st.text_input(
        "연구 주제 (문헌 검색용, 영문 권장)",
        value="land-atmosphere coupling West-Central Eurasia",
    )
    research_context = st.text_area(
        "연구 배경/맥락",
        value="GRIMS 기반 지면-대기 상호작용 민감도 실험",
    )
    research_question = st.text_area(
        "핵심 연구 질문",
        value="토양수분 초기조건 변화가 지면-대기 결합 강도에 미치는 영향은?",
    )
    uploaded = st.file_uploader("분석할 데이터 파일 (CSV 또는 NetCDF .nc)", type=["csv", "nc"])
    data_description_extra = st.text_area(
        "데이터에 대한 추가 설명 (변수명, 기간, 영역 등)",
        value="GRIMS 출력 NetCDF 파일 (토양수분, 지표 플럭스 변수 포함)",
    )
    submitted = st.form_submit_button("Crew 실행")

if submitted:
    data_description = data_description_extra
    if uploaded is not None:
        suffix = Path(uploaded.name).suffix
        tmp = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
        tmp.write(uploaded.read())
        tmp.close()
        data_description = f"{data_description_extra}\n실제 파일 경로: {tmp.name}"

    from crew import build_crew  # 지연 임포트: 위에서 secrets를 먼저 env로 반영한 뒤 로드

    inputs = {
        "topic": topic,
        "research_context": research_context,
        "data_description": data_description,
        "research_question": research_question,
    }

    with st.spinner("Crew가 협업 중입니다... (매니저 AI가 작업을 배분/중재하므로 수 분 소요될 수 있음)"):
        try:
            result = build_crew().kickoff(inputs=inputs)
        except Exception as e:
            st.exception(e)
            st.stop()

    st.subheader("종합 결과")
    st.markdown(str(result))
