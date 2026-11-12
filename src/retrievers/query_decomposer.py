"""
Query Decomposition Engine for Enterprise Policy RAG.
Decomposes complex multi-policy, comparative, and multi-facet questions
into targeted sub-queries to enable thorough multi-document retrieval.
"""

import re
from typing import Dict, Any, List, Optional
from src.ingestion.metadata_extractor import metadata_registry


class QueryDecomposer:
    """Analyzes and decomposes complex user queries into structured sub-queries."""

    # 10 Distinct Enterprise Policy Question Intents
    INTENT_REQUIRED_DOCUMENTS = "required_documents"
    INTENT_RECORDS = "records"
    INTENT_APPROVING_AUTHORITY = "approving_authority"
    INTENT_PROCEDURE = "procedure"
    INTENT_MANDATORY_REQUIREMENTS = "mandatory_requirements"
    INTENT_DISCIPLINARY_ACTIONS = "disciplinary_actions"
    INTENT_SECURITY_CONTROLS = "security_controls"
    INTENT_POLICY_COMPARISON = "policy_comparison"
    INTENT_POLICY_DISCOVERY = "policy_discovery"
    INTENT_EXCEPTIONS_RESTRICTIONS = "exceptions_restrictions"
    INTENT_REJECTION_APPEAL = "rejection_appeal"

    INTENT_TARGET_SECTIONS = {
        INTENT_REQUIRED_DOCUMENTS: ["7", "4"],
        INTENT_RECORDS: ["7", "4"],
        INTENT_APPROVING_AUTHORITY: ["6", "5"],
        INTENT_PROCEDURE: ["5", "4"],
        INTENT_MANDATORY_REQUIREMENTS: ["4", "5"],
        INTENT_DISCIPLINARY_ACTIONS: ["10", "5", "4"],
        INTENT_SECURITY_CONTROLS: ["4", "3"],
        INTENT_POLICY_COMPARISON: ["1", "4", "5"],
        INTENT_POLICY_DISCOVERY: ["1", "4"],
        INTENT_EXCEPTIONS_RESTRICTIONS: ["9", "4"],
        INTENT_REJECTION_APPEAL: ["5", "4", "9", "10"],
    }

    COMPARATIVE_PATTERNS = [
        r"what\s+are\s+the\s+reporting\s+procedures\s+under\s+(.+?)\s+compared\s+(?:with|to)\s+(.+)",
        r"reporting\s+procedures\s+under\s+(.+?)\s+compared\s+(?:with|to)\s+(.+)",
        r"(?:explain\s+the\s+)?differences?\s+between\s+(.+?)\s+and\s+(.+)",
        r"compare\s+(.+?)\s+(?:and|with|to)\s+(.+)",
        r"(.+?)\s+compared\s+with\s+(.+)",
        r"(.+?)\s+compared\s+to\s+(.+)",
        r"(.+?)\s+versus\s+(.+)",
        r"(.+?)\s+vs\.?\s+(.+)",
        r"(.+?)\s+(?:এবং|ও)\s+(.+?)(?:এর\s+মধ্যে.*?(?:পার্থক্য|তুলনা)|(?:এর\s+)?(?:পার্থক্য|তুলনা))",
        r"(.+?)\s+(?:এবং|ও)\s+(.+?)\s*(?:এর\s+মধ্যে\s+তুলনা|এর\s+তুলনা)",
        r"(.+?)\s+(?:এবং|ও)\s+(.+?)\s*(?:এর\s+মধ্যে\s+পার্থক্য|এর\s+পার্থক্য)"
    ]

    THEMATIC_PATTERNS = [
        r"find\s+all\s+policies\s+related\s+to\s+(.+)",
        r"all\s+policies\s+(?:related\s+to|regarding|concerning)\s+(.+)",
        r"every\s+policy\s+covering\s+(.+)",
        r"list\s+all\s+policies\s+(?:for|on|about)\s+(.+)",
        r"which\s+policies\s+(?:govern|address|cover|apply\s+to)\s+(.+)",
        r"policies\s+(?:governing|addressing|covering)\s+(.+)"
    ]

    THEMATIC_TAXONOMY = {
        "misconduct": {
            "title": "Employee Misconduct, Investigation, and Disciplinary Action",
            "policies": ["HR-001", "HR-014", "HR-013", "LEG-004"],
            "sub_queries": [
                {"policy_id": "HR-001", "query": "HR-001 Employee Code of Conduct workplace conduct rules reporting ethical breaches", "focus": "Standards & Conduct"},
                {"policy_id": "HR-014", "query": "HR-014 Disciplinary Action formal investigation procedure due process progressive sanctions", "focus": "Investigation & Discipline"},
                {"policy_id": "HR-013", "query": "HR-013 Employee Grievance and Appeals dispute escalation fair hearing", "focus": "Grievance & Appeals"},
                {"policy_id": "LEG-004", "query": "LEG-004 Whistleblower Protection confidential reporting anti-retaliation protections", "focus": "Whistleblower & Protection"}
            ]
        },
        "fraud": {
            "title": "Fraud Prevention, Corruption, and Assurance",
            "policies": ["LEG-001", "FIN-013", "GOV-014", "LEG-004"],
            "sub_queries": [
                {"policy_id": "LEG-001", "query": "LEG-001 Anti-Bribery and Anti-Corruption compliance prohibited payments and gifts", "focus": "Anti-Bribery"},
                {"policy_id": "FIN-013", "query": "FIN-013 Fraud Prevention financial internal controls segregation of duties", "focus": "Fraud Prevention"},
                {"policy_id": "GOV-014", "query": "GOV-014 Fraud Risk Reporting governance escalation independent audit", "focus": "Fraud Risk Governance"},
                {"policy_id": "LEG-004", "query": "LEG-004 Whistleblower Protection reporting illegal activity without retaliation", "focus": "Whistleblower"}
            ]
        },
        "security": {
            "title": "Information Security, Access, and Infrastructure Safeguards",
            "policies": ["IT-001", "IT-002", "IT-003", "IT-005"],
            "sub_queries": [
                {"policy_id": "IT-001", "query": "IT-001 Information Security data classification mandatory safeguards", "focus": "Information Security"},
                {"policy_id": "IT-002", "query": "IT-002 Identity and Access Management grant revoke system access least privilege", "focus": "Access Management"},
                {"policy_id": "IT-003", "query": "IT-003 Password and Authentication credential standards MFA", "focus": "Authentication"},
                {"policy_id": "IT-005", "query": "IT-005 Network Security firewall perimeter segmentation monitoring", "focus": "Network Security"}
            ]
        },
        "data_privacy": {
            "title": "Confidential Information, Employee Privacy, and Data Protection",
            "policies": ["IT-001", "LEG-008", "HR-003"],
            "sub_queries": [
                {"policy_id": "IT-001", "query": "IT-001 Information Security confidential information data classification safeguards", "focus": "Confidential Information"},
                {"policy_id": "LEG-008", "query": "LEG-008 Privacy and Data Protection personal data processing transparency", "focus": "Data Protection & Privacy"},
                {"policy_id": "HR-003", "query": "HR-003 Leave Management employee records privacy confidentiality", "focus": "Employee Privacy"}
            ]
        }
    }

    def classify_intent(self, query: str) -> str:
        """
        Classifies user query into one of 9 distinct enterprise policy intents:
        - required_documents
        - approving_authority
        - procedure
        - mandatory_requirements
        - disciplinary_actions
        - security_controls
        - policy_comparison
        - policy_discovery
        - exceptions_restrictions
        """
        q_lower = query.lower().strip()
        q_clean = re.sub(r"[?!.,]", "", q_lower).strip()

        # 1. Comparative
        for pattern in self.COMPARATIVE_PATTERNS:
            if re.search(pattern, q_clean, re.IGNORECASE):
                return self.INTENT_POLICY_COMPARISON
        if any(term in q_lower for term in [" compare ", "versus", " vs ", " vs.", "differences between", "difference between", "তুলনা", "পার্থক্য"]):
            return self.INTENT_POLICY_COMPARISON

        # 2. Policy Discovery / Thematic
        for pattern in self.THEMATIC_PATTERNS:
            if re.search(pattern, q_clean, re.IGNORECASE):
                return self.INTENT_POLICY_DISCOVERY
        if any(term in q_lower for term in [
            "all policies", "find all policies", "list all policies",
            "which policies govern", "which policies address", "which policies cover", "which policies"
        ]):
            return self.INTENT_POLICY_DISCOVERY

        # 3. Security Controls & Confidentiality
        if any(term in q_lower for term in [
            "confidential information", "protect confidential", "protecting confidential",
            "protect sensitive", "protecting sensitive", "confidentiality requirements",
            "security controls", "data protection requirements", "cybersecurity controls",
            "safeguards for confidential", "গোপনীয় তথ্য", "নিরাপত্তা নিয়ন্ত্রণ"
        ]):
            return self.INTENT_SECURITY_CONTROLS

        # 4. Rejection and Appeals
        if any(term in q_lower for term in [
            "rejected", "rejection", "turned down", "denied", "appeal", "appeals",
            "if a leave request is rejected", "what happens if a request is rejected", "প্রত্যাখ্যাত"
        ]):
            return self.INTENT_REJECTION_APPEAL

        # 5. Specific Records & Retention Requirements
        if (
            any(term in q_lower for term in [
                "what specific records", "specific records", "records must procurement retain",
                "records must retain", "records to retain", "records retention", "records should be retained",
                "records must be retained", "retention requirements", "record retention", "নথি সংরক্ষণ", "রেকর্ড"
            ])
            or ("records" in q_lower and any(v in q_lower for v in ["retain", "preserv", "retention", "evaluating a supplier"]))
        ):
            return self.INTENT_RECORDS

        # 6. Required Documents / Records & Evidence / Access Request Info
        if (
            any(term in q_lower for term in [
                "what documents", "documents are required", "document required", "required documents",
                "receipts", "submission documents", "what paperwork", "records and evidence",
                "supporting evidence required", "evidence is required", "records are required",
                "documentation required", "documents required", "supporting documents", "attach",
                "what information must be included", "information must be included in a system access request",
                "information must be included",
                "কী কী নথি", "কাগজপত্র"
            ])
            or (any(d in q_lower for d in ["document", "receipt", "paperwork", "evidence", "records"])
                and any(v in q_lower for v in ["require", "needed", "attach", "submission", "submit"]))
            or (any(d in q_lower for d in ["information", "detail"]) and "access request" in q_lower and any(v in q_lower for v in ["require", "included", "need"]))
        ):
            return self.INTENT_REQUIRED_DOCUMENTS

        # 4. Approving Authority / Responsible Roles
        if (
            any(term in q_lower for term in [
                "who is responsible for approving", "who approves", "approving authority", "approval authority",
                "who can approve", "who has authority to approve", "approval hierarchy", "who authorizes",
                "authority to approve", "roles and responsibilities", "who has final authority",
                "অনুমোদনকারী", "কে অনুমোদন করে"
            ])
            or ("who" in q_lower and any(w in q_lower for w in ["approv", "authoriz", "responsible", "sign off"]))
        ):
            return self.INTENT_APPROVING_AUTHORITY

        # 5. Disciplinary Actions / Non-Compliance / Sanctions
        if any(term in q_lower for term in [
            "what disciplinary actions", "disciplinary action", "disciplinary actions", "disciplinary consequences",
            "sanctions", "penalties", "punishment", "violates the code of conduct", "violates", "violation",
            "non-compliance actions", "breach consequences", "শাস্তিমূলক ব্যবস্থা", "দণ্ড"
        ]):
            return self.INTENT_DISCIPLINARY_ACTIONS


        # 7. Exceptions and Restrictions
        if any(term in q_lower for term in [
            "exception", "exceptions", "waiver", "waivers", "restriction", "restrictions",
            "limitations", "non-standard approval", "deviation", "ব্যতিক্রম"
        ]):
            return self.INTENT_EXCEPTIONS_RESTRICTIONS

        # 8. Mandatory Requirements / Due Diligence Requirements
        if any(term in q_lower for term in [
            "mandatory requirements", "mandatory obligations", "due diligence is required",
            "what due diligence", "compliance criteria", "compliance obligations", "rules for",
            "বাধ্যতামূলক"
        ]):
            return self.INTENT_MANDATORY_REQUIREMENTS

        # 9. Procedure / Operating Workflow (Default for operational questions)
        if any(term in q_lower for term in [
            "what is the procedure", "how is", "how can an employee apply", "how do i apply",
            "process for", "procedure for", "steps for", "workflow", "how does the company",
            "operating procedure", "পদ্ধতি", "কার্যপ্রণালী"
        ]):
            return self.INTENT_PROCEDURE

        return self.INTENT_PROCEDURE

    def get_target_sections_for_intent(self, intent: str) -> List[str]:
        """Returns the primary and secondary policy section numbers for a given intent."""
        return self.INTENT_TARGET_SECTIONS.get(intent, ["5", "4"])

    def decompose(self, query: str, detected_policy_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Decomposes query into structured sub-queries with execution instructions.
        """
        q_lower = query.lower().strip()
        q_clean = re.sub(r"[?!.,]", "", q_lower).strip()
        intent = self.classify_intent(query)
        target_secs = self.get_target_sections_for_intent(intent)

        # 1. Check Comparative Intent
        for pattern in self.COMPARATIVE_PATTERNS:
            match = re.search(pattern, q_clean, re.IGNORECASE)
            if match:
                item_a_raw = match.group(1).strip()
                item_b_raw = match.group(2).strip()

                # Clean words like "policies", "policy", "the", Bengali postpositions
                item_a = re.sub(r"\b(policies|policy|the|নীতিমালা)\b", "", item_a_raw, flags=re.IGNORECASE).strip()
                item_b = re.sub(r"\b(policies|policy|the|নীতিমালা|এর|মধ্যে|পার্থক্য|তুলনা|কী|কি|বলুন)\b", "", item_b_raw, flags=re.IGNORECASE).strip()

                pid_a = self._resolve_entity_to_policy_id(item_a)
                pid_b = self._resolve_entity_to_policy_id(item_b)

                meta_a = metadata_registry.get_metadata(pid_a) if pid_a else None
                meta_b = metadata_registry.get_metadata(pid_b) if pid_b else None
                title_a = meta_a.get("policy_title", item_a.title()) if meta_a else item_a.title()
                title_b = meta_b.get("policy_title", item_b.title()) if meta_b else item_b.title()

                sub_queries = [
                    {
                        "step": 1,
                        "policy_id": pid_a,
                        "query": f"{pid_a or item_a} {title_a} purpose scope mandatory requirements controls",
                        "objective": f"Retrieve governance scope, objectives, and mandatory controls for {title_a}"
                    },
                    {
                        "step": 2,
                        "policy_id": pid_b,
                        "query": f"{pid_b or item_b} {title_b} purpose scope mandatory requirements controls",
                        "objective": f"Retrieve governance scope, objectives, and mandatory controls for {title_b}"
                    },
                    {
                        "step": 3,
                        "policy_id": None,
                        "query": f"{title_a} vs {title_b} difference in controls operating procedure responsibilities",
                        "objective": "Cross-compare verified clauses, responsibilities, and infrastructure scope"
                    }
                ]

                target_policies = [p for p in [pid_a, pid_b] if p]
                return {
                    "is_complex": True,
                    "strategy": "comparative",
                    "intent_type": self.INTENT_POLICY_COMPARISON,
                    "target_sections": ["1", "4", "5"],
                    "explanation": f"Decomposed comparative query into {title_a} ({pid_a}) vs {title_b} ({pid_b}) facet evaluations.",
                    "target_policies": target_policies,
                    "sub_queries": sub_queries
                }

        # 2. Check Thematic Multi-Document Intent
        for pattern in self.THEMATIC_PATTERNS:
            match = re.search(pattern, q_clean, re.IGNORECASE)
            if match:
                theme_topic = match.group(1).strip()
                matched_theme = None
                for key in self.THEMATIC_TAXONOMY:
                    if key in theme_topic or key in q_lower:
                        matched_theme = key
                        break

                if matched_theme:
                    tax = self.THEMATIC_TAXONOMY[matched_theme]
                    sub_queries = []
                    for i, facet in enumerate(tax["sub_queries"], 1):
                        sub_queries.append({
                            "step": i,
                            "policy_id": facet["policy_id"],
                            "query": facet["query"],
                            "objective": f"Verify provisions for {facet['focus']}"
                        })

                    return {
                        "is_complex": True,
                        "strategy": "multi_document",
                        "intent_type": self.INTENT_POLICY_DISCOVERY,
                        "target_sections": ["1", "4"],
                        "explanation": f"Decomposed multi-policy query across {tax['title']}.",
                        "target_policies": tax["policies"],
                        "sub_queries": sub_queries
                    }

        # Also check keyword triggers for multi-policy themes
        if (any(term in q_lower for term in ["misconduct", "disciplinary action", "investigation"])
            and any(term in q_lower for term in ["all", "find all", "list", "policies", "which policies"])):
            tax = self.THEMATIC_TAXONOMY["misconduct"]
            sub_queries = [
                {"step": i, "policy_id": f["policy_id"], "query": f["query"], "objective": f"Verify provisions for {f['focus']}"}
                for i, f in enumerate(tax["sub_queries"], 1)
            ]
            return {
                "is_complex": True,
                "strategy": "multi_document",
                "intent_type": self.INTENT_POLICY_DISCOVERY,
                "target_sections": ["1", "4"],
                "explanation": "Decomposed multi-policy misconduct & discipline query into 4 facet policy retrievals.",
                "target_policies": tax["policies"],
                "sub_queries": sub_queries
            }

        if (any(term in q_lower for term in ["fraud", "corruption", "bribery", "whistleblower"])
            and any(term in q_lower for term in ["all", "find all", "list", "policies", "which policies", "address", "govern"])):
            tax = self.THEMATIC_TAXONOMY["fraud"]
            sub_queries = [
                {"step": i, "policy_id": f["policy_id"], "query": f["query"], "objective": f"Verify provisions for {f['focus']}"}
                for i, f in enumerate(tax["sub_queries"], 1)
            ]
            return {
                "is_complex": True,
                "strategy": "multi_document",
                "intent_type": self.INTENT_POLICY_DISCOVERY,
                "target_sections": ["1", "4"],
                "explanation": "Decomposed multi-policy fraud & corruption query into 4 facet policy retrievals.",
                "target_policies": tax["policies"],
                "sub_queries": sub_queries
            }

        if (any(term in q_lower for term in ["confidential information", "employee privacy", "data protection"])
            and any(term in q_lower for term in ["all", "find all", "list", "policies", "which policies", "address", "govern"])):
            tax = self.THEMATIC_TAXONOMY["data_privacy"]
            sub_queries = [
                {"step": i, "policy_id": f["policy_id"], "query": f["query"], "objective": f"Verify provisions for {f['focus']}"}
                for i, f in enumerate(tax["sub_queries"], 1)
            ]
            return {
                "is_complex": True,
                "strategy": "multi_document",
                "intent_type": self.INTENT_POLICY_DISCOVERY,
                "target_sections": ["1", "4"],
                "explanation": "Decomposed multi-policy data protection and privacy query into 3 facet policy retrievals.",
                "target_policies": tax["policies"],
                "sub_queries": sub_queries
            }

        # 3. Check Complex Operational Intent (Type D)
        # e.g., "How does the company evaluate and approve new suppliers?" or "Which policies govern supplier selection, financial approval, and vendor risk?"
        if any(term in q_lower for term in ["evaluate and approve new suppliers", "evaluate and approve suppliers", "how does the company evaluate and approve"]) and "due diligence" not in q_lower:
            sub_queries = [
                {
                    "step": 1,
                    "policy_id": "PROC-002",
                    "query": "PROC-002 Supplier Due Diligence evaluation risk screening qualification mandatory requirements",
                    "objective": "Retrieve mandatory due diligence and risk screening requirements for new suppliers"
                },
                {
                    "step": 2,
                    "policy_id": "PROC-006",
                    "query": "PROC-006 Vendor Onboarding new vendor setup intake verification approval",
                    "objective": "Retrieve operational onboarding and profile verification procedure"
                },
                {
                    "step": 3,
                    "policy_id": "FIN-012",
                    "query": "FIN-012 Financial Delegation of Authority spending approval thresholds procurement authorization",
                    "objective": "Retrieve documented financial approval thresholds and delegation limits"
                }
            ]
            return {
                "is_complex": True,
                "strategy": "complex_operational",
                "intent_type": "D_complex_operational",
                "target_sections": ["4", "5"],
                "explanation": "Decomposed operational query into Procurement Due Diligence (PROC-002), Vendor Onboarding (PROC-006), and Financial Delegation of Authority (FIN-012).",
                "target_policies": ["PROC-002", "PROC-006", "FIN-012"],
                "sub_queries": sub_queries
            }

        # 4. Targeted Single-Policy Query with Intent-Driven Section Targeting
        effective_pid = detected_policy_id
        if not effective_pid:
            effective_pid = self._resolve_entity_to_policy_id(q_clean)
        if not effective_pid:
            # Check if query matches known policy
            for title, pid in metadata_registry.title_to_id.items():
                if len(title) >= 5 and title in q_lower:
                    effective_pid = pid
                    break

        if effective_pid:
            p_meta = metadata_registry.get_metadata(effective_pid)
            title = p_meta.get("policy_title", effective_pid) if p_meta else effective_pid

            if intent in [self.INTENT_REQUIRED_DOCUMENTS, self.INTENT_RECORDS]:
                sub_queries = [
                    {
                        "step": 1,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 7 Records and Evidence documentation receipts required records retention",
                        "objective": "Retrieve required records, receipts, and submission documentation"
                    },
                    {
                        "step": 2,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 4 Mandatory Requirements reliable evidence documentation record retention",
                        "objective": "Retrieve mandatory evidence and record retention rules"
                    }
                ]
            elif intent == self.INTENT_APPROVING_AUTHORITY:
                sub_queries = [
                    {
                        "step": 1,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 6 Roles and Responsibilities approving authority authorized manager decision-maker",
                        "objective": "Retrieve approving authority and managerial responsibilities"
                    },
                    {
                        "step": 2,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 5 Operating Procedure Step 3 review communicate decision",
                        "objective": "Retrieve approval procedure conditions and decisions"
                    }
                ]
            elif intent == self.INTENT_DISCIPLINARY_ACTIONS:
                sub_queries = [
                    {
                        "step": 1,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 10 Non-Compliance and Escalation disciplinary actions sanctions termination",
                        "objective": "Retrieve documented disciplinary actions and escalation consequences"
                    },
                    {
                        "step": 2,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 5 Operating Procedure fair investigation due process",
                        "objective": "Retrieve fair investigation and due process procedures"
                    }
                ]
            elif intent == self.INTENT_SECURITY_CONTROLS:
                sub_queries = [
                    {
                        "step": 1,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 4 Mandatory Requirements confidential information security controls access classification",
                        "objective": "Retrieve mandatory confidentiality and security safeguards"
                    },
                    {
                        "step": 2,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 3 Policy Statement and Principles safeguarding data protection",
                        "objective": "Retrieve security principles and protection commitments"
                    }
                ]
            elif intent == self.INTENT_MANDATORY_REQUIREMENTS:
                sub_queries = [
                    {
                        "step": 1,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 4 Mandatory Requirements controls compliance obligations",
                        "objective": "Retrieve mandatory compliance obligations and requirements"
                    },
                    {
                        "step": 2,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 5 Operating Procedure evaluation criteria",
                        "objective": "Retrieve operational procedure criteria and steps"
                    }
                ]
            elif intent == self.INTENT_EXCEPTIONS_RESTRICTIONS:
                sub_queries = [
                    {
                        "step": 1,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 9 Exceptions written rationale register approval time-limited",
                        "objective": "Retrieve exception criteria, waivers, and time-limited approvals"
                    },
                    {
                        "step": 2,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 4 Mandatory Requirements restrictions",
                        "objective": "Retrieve mandatory baseline restrictions"
                    }
                ]
            elif intent == self.INTENT_REJECTION_APPEAL:
                sub_queries = [
                    {
                        "step": 1,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 5 Operating Procedure Step 3 review communicate decision record rationale",
                        "objective": "Retrieve decision communication and documented rationale"
                    },
                    {
                        "step": 2,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 4 Mandatory Requirements fair opportunity raise concerns contested matters",
                        "objective": "Retrieve employee rights to raise concerns and manager referral rules"
                    },
                    {
                        "step": 3,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 9 Exceptions Section 10 Non-Compliance exception register dispute escalation",
                        "objective": "Retrieve exception authorization and dispute escalation routes"
                    }
                ]
            else:  # INTENT_PROCEDURE or standard
                sub_queries = [
                    {
                        "step": 1,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 5 Operating Procedure workflow steps",
                        "objective": "Retrieve chronological operating procedure steps"
                    },
                    {
                        "step": 2,
                        "policy_id": effective_pid,
                        "query": f"{effective_pid} {title} Section 4 Mandatory Requirements controls compliance",
                        "objective": "Retrieve mandatory compliance obligations"
                    }
                ]

            return {
                "is_complex": False,
                "strategy": "single_policy",
                "intent_type": intent,
                "target_sections": target_secs,
                "explanation": f"Targeted single-policy retrieval for {effective_pid} ({title}) focused on intent '{intent}' (Sections {', '.join(target_secs)}).",
                "target_policies": [effective_pid],
                "sub_queries": sub_queries
            }

        # 5. Standard Global Search
        return {
            "is_complex": False,
            "strategy": "standard",
            "intent_type": intent,
            "target_sections": target_secs,
            "explanation": f"Standard semantic and lexical hybrid retrieval targeting intent '{intent}'.",
            "target_policies": [],
            "sub_queries": [
                {
                    "step": 1,
                    "policy_id": None,
                    "query": query,
                    "objective": "Execute global hybrid search with cross-encoder reranking"
                }
            ]
        }

    def _resolve_entity_to_policy_id(self, text: str) -> Optional[str]:
        """Resolves natural language policy phrases or IDs to canonical Policy ID."""
        t_clean = text.strip().lower()

        # Check explicit ID (e.g. IT-001, HR-003)
        match = re.search(r"\b([A-Z]{2,5}-\d{3})\b", text.upper())
        if match and match.group(1) in metadata_registry.registry:
            return match.group(1)

        # Domain aliases
        MAPPING = {
            "information security": "IT-001",
            "network security": "IT-005",
            "expense reimbursement": "FIN-002",
            "financial delegation of authority": "FIN-012",
            "delegation of authority": "FIN-012",
            "financial delegation": "FIN-012",
            "corporate card": "FIN-010",
            "travel expense": "FIN-014",
            "workplace harassment": "HR-012",
            "anti-harassment policy": "HR-012",
            "anti harassment policy": "HR-012",
            "anti-harassment": "HR-012",
            "anti harassment": "HR-012",
            "harassment policy": "HR-012",
            "harassment": "HR-012",
            "leave request is rejected": "HR-003",
            "leave request": "HR-003",
            "leave application": "HR-003",
            "leave rejection": "HR-003",
            "leave is rejected": "HR-003",
            "leave management": "HR-003",
            "annual leave": "HR-003",
            "leave": "HR-003",
            "employee code of conduct": "HR-001",
            "code of conduct": "HR-001",
            "employee conduct": "HR-001",
            "system access request": "IT-002",
            "system permissions when they transfer": "IT-002",
            "system permissions": "IT-002",
            "permissions when they transfer": "IT-002",
            "transfer to another department": "IT-002",
            "access request": "IT-002",
            "system access": "IT-002",
            "access management": "IT-002",
            "identity and access": "IT-002",
            "final settlement after resignation": "HR-015",
            "final settlement": "HR-015",
            "after resignation": "HR-015",
            "resignation": "HR-015",
            "employee separation and offboarding": "HR-015",
            "employee separation": "HR-015",
            "separation and offboarding": "HR-015",
            "offboarding": "HR-015",
            "advertising review": "MKT-003",
            "advertising": "MKT-003",
            "whistleblower protection": "LEG-004",
            "whistleblower": "LEG-004",
            "privacy and data protection": "LEG-008",
            "data protection": "LEG-008",
            "employee privacy": "LEG-008",
            "confidential information": "IT-001",
            "disciplinary action": "HR-014",
            "employee grievance": "HR-013",
            "grievance": "HR-013",
            "anti bribery": "LEG-001",
            "anti-bribery": "LEG-001",
            "anti-corruption": "LEG-001",
            "fraud prevention": "FIN-013",
            "fraud risk reporting": "GOV-014",
            "records must procurement retain": "PROC-002",
            "records when evaluating a supplier": "PROC-002",
            "evaluating a supplier": "PROC-002",
            "supplier due diligence": "PROC-002",
            "due diligence": "PROC-002",
            "তথ্য নিরাপত্তা": "IT-001",
            "নেটওয়ার্ক নিরাপত্তা": "IT-005",
            "ব্যয় প্রতিদান": "FIN-002",
            "খরচ পরিশোধ": "FIN-002",
            "আর্থিক অনুমোদন": "FIN-012",
            "ছুটি": "HR-003",
            "ছুটির আবেদন": "HR-003",
            "কর্মক্ষেত্রে হয়রানি": "HR-012",
            "হয়রানি": "HR-012",
            "কর্মচারী আচরণবিধি": "HR-001",
            "আচরণবিধি": "HR-001",
            "সিস্টেম পারমিশন": "IT-002",
            "সিস্টেম অ্যাক্সেস": "IT-002",
            "পারমিশন": "IT-002",
            "অ্যাক্সেস": "IT-002",
            "বদলি": "IT-002",
            "পদত্যাগ": "HR-015",
            "চূড়ান্ত নিষ্পত্তি": "HR-015",
            "নিষ্পত্তি": "HR-015",
            "সরবরাহকারী": "PROC-002",
            "প্রকিউরমেন্ট": "PROC-002",
            "প্রাইভেসি": "LEG-008",
            "ডেটা সুরক্ষা": "LEG-008",
            "হুইসেলব্লোয়ার": "LEG-004",
            "দুর্নীতি": "LEG-001",
            "জালিয়াতি": "FIN-013"
        }

        for alias, pid in MAPPING.items():
            if alias in t_clean:
                return pid

        for title, pid in metadata_registry.title_to_id.items():
            if title in t_clean or t_clean in title:
                return pid

        return None


query_decomposer = QueryDecomposer()
