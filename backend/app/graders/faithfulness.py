import re
from typing import List, Dict, Any, Tuple
from backend.app.core.config import settings
from backend.app.core.logging import logger

def stem(w: str) -> str:
    w = w.lower()
    for s in ["ingly", "edly", "fully", "ing", "ly", "ed", "es", "s"]:
        if w.endswith(s) and len(w) > len(s) + 2:
            return w[:-len(s)]
    return w

class FaithfulnessGrader:
    def __init__(self, threshold: float = settings.FAITHFULNESS_THRESHOLD):
        self.threshold = threshold

    def grade(self, response_text: str, context_documents: List[Dict[str, Any]]) -> Tuple[bool, float, List[str]]:
        if not response_text:
            return True, 1.0, []

        if not context_documents:
            return False, 0.0, ["Response generated without any supporting context."]

        context_corpus = " ".join([d.get("text", "") for d in context_documents]).lower()
        context_stems = set(stem(w) for w in re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", context_corpus))

        # Split response into statements / sentences
        sentences = re.split(r"(?<=[.!?])\s+", response_text)
        sentences = [s.strip() for s in sentences if len(s.strip()) > 12]

        if not sentences:
            return True, 1.0, []

        unsupported_claims = []
        grounded_count = 0

        for sentence in sentences:
            tokens = [w for w in re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", sentence.lower()) if w not in {"according", "company", "policy", "employees", "must", "should", "based", "provided"}]
            if not tokens:
                grounded_count += 1
                continue

            sentence_stems = [stem(w) for w in tokens]
            matches = sum(1 for st in sentence_stems if st in context_stems)
            ratio = matches / len(sentence_stems)

            if ratio >= 0.40:
                grounded_count += 1
            else:
                unsupported_claims.append(sentence)

        faithfulness_score = grounded_count / len(sentences)
        is_faithful = faithfulness_score >= self.threshold

        return is_faithful, float(faithfulness_score), unsupported_claims

faithfulness_grader = FaithfulnessGrader()
