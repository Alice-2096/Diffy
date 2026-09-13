from diffy.rag.chunk import markdown_sections


def test_splits_markdown_on_semantic_headings() -> None:
    sections = markdown_sections("# Network\nIntro\n## Public ingress\nRule")

    assert sections == [("Network", "Intro"), ("Public ingress", "Rule")]
