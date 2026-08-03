from app.pipeline.summarize import extractive_summary


def test_extractive_returns_all_when_short():
    text = "One sentence only."
    assert extractive_summary(text, 5) == "One sentence only."


def test_extractive_limits_sentence_count():
    text = " ".join(f"Topic word alpha beta sentence number {i}." for i in range(10))
    out = extractive_summary(text, 3)
    assert out
    # At most 3 sentences (each ends with a period).
    assert out.count(".") <= 3


def test_extractive_empty():
    assert extractive_summary("", 5) == ""
    assert extractive_summary("   ", 5) == ""
