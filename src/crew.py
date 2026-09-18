import os
import yaml
from pathlib import Path

from crewai import Agent, Task, Crew, Process, LLM
from tools.tools import ArxivSearchTool, DatasetSummaryTool

CONFIG_DIR = Path(__file__).parent


def _load_yaml(name: str) -> dict:
    with open(CONFIG_DIR / name, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def _llm(env_var: str, default: str) -> LLM:
    """환경변수로 지정된 provider/model 문자열로 LLM 객체를 만든다.
    예: anthropic/claude-sonnet-4-5, openai/gpt-4o, gemini/gemini-1.5-pro
    litellm이 provider 접두어를 보고 해당하는 API 키(ANTHROPIC_API_KEY,
    OPENAI_API_KEY, GEMINI_API_KEY)를 자동으로 찾아 사용한다."""
    return LLM(model=os.getenv(env_var, default))


def build_crew() -> Crew:
    agents_cfg = _load_yaml("agents.yaml")
    tasks_cfg = _load_yaml("tasks.yaml")

    # --- 서로 다른 LLM 제공사를 각 에이전트에 배정 ---
    literature_llm = _llm("LITERATURE_MODEL", "anthropic/claude-sonnet-4-5")
    data_llm = _llm("DATA_MODEL", "openai/gpt-4o")
    report_llm = _llm("REPORT_MODEL", "gemini/gemini-1.5-pro")
    manager_llm = _llm("MANAGER_MODEL", "anthropic/claude-opus-4-1")

    # allow_delegation=True: 작업 도중 다른 에이전트에게 실시간으로
    # 질문하거나(ask question) 하위 작업을 위임(delegate)할 수 있게 함.
    # 이게 없으면 그냥 순서대로 결과만 넘기는 파이프라인이 된다.
    literature_reviewer = Agent(
        config=agents_cfg["literature_reviewer"],
        tools=[ArxivSearchTool()],
        llm=literature_llm,
        allow_delegation=True,
        verbose=True,
    )
    data_analyst = Agent(
        config=agents_cfg["data_analyst"],
        tools=[DatasetSummaryTool()],
        llm=data_llm,
        allow_delegation=True,
        verbose=True,
    )
    report_writer = Agent(
        config=agents_cfg["report_writer"],
        llm=report_llm,
        allow_delegation=True,
        verbose=True,
    )

    literature_review_task = Task(config=tasks_cfg["literature_review_task"])
    data_analysis_task = Task(config=tasks_cfg["data_analysis_task"])
    synthesis_task = Task(
        config=tasks_cfg["synthesis_task"],
        context=[literature_review_task, data_analysis_task],
    )

    # Process.hierarchical: 고정 순서가 아니라, 매니저 AI(manager_llm)가
    # 각 작업을 실행 중에 어떤 에이전트에게 맡길지 동적으로 결정하고,
    # 필요하면 에이전트들끼리 서로 되묻게 조율한다.
    return Crew(
        agents=[literature_reviewer, data_analyst, report_writer],
        tasks=[literature_review_task, data_analysis_task, synthesis_task],
        process=Process.hierarchical,
        manager_llm=manager_llm,
        verbose=True,
    )
