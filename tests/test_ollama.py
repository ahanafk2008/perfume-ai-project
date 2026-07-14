import ollama

print("Connecting...")

response = ollama.chat(
    model="qwen3-coder:30b",
    messages=[
        {
            "role": "user",
            "content": "Say hello in one sentence."
        }
    ]
)

print(response["message"]["content"])
