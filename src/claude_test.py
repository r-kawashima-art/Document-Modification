# example_claude_connect_test.py

import anthropic, os

client = anthropic.Anthropic(
    api_key=os.environ.get("ANTHROPIC_API_KEY", "YOUR_API_KEY"),
    base_url="https://api.anthropic.com"
)

try:
    resp = client.messages.create(
        model="claude-3-opus-latest",
        max_tokens=512,
        messages=[{"role": "user", "content": "ping"}],
    )
    print("OK, response:", resp)
except Exception as e:
    import traceback
    traceback.print_exc()
