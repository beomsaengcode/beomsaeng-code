"""모델 없이 도는 테스트: python -m pytest week02-rag/tests"""

import sys
from pathlib import Path

HERE = Path(__file__).parent.parent
sys.path.insert(0, str(HERE))

from rag import Index, chunk  # noqa: E402

DOC = (HERE / "docs/haneul_policy.md").read_text(encoding="utf-8")


def test_chunk_by_heading_keeps_sections_whole():
    parts = chunk(DOC)
    assert all(p.startswith("#") for p in parts[1:])
    assert any("골드: 30만 원" in p and "멤버십" in p for p in parts)


def test_fixed_chunk_with_overlap_repeats_edges():
    parts = chunk("가나다라마바사아", size=4, overlap=1)
    assert parts[0] == "가나다라" and parts[1].startswith("라")


def test_search_finds_membership_section():
    found = Index(chunk(DOC)).search("골드 회원 기준이 얼마예요?", k=2)
    assert any("30만 원" in c for c in found)
