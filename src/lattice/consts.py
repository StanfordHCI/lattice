MODEL_FAMILIES = {
    "gpt-4.1": {"provider": "openai", "context_window": 1000000},
    "gpt-4.1-mini": {"provider": "openai", "context_window": 1000000},
    "gpt-5-mini": {"provider": "openai", "context_window": 1000000},
    "gpt-5.1": {"provider": "openai", "context_window": 1000000},
    "gpt-5.2": {"provider": "openai", "context_window": 1000000},
    "claude-sonnet-4-5-20250929": {"provider": "anthropic", "context_window": 1000000},
    "claude-opus-4-6": {"provider": "anthropic", "context_window": 1000000},
    "claude-sonnet-4-6": {"provider": "anthropic", "context_window": 1000000},
    "gemini-3-flash-preview": {"provider": "google", "context_window": 1000000},
    "gemini-3-pro-preview": {"provider": "google", "context_window": 1000000},
    "llama-3.3-70b": {"provider": "together", "name": "meta-llama/Llama-3.3-70B-Instruct-Turbo","context_window": 100000},
    "qwen-235b-instruct": {"provider": "together", "name": "Qwen/Qwen3-235B-A22B-Instruct-2507-tput","context_window": 220000},
    "qwen-235b-thinking": {"provider": "together", "name": "Qwen/Qwen3-235B-A22B-Thinking-2507","context_window": 220000},
    "qwen-3-80b": {"provider": "together", "name": "Qwen/Qwen3-Next-80B-A3B-Instruct","context_window": 220000},
}

WINDOW_SIZE = 10
MAX_CONCURRENT = 100
MIN_INSIGHTS = 3