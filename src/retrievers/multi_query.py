"""
Multi-Query Expansion and Multilingual Cross-Lingual Query Processor.
Supports English and Bangla user queries, expanding natural language questions
into diverse domain-specific search expressions.
"""

import re
from typing import List, Dict, Any, Optional
from src.config.settings import settings


class MultilingualQueryExpander:
    """Expands queries into domain-specific variants and translates Bangla terms to English keywords."""

    # Bangla to English policy concept dictionary
    BANGLA_CONCEPT_MAP = {
        "ছুটি": "leave absence annual leave vacation HR-003",
        "আবেদন": "application request submit process",
        "কর্মচারী": "employee staff personnel worker",
        "অসদাচরণ": "misconduct disciplinary violation ethics conduct HR-014",
        "ব্যবস্থা": "action procedure penalty measures",
        "ব্যয়": "expense reimbursement travel claim FIN-002",
        "ভাতা": "allowance per diem stipend payment",
        "বেতন": "compensation payroll salary wages HR-008",
        "অনুমোদন": "approval authorized manager sign-off",
        "নিরাপত্তা": "security access control infosec physical security IT-001",
        "পাসওয়ার্ড": "password authentication complexity credentials IT-003",
        "হয়রানি": "harassment bullying discrimination grievance HR-012",
        "ক্রয়": "procurement purchasing vendor supplier sourcing PROC-002",
        "সরবরাহকারী": "supplier due diligence vendor procurement PROC-002",
        "প্রকিউরমেন্ট": "procurement purchasing vendor supplier PROC-002",
        "গোপনীয়তা": "privacy gdpr customer data confidentiality LEG-008",
        "প্রাইভেসি": "privacy data protection personal information LEG-008",
        "ডেটা সুরক্ষা": "data protection privacy personal information LEG-008",
        "তথ্য নিরাপত্তা": "information security confidentiality controls IT-001",
        "নেটওয়ার্ক": "network security firewall perimeter IT-005",
        "সিস্টেম": "system accounts applications IT-002",
        "পারমিশন": "permissions access control privileges identity IT-002",
        "অ্যাক্সেস": "access request identity access management IT-002",
        "বদলি": "transfer department transfer permissions role change IT-002",
        "পদত্যাগ": "resignation employee separation offboarding departure HR-015",
        "নিষ্পত্তি": "settlement final settlement compensation separation HR-015 HR-008",
        "চূড়ান্ত নিষ্পত্তি": "final settlement compensation separation offboarding HR-015 HR-008",
        "রেকর্ড": "records evidence retention documentation Section 7",
        "সংরক্ষণ": "retain retention records storage Section 7",
        "আচরণবিধি": "code of conduct employee ethics standards HR-001",
        "দূরবর্তী": "remote work telecommuting hybrid work from home HR-010",
        "হুইসেলব্লোয়ার": "whistleblower reporting ethics hotline violation LEG-004",
        "দুর্নীতি": "anti-bribery anti-corruption integrity LEG-001",
        "জালিয়াতি": "fraud prevention financial controls FIN-013",
    }

    @staticmethod
    def contains_bangla_script(text: str) -> bool:
        """Checks if text contains Bengali Unicode characters."""
        return bool(re.search(r"[\u0980-\u09FF]", text))

    @classmethod
    def is_bangla(cls, text: str) -> bool:
        """Checks if text contains Bengali Unicode characters or explicitly asks for Bengali output."""
        t = text.lower()
        return (
            cls.contains_bangla_script(text)
            or "in bangla" in t
            or "in bengali" in t
            or "বাংলা" in text
            or any(w in t.split() for w in ["bangla", "bengali"])
        )

    def expand(self, query: str, num_queries: int = settings.NUM_EXPANDED_QUERIES) -> List[str]:
        """
        Generates 3-4 diverse alternative search formulations.
        Preserves original query as the first item.
        """
        queries = [query.strip()]

        # If query has an exact Policy ID (e.g. HR-003), skip aggressive expansion
        if re.search(r"\b[A-Z]{2,5}-\d{3}\b", query.upper()):
            return queries

        query_clean = re.sub(r"[?!.,]", "", query).strip()

        # Handle Bangla Query: Translate concepts into English keywords if written in Bangla script
        if self.contains_bangla_script(query):
            translated_keywords = []
            for bn_word, en_concepts in self.BANGLA_CONCEPT_MAP.items():
                if bn_word in query:
                    translated_keywords.append(en_concepts.split()[0])
                    translated_keywords.extend(en_concepts.split()[1:3])

            if translated_keywords:
                unique_kw = list(dict.fromkeys(translated_keywords))
                queries.append(" ".join(unique_kw))
                queries.append(f"policy mandatory requirements procedure {' '.join(unique_kw[:3])}")
                queries.append(f"employee guidelines {' '.join(unique_kw[:4])}")

            return queries[:num_queries + 1]

        # For English queries (including those requesting Bangla output), clean search terms
        cleaned_for_search = re.sub(r"\b(in\s+bangla|in\s+bengali|bangla|bengali)\b", "", query_clean, flags=re.IGNORECASE).strip()
        ql = cleaned_for_search.lower()
        if "advertis" in ql or "ad " in ql or "campaign" in ql:
            queries.extend([
                "advertising review and approval procedure MKT-003",
                "marketing campaign creative claims pre-publication authorization",
                "MKT-003 advertising review operating procedure and requirements"
            ])
        elif "unethical" in ql or "ethics" in ql or "whistleblower" in ql:
            queries.extend([
                "employee code of conduct reporting unethical conduct HR-001",
                "whistleblower protection reporting suspected misconduct LEG-004",
                "workplace ethics concern escalation and non-retaliation protection"
            ])
        elif "sensitive" in ql or "confidential" in ql:
            queries.extend([
                "information security protecting sensitive company information IT-001",
                "confidential data protection access control and records safeguards",
                "IT-001 information security mandatory requirements"
            ])
        elif "leave" in ql or "vacation" in ql:
            queries.extend([
                "employee leave application process and approval workflow",
                "leave request submission procedure and eligibility requirements",
                "HR-003 leave management policy mandatory requirements"
            ])
        elif "expense" in ql or "reimbursement" in ql or "travel" in ql:
            queries.extend([
                "business travel and expense reimbursement procedure and limits",
                "corporate card expenditure documentation and submission deadline",
                "finance expense approval authority and per diem"
            ])
        elif "violate" in ql or "misconduct" in ql or "conduct" in ql or "disciplinary" in ql:
            queries.extend([
                "employee code of conduct disciplinary action procedure HR-001",
                "HR-014 disciplinary action investigation and due process",
                "workplace ethics non-compliance escalation and consequences"
            ])
        elif "remote" in ql or "hybrid" in ql or "work from home" in ql:
            queries.extend([
                "remote and hybrid workplace schedule and eligibility guidelines",
                "telecommuting home office stipend and core working hours",
                "IT endpoint security requirements for remote workers"
            ])
        elif "security" in ql or "password" in ql or "access" in ql:
            queries.extend([
                "information security access control and password complexity rules",
                "identity management MFA hardware token requirements",
                "corporate data protection and incident reporting protocol"
            ])
        elif "harassment" in ql or "bullying" in ql:
            queries.extend([
                "anti-harassment and anti-bullying reporting procedure",
                "workplace grievance formal investigation and protection from retaliation",
                "HR confidential complaint escalation and employee rights"
            ])
        elif "approve" in ql or "approval" in ql or "transaction" in ql:
            queries.extend([
                "delegation of authority financial transaction approval thresholds",
                "authorized decision rights and procurement sign-off limits",
                "internal control framework segregation of duties"
            ])
        else:
            # General query expansion
            queries.extend([
                f"{query_clean} policy mandatory requirements",
                f"{query_clean} operating procedure and responsibilities",
                f"{query_clean} approval guidelines and exceptions"
            ])

        # Deduplicate while preserving order
        seen = set()
        unique_queries = []
        for q in queries:
            if q not in seen:
                seen.add(q)
                unique_queries.append(q)

        return unique_queries[:num_queries + 1]


query_expander = MultilingualQueryExpander()

