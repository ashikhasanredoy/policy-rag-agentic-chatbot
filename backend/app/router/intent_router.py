import re
from typing import Tuple, Optional, Dict, Any
from backend.app.router.intent_types import IntentType
from backend.app.core.logging import logger

POLICY_CATEGORIES = {
    "benefits": {
        "name": "Benefits & Perks",
        "description": "Comprehensive health, dental, and vision insurance, 401(k) matching (100% match up to 4%, 50% match up to 6%), annual tuition assistance ($5,250/year), and wellness subsidies ($75/month).",
        "examples": [
            "Does the company offer tuition assistance?",
            "What is the 401(k) retirement company match?",
            "What health and wellness perks are available?"
        ]
    },
    "hr": {
        "name": "Human Resources & Leave",
        "description": "Annual paid vacation (20 days per year), carryover limits (up to 5 days), 10 paid sick days, parental leaves (16 weeks maternity, 6 weeks paternity), and bereavement.",
        "examples": [
            "How many annual leave days do employees get?",
            "What is the rollover policy for unused leave?",
            "How many weeks of paid maternity leave are provided?"
        ]
    },
    "leave": {
        "name": "Annual Leave & Time Off",
        "description": "Annual paid vacation, public holidays, sick leave medical note requirements, and civic/jury duty leave.",
        "examples": [
            "How many vacation days do full-time employees accrue?",
            "Can I sell back or cash out unused annual leave?"
        ]
    },
    "remote": {
        "name": "Remote Work & Hybrid Schedule",
        "description": "Hybrid schedule (up to 2 remote days/week), core working hours (10:00 AM - 4:00 PM), $500 home office ergonomic stipend, and international travel restrictions.",
        "examples": [
            "How many days per week can I work from home?",
            "What are the mandatory core hours?",
            "Can I work remotely from another country?"
        ]
    },
    "travel": {
        "name": "Business Travel & Expense Reimbursement",
        "description": "Daily meal per diem ($75/day max: $15 breakfast, $25 lunch, $35 dinner), standard hotel limits ($200/night), coach airfare for flights under 5h, and mileage reimbursement.",
        "examples": [
            "What is the maximum daily meal per diem for business travel?",
            "What is the hotel lodging rate limit?",
            "Can I fly business class for international trips?"
        ]
    },
    "expense": {
        "name": "Travel & Expense Reimbursement",
        "description": "Allowable business expenses, per diem rates, lodging limits, corporate credit cards, and the 30-day receipt submission deadline.",
        "examples": [
            "What is the meal allowance breakdown?",
            "What is the deadline to submit travel expense claims?"
        ]
    },
    "security": {
        "name": "Information Security & Access Control",
        "description": "Password complexity (14+ chars, 90-day rotation), mandatory hardware MFA, VPN connection requirements, clean desk policy, and incident response SLAs.",
        "examples": [
            "What is the minimum password character length?",
            "When must I connect to corporate VPN?",
            "What is the clean desk policy?"
        ]
    },
    "it": {
        "name": "IT & BYOD Endpoint Security",
        "description": "Device security, 5-minute auto screen lock, 2-hour emergency lost device reporting SLA, and remote enterprise data wiping.",
        "examples": [
            "What is the screen lock timeout requirement?",
            "What is the deadline to report a lost or stolen laptop?"
        ]
    },
    "conduct": {
        "name": "Code of Conduct & Ethics",
        "description": "Workplace anti-harassment, gift & hospitality thresholds ($100 maximum value), conflict of interest disclosures, and whistleblower protections.",
        "examples": [
            "What is the gift threshold that requires disclosure?",
            "How are whistleblower reports kept confidential?"
        ]
    },
    "customer": {
        "name": "Customer Service & Refund Policy",
        "description": "30-day money-back guarantee, refund eligibility criteria, cancellation terms, and support ticket response SLA deadlines.",
        "examples": [
            "What is the standard refund eligibility window?",
            "What is the response SLA deadline for customer support?"
        ]
    }
}

