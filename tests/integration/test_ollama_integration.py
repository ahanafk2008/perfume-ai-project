import pytest
import os

# This is an integration test that requires Ollama server to be running
# It should only be run manually when Ollama is available

@pytest.mark.integration
@pytest.mark.skipif(
    not os.path.exists('/usr/bin/ollama') and not os.path.exists('C:\\Program Files\\Ollama\\ollama.exe'),
    reason="Ollama not available for testing"
)
def test_ollama_integration():
    """Integration test that requires Ollama server to be running"""
    # Import here to avoid import errors when Ollama is not installed
    from app.ollama_ai import OllamaAI
    
    ai = OllamaAI()
    assert ai is not None
    
    # Test basic functionality - this will fail if Ollama server isn't running
    try:
        response = ai.generate_response("Hello", "What is your name?")
        assert response is not None
        print(f"Ollama response: {response}")
    except Exception as e:
        pytest.fail(f"Failed to get response from Ollama: {e}")

@pytest.mark.integration  
@pytest.mark.skipif(
    not os.path.exists('/usr/bin/ollama') and not os.path.exists('C:\\Program Files\\Ollama\\ollama.exe'),
    reason="Ollama not available for testing"
)
def test_ai_generator_with_ollama():
    """Test that AIResponseGenerator works with OllamaAI"""
    from app.ollama_ai import OllamaAI
    from app.services.ai import AIResponseGenerator
    
    ai = OllamaAI()
    generator = AIResponseGenerator(ai)
    
    assert generator is not None
    assert generator.ai_service is not None