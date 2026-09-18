"""
Research Crew용 커스텀 도구.

- ArxivSearchTool: arXiv API로 논문 검색 (API 키 불필요)
- DatasetSummaryTool: CSV/NetCDF 파일을 읽어 기술통계 요약
"""

import urllib.request
import urllib.parse
import xml.etree.ElementTree as ET

from crewai.tools import BaseTool
from pydantic import BaseModel, Field


class ArxivSearchInput(BaseModel):
    query: str = Field(..., description="arXiv에서 검색할 키워드 (영문 권장)")
    max_results: int = Field(5, description="반환할 최대 논문 수")


class ArxivSearchTool(BaseTool):
    name: str = "arxiv_search"
    description: str = (
        "arXiv에서 주어진 키워드로 논문을 검색하여 제목, 저자, 요약, 링크를 반환한다. "
        "기후/대기과학 관련 최신 논문 조사에 사용."
    )
    args_schema: type[BaseModel] = ArxivSearchInput

    def _run(self, query: str, max_results: int = 5) -> str:
        base_url = "http://export.arxiv.org/api/query?"
        params = urllib.parse.urlencode(
            {
                "search_query": f"all:{query}",
                "start": 0,
                "max_results": max_results,
                "sortBy": "submittedDate",
                "sortOrder": "descending",
            }
        )
        try:
            with urllib.request.urlopen(base_url + params, timeout=15) as resp:
                data = resp.read()
        except Exception as e:
            return f"arXiv 검색 실패: {e}"

        ns = {"atom": "http://www.w3.org/2005/Atom"}
        root = ET.fromstring(data)
        entries = root.findall("atom:entry", ns)
        if not entries:
            return "검색 결과 없음."

        lines = []
        for e in entries:
            title = e.find("atom:title", ns).text.strip().replace("\n", " ")
            summary = e.find("atom:summary", ns).text.strip().replace("\n", " ")
            link = e.find("atom:id", ns).text.strip()
            authors = ", ".join(
                a.find("atom:name", ns).text for a in e.findall("atom:author", ns)
            )
            published = e.find("atom:published", ns).text[:10]
            lines.append(
                f"- {title} ({published})\n"
                f"  저자: {authors}\n"
                f"  링크: {link}\n"
                f"  요약: {summary[:400]}..."
            )
        return "\n\n".join(lines)


class DatasetSummaryInput(BaseModel):
    file_path: str = Field(..., description="CSV 또는 NetCDF(.nc) 파일 경로")


class DatasetSummaryTool(BaseTool):
    name: str = "dataset_summary"
    description: str = (
        "CSV 또는 NetCDF(.nc) 파일을 읽어 변수별 기술통계(평균, 표준편차, 최소/최대, "
        "결측치 비율)를 요약한다. 대용량 파일은 자동으로 서브샘플링한다."
    )
    args_schema: type[BaseModel] = DatasetSummaryInput

    def _run(self, file_path: str) -> str:
        try:
            if file_path.endswith(".nc"):
                import xarray as xr

                ds = xr.open_dataset(file_path)
                lines = [f"변수 목록: {list(ds.data_vars)}"]
                for var in ds.data_vars:
                    da = ds[var]
                    lines.append(
                        f"- {var}: mean={float(da.mean()):.4g}, "
                        f"std={float(da.std()):.4g}, "
                        f"min={float(da.min()):.4g}, max={float(da.max()):.4g}, "
                        f"dims={da.dims}"
                    )
                return "\n".join(lines)
            else:
                import pandas as pd

                df = pd.read_csv(file_path)
                return df.describe(include="all").to_string()
        except Exception as e:
            return f"파일 분석 실패: {e}"