OUT_OF_SCOPE_PATTERNS = [
    r"^.*(what('s| is) (the )?weather|weather in|temperature in|forecast).*$",
    r"^.*(who (won|is|was) the (match|game|super bowl|world cup|election|president of)).*$",
    r"^.*(write (a )?python|write (a )?code|debug this code|solve this math|what is \d+ [\+\-\*\/]).*$",
    r"^.*(tell me a joke|sing a song|write a poem|who is your creator).*$",
]

POLICY_LIST_PATTERNS = [
    r"^.*(what policies (do you have|are there|exist)|list (all |the )?policies|show (all |available )?policies|what can i ask( you)? about|what are the company policies)[\s.!?]*$",
]

CATEGORY_INQUIRY_PATTERNS = [
    r"^.*(tell me about|info(rmation)? (about|on|regarding)|overview of|explain( the)?|what does( the)? .* cover|what is( the)? .* about|help with( the)?|learn about|guide on( the)?)[\s]+.*(hr|human resources|leave|vacation|pto|remote work|wfh|travel|expense|expenses|security|it|benefits|perks|conduct|ethics|code of conduct|refund|customer service).*$",
    r"^.*(i need (some |more )?info(rmation)? (about|on|regarding) (the )?).*(hr|human resources|leave|vacation|remote work|travel|expense|security|it|benefits|perks|conduct|ethics|code of conduct).*$",
    r"^.*(can you tell me about (the )?).*(hr|human resources|leave|vacation|remote work|travel|expense|security|it|benefits|perks|conduct|ethics).*$",
]

SPECIFIC_POLICY_TOPIC_WORDS = [
    "annual leave", "vacation", "sick leave", "sick day", "sick days", "maternity", "paternity", "bereavement", "jury duty",
    "rollover", "carryover", "accrual", "accrue", "holiday", "sabbatical", "time off", "pto",
    "work from home", "remote work", "telecommute", "core hours", "hybrid schedule", "stipend", "home office",
    "meal allowance", "per diem", "lodging", "hotel limit", "airfare", "flight", "business class", "mileage",
    "corporate card", "concur", "receipt", "reimbursement", "travel expense",
    "password", "mfa", "hardware token", "vpn", "clean desk", "encryption", "byod", "screen lock",
    "lost device", "stolen device", "remote wipe", "data classification", "security incident",
    "401k", "401(k)", "tuition", "tuition assistance", "tuition reimbursement", "health insurance", "dental",
    "vision", "gym subsidy", "wellness subsidy", "life insurance",
    "gift", "hospitality", "whistleblower", "anti-harassment", "harassment", "conflict of interest", "bribe",
    "refund", "cancellation", "sla", "customer ticket", "housing allowance", "pet", "dog", "cat", "car allowance", "private jet"
]

CONVERSATIONAL_KEYWORDS = [
    "hello", "hi", "hey", "greetings", "good morning", "good afternoon", "good evening", "howdy", "sup", "hola",
    "how are you", "how are you doing", "how's it going", "how is it going", "what's up", "whats up",
    "who are you", "what are you", "what can you do", "what do you do", "how can you help", "what is your job",
    "thank you", "thanks", "thx", "appreciate", "much appreciated", "great", "awesome", "perfect", "cool", "nice",
    "bye", "goodbye", "see you", "have a good day", "have a nice day", "talk to you later",
    "i need help", "can you help me", "help me", "assist me", "i need some help", "i have a question",
    "need some info", "need info", "some info", "give me info", "want info", "get info", "tell me info",
    "need information", "some information", "info please", "information please", "tell me something", "what can you tell me",
    "give me some question", "give me some questions", "give me questions", "sample questions", "example questions", "suggest some questions", "suggest questions"
]

GENERIC_REQUEST_WORDS = {"need", "some", "info", "information", "help", "want", "tell", "me", "please", "can", "you", "give", "get", "know", "about", "show", "guidance", "question", "questions", "example", "examples", "sample", "samples", "a", "i"}

