import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dotenv import load_dotenv
from crew import build_crew

load_dotenv()


def main():
    crew = build_crew()
    inputs = {
        "topic": "land-atmosphere coupling West-Central Eurasia",
        "research_context": "GRIMS 기반 지면-대기 상호작용 민감도 실험",
        "data_description": "GRIMS 출력 NetCDF 파일 (토양수분, 지표 플럭스 변수 포함)",
        "research_question": "토양수분 초기조건 변화가 지면-대기 결합 강도에 미치는 영향은?",
    }
    result = crew.kickoff(inputs=inputs)
    print("\n\n=== 최종 결과 ===\n")
    print(result)


if __name__ == "__main__":
    main()
