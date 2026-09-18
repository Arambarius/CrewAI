import os
import yaml
from pathlib import Path

from crewai import Agent, Task, Crew, Process, LLM
from tools.tools import ArxivSearchTool, DatasetSummaryTool

CONFIG_DIR = Path(__file__).parent


def _load_yaml(name: str) -> dict:
    with open(CONFIG_DIR / name, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_crew() -> Crew:
    agents_cfg = _load_yaml("agents.yaml")
    tasks_cfg = _load_yaml("tasks.yaml")

    llm = LLM(model=os.getenv("MODEL", "anthropic/claude-sonnet-4-5"))

    literature_reviewer = Agent(
        config=agents_cfg["literature_reviewer"],
        tools=[ArxivSearchTool()],
        llm=llm,
        verbose=True,
    )
    data_analyst = Agent(
        config=agents_cfg["data_analyst"],
        tools=[DatasetSummaryTool()],
        llm=llm,
        verbose=True,
    )
    report_writer = Agent(
        config=agents_cfg["report_writer"],
        llm=llm,
        verbose=True,
    )

    literature_review_task = Task(
        config=tasks_cfg["literature_review_task"],
        agent=literature_reviewer,
    )
    data_analysis_task = Task(
        config=tasks_cfg["data_analysis_task"],
        agent=data_analyst,
    )
    synthesis_task = Task(
        config=tasks_cfg["synthesis_task"],
        agent=report_writer,
        context=[literature_review_task, data_analysis_task],
    )

    return Crew(
        agents=[literature_reviewer, data_analyst, report_writer],
        tasks=[literature_review_task, data_analysis_task, synthesis_task],
        process=Process.sequential,
        verbose=True,
    )