class IntentRouter:
    def route(self, query: str, conversation_history: Optional[list] = None) -> Tuple[IntentType, Optional[Dict[str, Any]]]:
        clean_q = query.strip()
        clean_lower = clean_q.lower()
        logger.info(f"IntentRouter: Classifying query '{clean_q}'")

        # 1. Check Out of Scope (Weather, code, trivia)
        for pat in OUT_OF_SCOPE_PATTERNS:
            if re.search(pat, clean_lower):
                logger.info("IntentRouter -> OUT_OF_SCOPE")
                return IntentType.OUT_OF_SCOPE, None

        # 2. Check Policy List request ("What policies do you have?")
        for pat in POLICY_LIST_PATTERNS:
            if re.search(pat, clean_lower):
                logger.info("IntentRouter -> POLICY_LIST")
                return IntentType.POLICY_LIST, None

        # 3. Check Policy Category Overview ("Tell me about Benefits & Perks", "Info on HR")
        for pat in CATEGORY_INQUIRY_PATTERNS:
            if re.search(pat, clean_lower):
                matched_cat = None
                for cat_key, cat_data in POLICY_CATEGORIES.items():
                    if (cat_key in clean_lower
                        or (cat_key == "benefits" and any(b in clean_lower for b in ["benefit", "perk"]))
                        or (cat_key == "hr" and any(h in clean_lower for h in ["hr", "human resources", "people"]))
                        or (cat_key == "travel" and any(t in clean_lower for t in ["travel", "flight", "lodging"]))
                        or (cat_key == "remote" and any(r in clean_lower for r in ["remote", "wfh", "telecommute"]))):
                        matched_cat = cat_data
                        break
                if matched_cat:
                    logger.info(f"IntentRouter -> POLICY_CATEGORY ({matched_cat['name']})")
                    return IntentType.POLICY_CATEGORY, matched_cat

        # Check short category name mentions (e.g. "benefits & perks", "hr policy", "travel policy")
        if len(clean_lower.split()) <= 7:
            for cat_key, cat_data in POLICY_CATEGORIES.items():
                if (clean_lower in [cat_key, f"{cat_key} policy", f"about {cat_key}", f"about {cat_key} policy", f"{cat_key} info"]
                    or (cat_key == "benefits" and any(b in clean_lower for b in ["benefits", "benefits & perks", "benefits and perks", "perks"]))
                    or (cat_key == "hr" and any(h in clean_lower for h in ["hr", "human resources", "hr policy", "human resources policy"]))):
                    logger.info(f"IntentRouter -> POLICY_CATEGORY ({cat_data['name']})")
                    return IntentType.POLICY_CATEGORY, cat_data

        # 4. Check General Chat, Greetings & Generic Info Requests
        has_policy_topic = any(topic in clean_lower for topic in SPECIFIC_POLICY_TOPIC_WORDS)
        has_conversational_cue = any(cue in clean_lower for cue in CONVERSATIONAL_KEYWORDS)

        if has_conversational_cue and not has_policy_topic:
            logger.info("IntentRouter -> GENERAL_CHAT (cue match)")
            return IntentType.GENERAL_CHAT, None

        # Check if query is composed purely of generic request words without any policy topic
        query_tokens = set(re.findall(r"\b[a-zA-Z0-9_-]+\b", clean_lower))
        if query_tokens and query_tokens.issubset(GENERIC_REQUEST_WORDS) and not has_policy_topic:
            logger.info("IntentRouter -> GENERAL_CHAT (generic tokens)")
            return IntentType.GENERAL_CHAT, None

        # Check for pure short general phrases (e.g. "hi", "ok", "help")
        if len(clean_lower.split()) <= 3 and any(cue in clean_lower for cue in ["hi", "hello", "hey", "help", "thanks", "bye", "ok", "info"]):
            if not has_policy_topic:
                logger.info("IntentRouter -> GENERAL_CHAT (short phrase)")
                return IntentType.GENERAL_CHAT, None

        # 5. Default to POLICY_QUERY (Hybrid RAG + Verification Pipeline)
        logger.info("IntentRouter -> POLICY_QUERY")
        return IntentType.POLICY_QUERY, None

intent_router = IntentRouter()
