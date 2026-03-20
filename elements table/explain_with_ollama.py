import os
import requests
import json
from typing import List

def query_ollama_for_explanation(log_lines: List[str], ollama_url: str = None, model: str = None) -> str:
    """
    Send simulation log lines to Ollama and get an explanation/summary.
    """
    # Allow overriding model and API URL via environment variables
    model = model or os.environ.get("OLLAMA_MODEL", "llama3.2:1b")
    ollama_url = ollama_url or os.environ.get("OLLAMA_API_URL", "http://localhost:11434/api/generate")

    prompt = (
        "You are an AI lab assistant. Given the following simulation log, explain the key results, anomalies, and what the data means in a scientific context.\n"
        "Log:\n" + "\n".join(log_lines)
    )
    payload = {
        "model": model,
        "prompt": prompt,
        "stream": False
    }
    response = requests.post(ollama_url, json=payload)
    response.raise_for_status()
    result = response.json()
    return result.get("response", "No explanation returned.")

if __name__ == "__main__":
    # Example usage: read a log file and get explanation
    import sys
    if len(sys.argv) < 2:
        print("Usage: python explain_with_ollama.py <logfile>")
        sys.exit(1)
    with open(sys.argv[1], "r") as f:
        log_lines = f.readlines()
    explanation = query_ollama_for_explanation(log_lines)
    print("\n--- AI Explanation ---\n")
    print(explanation)
