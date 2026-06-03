import tiktoken
from typing import Dict, Union

# Price per single token (based on typical price per 1M tokens)
MODEL_PRICING = {
    "gpt-4": 0.00003,            # $30.00 / 1M tokens
    "gpt-4o": 0.0000025,         # $2.50 / 1M tokens
    "claude-3-5-sonnet": 0.000003, # $3.00 / 1M tokens
    "gemini-2.5-flash": 0.000000075, # $0.075 / 1M tokens
}

def get_pricing_per_token(model_name: str) -> float:
    """Returns the cost per token for a given model name."""
    name = model_name.lower()
    if "gpt-4o" in name or "o1" in name or "o3" in name:
        return MODEL_PRICING["gpt-4o"]
    elif "gpt-4" in name:
        return MODEL_PRICING["gpt-4"]
    elif "claude" in name:
        return MODEL_PRICING["claude-3-5-sonnet"]
    elif "gemini" in name:
        return MODEL_PRICING["gemini-2.5-flash"]
    return 0.00001  # Default fallback: $10.00 / 1M tokens

def count_tokens(text: str, model_name: str = "gpt-4") -> int:
    """
    Calculate the number of tokens in the given text using tiktoken.
    Gracefully falls back to character/word counting heuristics in offline or sandboxed environments.
    Supports gpt-4, gpt-4o, claude, and gemini approximations.
    """
    if not text:
        return 0
        
    name = model_name.lower()
    
    # Select encoding base
    encoding_name = "cl100k_base"
    if "gpt-4o" in name or "o1" in name or "o3" in name:
        # GPT-4o uses o200k_base
        encoding_name = "o200k_base"
        
    try:
        try:
            encoding = tiktoken.get_encoding(encoding_name)
        except KeyError:
            encoding = tiktoken.get_encoding("cl100k_base")
            
        base_tokens = len(encoding.encode(text, errors="ignore"))
        
        # Apply scaling heuristics for Claude & Gemini models that do not use tiktoken
        if "claude" in name:
            return int(base_tokens * 1.05)
        elif "gemini" in name:
            return int(base_tokens * 1.08)
            
        return base_tokens
    except Exception:
        # Sandboxed/Offline Fallback: Heuristic estimation (~1.3 tokens per word, or 1 token per 4 chars)
        words = text.split()
        if not words:
            return max(1, len(text) // 4)
        heuristic_tokens = max(1, int(len(words) * 1.3))
        
        if "claude" in name:
            return int(heuristic_tokens * 1.05)
        elif "gemini" in name:
            return int(heuristic_tokens * 1.08)
        elif "gpt-4o" in name or "o1" in name or "o3" in name:
            return int(heuristic_tokens * 0.85) # o200k_base is ~15% more token-efficient
            
        return heuristic_tokens


def compute_savings(raw: Union[str, int], compressed: str, model_name: str = "gpt-4") -> Dict[str, Union[int, float]]:
    """
    Computes compression stats between raw document inputs and normalized Markdown.
    If raw is an integer, it is treated as a character-length proxy.
    Calculates dynamic cost savings based on target model pricing.
    """
    if isinstance(raw, int):
        raw_tokens = raw
    else:
        raw_tokens = count_tokens(str(raw or ""), model_name)
        
    compressed_tokens = count_tokens(compressed, model_name)
    
    if raw_tokens <= 0:
        return {
            "raw_tokens": 0,
            "markdown_tokens": compressed_tokens,
            "tokens_saved": 0,
            "savings_percentage": 0.0,
            "dollars_saved": 0.0
        }
        
    tokens_saved = max(0, raw_tokens - compressed_tokens)
    savings_percentage = round((tokens_saved / raw_tokens) * 100.0, 2)
    
    # Calculate financial savings
    price_per_token = get_pricing_per_token(model_name)
    dollars_saved = round(tokens_saved * price_per_token, 6)
    
    return {
        "raw_tokens": raw_tokens,
        "markdown_tokens": compressed_tokens,
        "tokens_saved": tokens_saved,
        "savings_percentage": savings_percentage,
        "dollars_saved": dollars_saved
    }

