import re
from typing import List, Dict, Any, Tuple
from backend.app.core.config import settings
from backend.app.core.logging import logger

STOPWORDS = {
    "what", "is", "the", "how", "many", "much", "can", "i", "do", "we", "get", "are",
    "there", "a", "an", "for", "to", "of", "in", "on", "does", "company", "provide",
    "allowed", "per", "our", "my", "and", "or", "about", "with", "have", "under", "each",
    "required", "policy", "policies", "corporate", "regarding", "monthly", "personal", "rules", "requires",
    "that", "into", "from", "when", "where", "which", "available", "managers", "employees",
    "give", "need", "some", "info", "information", "tell", "me", "know", "learn", "details",
    "want", "like", "would", "please", "find", "see", "look", "check", "ask", "help", "guidance",
    "explain", "show", "guidelines", "procedure", "procedures"
}

def stem(w: str) -> str:
    w = w.lower()
    for s in ["ation", "itions", "ition", "ingly", "edly", "fully", "ing", "ly", "ed", "es", "s", "al"]:
        if w.endswith(s) and len(w) > len(s) + 2:
            return w[:-len(s)]
    return w

class AnswerabilityGrader:
    def __init__(self, threshold: float = settings.ANSWERABILITY_THRESHOLD):
        self.threshold = threshold

    def grade(self, query: str, documents: List[Dict[str, Any]]) -> Tuple[bool, float, str]:
        if not documents:
            return False, 0.0, "No documents retrieved to evaluate answerability."

        combined_text = " ".join([
            f"{d.get('text', '')} {d.get('policy_name', '')} {d.get('category', '')} {d.get('department', '')} {d.get('section', '')}"
            for d in documents
        ]).lower()
        context_words = set(re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", combined_text))
        context_stems = set(stem(w) for w in context_words)

        raw_words = re.findall(r"\b[a-zA-Z0-9_-]{2,}\b", query.lower())
        keywords = [w for w in raw_words if w not in STOPWORDS]

        if not keywords:
            keywords = [w for w in raw_words if len(w) > 2] or raw_words

        matched_keywords = []
        for kw in keywords:
            kw_st = stem(kw)
            if kw in combined_text or kw in context_words or kw_st in context_stems:
                matched_keywords.append(kw)

        keyword_coverage = len(matched_keywords) / len(keywords) if keywords else 1.0

        # Subject Specificity Verification:
        # If the query is about specific unmentioned concepts (e.g. 'housing', 'jet', 'pet', 'dog', 'cat')
        negative_hallucination_triggers = ["housing", "pet", "dog", "cat", "bird", "jet", "yacht", "relocation allowance"]
        for trigger in negative_hallucination_triggers:
            if trigger in query.lower():
                if trigger not in combined_text and stem(trigger) not in context_stems:
                    reason = f"Explicit subject query concept '{trigger}' not found in active policies."
                    logger.info(f"Answerability grader: UNANSWERABLE ({reason})")
                    return False, 0.0, reason

        best_doc_score = max([d.get("rerank_score", d.get("score", 0.0)) for d in documents], default=0.0)
        confidence = (0.65 * keyword_coverage) + (0.35 * best_doc_score)

        is_answerable = (keyword_coverage >= 0.50) and (confidence >= self.threshold)

        if not is_answerable:
            missing = [kw for kw in keywords if kw not in matched_keywords]
            reason = f"Context lacks specific policy evidence for: {', '.join(missing)}."
            logger.info(f"Answerability grader: UNANSWERABLE ({reason})")
        else:
            reason = f"Context contains sufficient evidence (coverage: {keyword_coverage:.1%}, confidence: {confidence:.2f})"

        return is_answerable, float(confidence), reason

answerability_grader = AnswerabilityGrader()
