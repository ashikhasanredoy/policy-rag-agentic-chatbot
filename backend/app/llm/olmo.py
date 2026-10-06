import re
from typing import List, Dict, Any, Optional
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.llm.prompts import POLICY_ASSISTANT_SYSTEM_PROMPT

STOPWORDS = {
    "what", "is", "the", "how", "many", "much", "can", "i", "do", "we", "get", "are",
    "there", "a", "an", "for", "to", "of", "in", "on", "does", "company", "provide",
    "allowed", "per", "our", "my", "and", "or", "about", "with", "have", "under", "each"
}

def stem(w: str) -> str:
    w = w.lower()
    for s in ["ingly", "edly", "fully", "ing", "ly", "ed", "es", "s"]:
        if w.endswith(s) and len(w) > len(s) + 2:
            return w[:-len(s)]
    return w

class OLMoLLM:
    def __init__(self, model_name: str = settings.OLMO_MODEL_NAME, use_mock: bool = settings.USE_MOCK_MODELS):
        self.model_name = model_name
        self.use_mock = use_mock
        self.pipeline = None

        if not self.use_mock:
            try:
                import torch
                from transformers import pipeline
                logger.info(f"Initializing OLMo model pipeline: {self.model_name}")
                self.pipeline = pipeline(
                    "text-generation",
                    model=self.model_name,
                    torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
                    device_map="auto" if torch.cuda.is_available() else None,
                    max_new_tokens=512
                )
            except Exception as e:
                logger.warning(f"Could not load local OLMo transformer pipeline ({e}). Using grounded deterministic OLMo engine.")
                self.use_mock = True

    def generate(self, prompt: str, system_prompt: str = POLICY_ASSISTANT_SYSTEM_PROMPT, max_tokens: int = 512) -> str:
        if not self.use_mock and self.pipeline:
            try:
                messages = [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ]
                output = self.pipeline(messages, max_new_tokens=max_tokens, do_sample=False)
                return output[0]["generated_text"][-1]["content"]
            except Exception as e:
                logger.error(f"Error during OLMo generation: {e}")
                return self._deterministic_generate(prompt)

        return self._deterministic_generate(prompt)

    def _deterministic_generate(self, prompt: str) -> str:
        """
        Synthesizes answers strictly from the context blocks provided in the prompt.
        """
        query_match = re.search(r"Question:\s*(.*?)(?:\n\s*Policy Evidence:|\n\s*Context:|\n\s*Answer:|$)", prompt, re.DOTALL | re.IGNORECASE)
        context_match = re.search(r"(?:Policy Evidence:|Context:)\s*(.*?)(?:\n\s*Answer:|$)", prompt, re.DOTALL | re.IGNORECASE)

        query_text = query_match.group(1).strip() if query_match else ""
        context_text = context_match.group(1).strip() if context_match else prompt

        raw_q_words = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", query_text.lower())
        q_stems = set(stem(w) for w in raw_q_words if w not in STOPWORDS)
        if not q_stems:
            q_stems = set(stem(w) for w in raw_q_words)

        # Split into bullet points or sentences
        lines = [line.strip() for line in re.split(r"(?:\n+|(?<=[.!?])\s+)", context_text) if len(line.strip()) > 15]

        matched_lines = []
        for line in lines:
            if line.startswith("[") and line.endswith("]"):
                continue
            line_stems = set(stem(w) for w in re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", line.lower()))
            overlap = len(q_stems.intersection(line_stems))
            if overlap >= 1:
                matched_lines.append((overlap, line))

        matched_lines.sort(key=lambda x: x[0], reverse=True)

        if not matched_lines:
            return "Based on the verified policy context, no explicit clause was found to address this specific inquiry."

        selected = [item[1] for item in matched_lines[:3]]
        clean_items = [re.sub(r"^[\s•\-]+", "", it).strip() for it in selected]
        if len(clean_items) > 1:
            points = "\n\n".join([f"• {it}" for it in clean_items])
            return f"According to company policy:\n\n{points}"
        else:
            return f"According to company policy:\n\n• {clean_items[0]}"

olmo_llm = OLMoLLM()
