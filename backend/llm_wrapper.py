import requests
import logging
import json
from typing import Dict
from pathlib import Path

logger = logging.getLogger(__name__)

class LLMWrapper:
    """Handles LLM calls to a local Ollama server for summarization and generation."""

    def __init__(self, model_name: str = "mistral", endpoint: str = "http://localhost:11434/api/generate"):
        self.model_name = model_name
        self.endpoint = endpoint

    def log_failed_chunk(self, chunk_text: str, error_type: str):
        """Log failed chunk and error type to a file for future review."""
        Path("logs").mkdir(exist_ok=True)
        with open("logs/failed_chunks.txt", "a", encoding="utf-8") as f:
            f.write(f"\n\n--- {error_type} ---\n")
            f.write(chunk_text)
            f.write("\n")

    def summarize_chunk(self, chunk_text: str) -> Dict:
        """Generate metadata summary from a document chunk."""
        prompt = f"""
You are summarizing notes from a counseling session. For the following text, return a JSON object with the following fields:
- summary: A 1-2 sentence summary of the content
- scope: The general scope of the chunk (e.g., check-in, therapy discussion, goals, history)
- client_names: A list of any names mentioned

Text:
\"\"\"
{chunk_text}
\"\"\"

Respond ONLY with a valid JSON object, for example:
{{
  "summary": "...",
  "scope": "...",
  "client_names": ["Name1", "Name2"]
}}
"""
        try:
            response = requests.post(self.endpoint, json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": False
            })
            response.raise_for_status()
            content = response.json().get("response", "")
            try:
                parsed = json.loads(content.strip())
            except json.JSONDecodeError as je:
                logger.warning(f"First attempt failed to parse JSON: {je}, retrying...")
                self.log_failed_chunk(chunk_text, "json_decode_error_first_attempt")
                retry_prompt = prompt + "\n\nPlease reformat the output as valid JSON."
                try:
                    retry_response = requests.post(self.endpoint, json={
                        "model": self.model_name,
                        "prompt": retry_prompt,
                        "stream": False
                    })
                    retry_response.raise_for_status()
                    retry_content = retry_response.json().get("response", "")
                    parsed = json.loads(retry_content.strip())
                except Exception as retry_e:
                    logger.error(f"Second attempt to parse JSON failed: {retry_e}")
                    self.log_failed_chunk(chunk_text, "json_decode_error_retry")
                    parsed = {
                        "summary": "Unable to parse summary.",
                        "scope": "unknown",
                        "client_names": []
                    }
            return parsed
        except Exception as e:
            logger.error(f"LLM summarization failed: {e}")
            self.log_failed_chunk(chunk_text, "request_exception")
            return {
                "summary": "Unable to summarize.",
                "scope": "unknown",
                "client_names": []
            }

    def generate_text(self, prompt: str) -> str:
        """Stream a full response to a counselor query using retrieved context."""
        try:
            response = requests.post(self.endpoint, json={
                "model": self.model_name,
                "prompt": prompt,
                "stream": True
            }, stream=True)
            response.raise_for_status()
            
            output = ""
            for line in response.iter_lines(decode_unicode=True):
                if line:
                    try:
                        data = json.loads(line)
                        token = data.get("response", "")
                        print(token, end="", flush=True)  # stream to terminal
                        output += token
                    except json.JSONDecodeError:
                        logger.warning(f"Malformed line in stream: {line}")
            return output.strip()
        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            return "I'm sorry, I couldn't generate a response due to an internal error."

    def build_structured_prompt(self, query: str, context: str, client_name: str) -> str:
        """Format the prompt to guide the LLM into giving structured, templated output."""
        return f'''
You are an expert therapy assistant helping a counselor prepare for client meetings. Use the following context to answer the question clearly and professionally.

Client: {client_name}

Context:
\"\"\"
{context}
\"\"\"

Question: {query}

Format your response with the following sections:

Summary:
- (Brief summary of the relevant information)

Therapy Goals:
- (List any mentioned or implied goals)

Progress Indicators:
- (Summarize how the client is progressing or struggling)

Recommendations:
- (List any follow-up or suggestions discussed)

Respond clearly and concisely. If there's not enough info, say so.
'''