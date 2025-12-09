"""
@file llm_client.py
@author naflashDev
@brief HTTP client for interacting with a local Ollama server.
@details This module provides a simple wrapper to send prompts
         and receive responses from an LLM served by Ollama.
"""

import os
import requests
from loguru import logger

# Base URL of the local Ollama server.
# By default, Ollama listens on 127.0.0.1:11434.
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://127.0.0.1:11434")

# Name of the model installed in Ollama.
# In this project we will use "llama3" by default.
OLLAMA_MODEL_NAME = os.getenv("OLLAMA_MODEL_NAME", "cybersentinel")


def query_llm(prompt: str, system_prompt: str | None = None) -> str:
    """
    @brief Sends a prompt to the local Ollama server and returns its response.
    @param prompt User prompt or question.
    @param system_prompt Optional system-level instruction.
    @return Generated text from the LLM.
    """
    try:
        url = f"{OLLAMA_BASE_URL}/api/chat"

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        payload = {
            "model": OLLAMA_MODEL_NAME,
            "messages": messages,
            # stream=False to get the full response in a single request.
            "stream": False,
        }

        logger.debug(f"[LLM Client] Sending request to Ollama model={OLLAMA_MODEL_NAME}")
        response = requests.post(url, json=payload, timeout=120)
        response.raise_for_status()
        data = response.json()

        # Ollama /api/chat response format:
        # {
        #   "message": { "role": "assistant", "content": "..." },
        #   "done": true,
        #   ...
        # }
        message = data.get("message", {})
        content = message.get("content", "")

        if not content:
            logger.warning("[LLM Client] Empty content returned by Ollama.")
            return "Respuesta vacía del modelo."

        return content.strip()

    except Exception as e:
        logger.error(f"[LLM Client] Error while querying Ollama: {e}")
        return "Error: no se puede contactar con el servidor LLM (Ollama)."
