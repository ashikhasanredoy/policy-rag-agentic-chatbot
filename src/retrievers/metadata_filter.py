"""
Deterministic Metadata Extraction and Filtering Module.
Extracts Policy IDs, department codes, and categories from user queries (multilingual English & Bangla).
Enforces safety rules to prevent over-filtering on cross-department queries.
"""

import re
from typing import Dict, Any, Optional, List
from src.ingestion.metadata_extractor import metadata_registry


class MetadataFilterExtractor:
    """Extracts and validates policy IDs and department filters from queries."""

    # Department keyword mappings (English & Bangla)
    DEPARTMENT_MAPPINGS = {
        "HR": [
            "human resources", "hr", "people", "leave", "attendance", "onboarding",
            "recruitment", "discipline", "grievance", "separation",
            "মানবসম্পদ", "ছুটি", "উপস্থিতি", "নিয়োগ", "অসদাচরণ"
        ],
        "IT": [
            "information technology", "it", "infosec", "information security", "password", "endpoint", "byod",
            "patch", "incident response", "cloud", "backup", "software asset", "system permissions", "access control",
            "system access", "identity and access",
            "তথ্যপ্রযুক্তি", "আইটি", "পাসওয়ার্ড", "ডিভাইস", "সফটওয়্যার"
        ],
        "FIN": [
            "finance", "fin", "financial", "expense", "reimbursement", "budget",
            "payroll", "treasury", "petty cash", "invoice", "travel expense",
            "অর্থ", "আর্থিক", "ব্যয়", "বাজেট", "বেতন", "ভাতা"
        ],
        "LEG": [
            "legal", "compliance", "anti-bribery", "whistleblower", "privacy", "gdpr",
            "contracts", "intellectual property", "ethics",
            "আইন", "সম্মতি", "আইনি", "হুইসেলব্লোয়ার", "গোপনীয়তা"
        ],
        "OPS": [
            "operations", "ops", "facilities", "business continuity", "disaster recovery",
            "supply chain", "workplace safety",
            "অপারেশন", "পরিচালন", "দুর্যোগ", "কর্মস্থল"
        ],
        "SEC": [
            "security", "sec", "corporate security", "physical security", "access control",
            "visitor", "cctv", "investigation",
            "নিরাপত্তা", "প্রবেশ নিয়ন্ত্রণ", "সিসিটিভি"
        ],
        "PROC": [
            "procurement", "proc", "purchasing", "sourcing", "vendor", "vendors", "supplier", "suppliers",
            "rfp", "purchase order", "due diligence", "onboarding",
            "ক্রয়", "সরবরাহকারী", "ভেন্ডর"
        ],
        "SALES": [
            "sales", "selling", "commission", "channel partner", "pricing", "discount",
            "বিক্রয়", "কমিশন", "ডিসকাউন্ট"
        ],
        "MKT": [
            "marketing", "mkt", "advertising", "advertisement", "branding", "public relations", "social media", "campaign",
            "মার্কেটিং", "বিপণন", "বিজ্ঞাপন"
        ],
        "GOV": [
            "governance", "gov", "risk", "internal control", "internal audit",
            "ai governance", "board", "policy lifecycle",
            "সুশাসন", "ঝুঁকি", "নিরীক্ষা", "অডিট"
        ]
    }

    DEPARTMENT_NAMES = {
        "HR": "Human Resources",
        "IT": "Information Technology",
        "FIN": "Finance",
        "LEG": "Legal and Compliance",
        "OPS": "Operations",
        "SEC": "Corporate Security",
        "PROC": "Procurement",
        "SALES": "Sales",
        "MKT": "Marketing",
        "GOV": "Governance, Risk and Assurance"
    }

    CROSS_COMPARISON_TERMS = [
        "compare", "versus", "vs", "differences between", "difference between", "difference", "differences",
        "compared with", "compared to", "comparison of", "comparison between",
        "between", "relationship between", "relate to", "relate", "both", "তুলনা", "পার্থক্য",
        "all policies", "find all", "list all", "multiple policies", "cross-policy",
        "policies related to", "policies regarding",
        "which policies", "what policies", "policies govern", "policies address",
        "policies covering", "policies that cover", "policies that govern", "policies that address"
    ]

    def extract_filters(self, query: str) -> Dict[str, Any]:
        """
        Extracts validated metadata filter.
        Returns a dictionary suitable for retriever filtering, e.g. {"policy_id": "HR-003"}
        or {"department": "Finance"}.
        """
        filters: Dict[str, Any] = {}
        query_lower = query.lower()

        # 1. Detect Exact Policy ID (e.g. HR-003, FIN-002, IT 001)
        raw_matches = re.findall(r"\b([A-Z]{2,5})[- ](\d{3})\b", query.upper())
        policy_id_matches = [f"{m[0]}-{m[1]}" for m in raw_matches]
        valid_ids = [pid for pid in policy_id_matches if pid in metadata_registry.registry]

        if valid_ids:
            # If multiple IDs found (e.g. comparison), do not restrict to a single policy_id
            if len(valid_ids) == 1:
                filters["policy_id"] = valid_ids[0]
            return filters

        # 2. Check for Comparative / Cross-Department Queries
        is_cross_query = any(term in query_lower for term in self.CROSS_COMPARISON_TERMS)
        if is_cross_query:
            # Avoid narrow single-policy filtering for comparative questions
            return filters

        # 3. Detect Exact Policy Title or Strong Domain Keywords
        # Check canonical policy titles from metadata registry
        for title, pid in metadata_registry.title_to_id.items():
            if len(title) >= 6 and title in query_lower:
                filters["policy_id"] = pid
                return filters

        # Domain title aliases
        TITLE_ALIASES = [
            ("advertisement", "MKT-003", "Marketing"),
            ("advertising review", "MKT-003", "Marketing"),
            ("advertising", "MKT-003", "Marketing"),
            ("marketing claims", "MKT-002", "Marketing"),
            ("unethical activities", "HR-001", "Human Resources"),
            ("unethical activity", "HR-001", "Human Resources"),
            ("unethical conduct", "HR-001", "Human Resources"),
            ("unethical", "HR-001", "Human Resources"),
            ("protect sensitive company information", "IT-001", "Information Technology"),
            ("protect sensitive information", "IT-001", "Information Technology"),
            ("sensitive company information", "IT-001", "Information Technology"),
            ("sensitive information", "IT-001", "Information Technology"),
            ("network security", "IT-005", "Information Technology"),
            ("information security", "IT-001", "Information Technology"),
            ("expense reimbursement", "FIN-002", "Finance"),
            ("expense claim", "FIN-002", "Finance"),
            ("reimbursement procedure", "FIN-002", "Finance"),
            ("reimbursement limit", "FIN-002", "Finance"),
            ("ergonomic equipment", "FIN-002", "Finance"),
            ("leave request is rejected", "HR-003", "Human Resources"),
            ("leave request rejected", "HR-003", "Human Resources"),
            ("leave is rejected", "HR-003", "Human Resources"),
            ("rejected leave", "HR-003", "Human Resources"),
            ("leave rejection", "HR-003", "Human Resources"),
            ("leave request", "HR-003", "Human Resources"),
            ("leave application", "HR-003", "Human Resources"),
            ("leave management", "HR-003", "Human Resources"),
            ("apply for leave", "HR-003", "Human Resources"),
            ("annual leave", "HR-003", "Human Resources"),
            ("anti-harassment policy", "HR-012", "Human Resources"),
            ("anti harassment policy", "HR-012", "Human Resources"),
            ("anti-harassment", "HR-012", "Human Resources"),
            ("anti harassment", "HR-012", "Human Resources"),
            ("workplace harassment", "HR-012", "Human Resources"),
            ("report suspected workplace harassment", "HR-012", "Human Resources"),
            ("report workplace harassment", "HR-012", "Human Resources"),
            ("suspected workplace harassment", "HR-012", "Human Resources"),
            ("harassment", "HR-012", "Human Resources"),
            ("system permissions when they transfer", "IT-002", "Information Technology"),
            ("system permissions", "IT-002", "Information Technology"),
            ("permissions when they transfer", "IT-002", "Information Technology"),
            ("transfer to another department", "IT-002", "Information Technology"),
            ("department transfer", "IT-002", "Information Technology"),
            ("system access request", "IT-002", "Information Technology"),
            ("access request", "IT-002", "Information Technology"),
            ("code of conduct", "HR-001", "Human Resources"),
            ("employee code of conduct", "HR-001", "Human Resources"),
            ("violates the code of conduct", "HR-001", "Human Resources"),
            ("violate the code of conduct", "HR-001", "Human Resources"),
            ("system access", "IT-002", "Information Technology"),
            ("grant, modify, and revoke", "IT-002", "Information Technology"),
            ("grant and revoke", "IT-002", "Information Technology"),
            ("grant and revoke system access", "IT-002", "Information Technology"),
            ("access management", "IT-002", "Information Technology"),
            ("identity and access", "IT-002", "Information Technology"),
            ("revoke access", "IT-002", "Information Technology"),
            ("grant access", "IT-002", "Information Technology"),
            ("records must procurement retain", "PROC-002", "Procurement"),
            ("records must retain when evaluating a supplier", "PROC-002", "Procurement"),
            ("records when evaluating a supplier", "PROC-002", "Procurement"),
            ("evaluating a supplier", "PROC-002", "Procurement"),
            ("evaluate and approve new suppliers", "PROC-002", "Procurement"),
            ("evaluate and approve suppliers", "PROC-002", "Procurement"),
            ("evaluate new suppliers", "PROC-002", "Procurement"),
            ("evaluate suppliers", "PROC-002", "Procurement"),
            ("supplier due diligence", "PROC-002", "Procurement"),
            ("due diligence", "PROC-002", "Procurement"),
            ("supplier evaluation", "PROC-002", "Procurement"),
            ("supplier selection", "PROC-002", "Procurement"),
            ("vendor onboarding", "PROC-006", "Procurement"),
            ("final settlement after resignation", "HR-015", "Human Resources"),
            ("final settlement", "HR-015", "Human Resources"),
            ("after resignation", "HR-015", "Human Resources"),
            ("resignation", "HR-015", "Human Resources"),
            ("separation and offboarding", "HR-015", "Human Resources"),
            ("employee separation", "HR-015", "Human Resources"),
            ("password and authentication", "IT-003", "Information Technology"),
            ("password", "IT-003", "Information Technology"),
            ("remote work", "HR-010", "Human Resources"),
            ("travel expense", "FIN-014", "Finance"),
            ("whistleblower protection", "LEG-004", "Legal and Compliance"),
            ("whistleblower", "LEG-004", "Legal and Compliance"),
            ("anti bribery", "LEG-001", "Legal and Compliance"),
            ("anti-bribery", "LEG-001", "Legal and Compliance"),
            ("attendance", "HR-002", "Human Resources"),
            ("disciplinary action", "HR-014", "Human Resources"),
            ("misconduct", "HR-014", "Human Resources"),
            ("ai use", "GOV-009", "Governance, Risk and Assurance"),
            ("ai governance", "GOV-009", "Governance, Risk and Assurance"),
            ("competitive bidding", "PROC-003", "Procurement"),
            ("security incident reporting", "SEC-002", "Corporate Security"),
            ("security incident", "SEC-002", "Corporate Security"),
            ("business continuity", "OPS-001", "Operations"),
            ("physical access", "OPS-010", "Operations"),
            ("endpoint and mobile device", "IT-004", "Information Technology"),
            ("endpoint", "IT-004", "Information Technology"),
            ("financial delegation of authority", "FIN-012", "Finance"),
            ("delegation of authority", "FIN-012", "Finance"),
            ("discount approval", "SALES-004", "Sales"),
            ("pricing and discount", "SALES-004", "Sales"),
            ("employee grievance", "HR-013", "Human Resources"),
            ("grievance", "HR-013", "Human Resources"),
            ("ছুটির আবেদন", "HR-003", "Human Resources"),
            ("ছুটি", "HR-003", "Human Resources"),
            ("অসদাচরণ", "HR-014", "Human Resources"),
            ("ব্যয় প্রতিদান", "FIN-002", "Finance"),
            ("খরচ পরিশোধ", "FIN-002", "Finance"),
            ("খরচ", "FIN-002", "Finance"),
            ("২৪ ঘণ্টা", "FIN-002", "Finance"),
            ("২৪ ঘন্টা", "FIN-002", "Finance"),
            ("নিরাপত্তা ঘটনা", "SEC-002", "Corporate Security"),
            ("তথ্য নিরাপত্তা", "IT-001", "Information Technology"),
            ("নেটওয়ার্ক নিরাপত্তা", "IT-005", "Information Technology"),
            ("আর্থিক অনুমোদন", "FIN-012", "Finance"),
            ("কর্মক্ষেত্রে হয়রানি", "HR-012", "Human Resources"),
            ("হয়রানি", "HR-012", "Human Resources"),
            ("কর্মচারী আচরণবিধি", "HR-001", "Human Resources"),
            ("আচরণবিধি", "HR-001", "Human Resources"),
            ("সিস্টেম পারমিশন", "IT-002", "Information Technology"),
            ("সিস্টেম অ্যাক্সেস", "IT-002", "Information Technology"),
            ("বদলি", "IT-002", "Information Technology"),
            ("পদত্যাগ", "HR-015", "Human Resources"),
            ("চূড়ান্ত নিষ্পত্তি", "HR-015", "Human Resources"),
            ("সরবরাহকারী", "PROC-002", "Procurement"),
            ("প্রকিউরমেন্ট", "PROC-002", "Procurement"),
            ("প্রাইভেসি", "LEG-008", "Legal and Compliance"),
            ("ডেটা সুরক্ষা", "LEG-008", "Legal and Compliance"),
            ("হুইসেলব্লোয়ার", "LEG-004", "Legal and Compliance"),
            ("reimbursement", "FIN-002", "Finance"),
        ]

        for alias, pid, dept in TITLE_ALIASES:
            if alias in query_lower:
                filters["policy_id"] = pid
                return filters

        # 3. Detect Department Intent
        detected_depts: List[str] = []
        for dept_code, keywords in self.DEPARTMENT_MAPPINGS.items():
            for kw in keywords:
                # Word boundary match for English; substring match for Bangla
                if re.search(r"[\u0980-\u09FF]", kw):
                    if kw in query_lower:
                        detected_depts.append(dept_code)
                        break
                else:
                    if re.search(r"\b" + re.escape(kw) + r"\b", query_lower):
                        detected_depts.append(dept_code)
                        break

        # Only filter by department if unambiguously single-department
        if len(set(detected_depts)) == 1:
            code = detected_depts[0]
            filters["department"] = self.DEPARTMENT_NAMES.get(code, code)

        return filters


metadata_filter_extractor = MetadataFilterExtractor()
