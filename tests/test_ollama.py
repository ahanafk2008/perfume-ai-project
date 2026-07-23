import pytest


@pytest.mark.integration
def test_ollama_connection():
    import ollama

    response = ollama.chat(
        model="qwen3-coder:30b",
        messages=[
            {
                "role": "user",
                "content": "Say hello in one sentence."
            }
        ],
    )

    assert "message" in response