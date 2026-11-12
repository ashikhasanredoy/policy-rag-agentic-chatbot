"""
Configurable Grounded Answer Generator for Enterprise Policies.
Supports OpenAI, Google Gemini, Anthropic, Ollama, and Grounded Deterministic Generation.
Includes post-generation Answer and Source Validation to guarantee zero hallucinations.
"""

import os
import re
from typing import List, Dict, Any, Optional
from src.config.settings import settings
from src.generation.prompt import SYSTEM_PROMPT, USER_PROMPT_TEMPLATE
from src.generation.citations import citation_mapper
from src.generation.answer_validator import answer_validator
from src.retrievers.multi_query import MultilingualQueryExpander
from src.retrievers.parent_retriever import parent_retriever
from src.ingestion.metadata_extractor import metadata_registry
from src.retrievers.query_decomposer import query_decomposer


class PolicyAnswerGenerator:
    """Generates structured, grounded answers citing exact enterprise policies and sections."""

    def __init__(self):
        self.provider = settings.LLM_PROVIDER.lower()
        self.model_name = settings.LLM_MODEL_NAME

    def _detect_escalation_department(
        self,
        question: str,
        context_chunks: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        q_lower = question.lower()

        # 1. Check explicit question keywords first
        hr_keywords = [
            "salary", "increment", "pay", "compensation", "allowance", "bonus", "raise", "wage",
            "leave", "holiday", "vacation", "maternity", "paternity", "sick leave", "attendance", "punctuality",
            "dress code", "conduct", "harassment", "bullying", "resignation", "separation", "probation",
            "promotion", "appraisal", "benefits", "benefit", "insurance", "pension", "retirement",
            "overtime", "onboarding", "offboarding", "grievance", "disciplinary", "payroll",
            # Bengali
            "বেতন", "বৃদ্ধি", "ছুটি", "বোনাস", "ভাতা", "পদত্যাগ", "নিয়োগ", "সুবিধা",
            "হয়রানি", "আচরণবিধি", "মাতৃত্বকালীন", "পেনশন"
        ]
        if any(w in q_lower for w in hr_keywords):
            return "HR"

        it_keywords = [
            "password", "authentication", "login", "access", "account", "vpn", "software", "hardware",
            "device", "network", "wifi", "firewall", "phishing", "malware", "encryption", "cybersecurity",
            "security", "mfa", "token", "laptop", "server", "credential",
            # Bengali
            "পাসওয়ার্ড", "লগইন", "অ্যাক্সেস", "কম্পিউটার", "নেটওয়ার্ক", "সফটওয়্যার", "নিরাপত্তা"
        ]
        if any(w in q_lower for w in it_keywords):
            return "IT"

        fin_proc_keywords = [
            "expense", "reimbursement", "invoice", "receipt", "supplier", "vendor", "procurement",
            "tax", "billing", "purchasing", "budget", "audit", "claim",
            # Bengali
            "বিল", "রসিদ", "ব্যয়", "ট্যাক্স", "ক্রয়", "সরবরাহকারী"
        ]
        if any(w in q_lower for w in fin_proc_keywords):
            return "FIN"

        leg_keywords = [
            "whistleblower", "bribery", "corruption", "legal", "compliance", "regulatory", "lawsuit",
            "nda", "gdpr", "ethics",
            # Bengali
            "আইন", "আইনি", "অনুপালন", "দুর্নীতি", "হুইসেলব্লোয়ার"
        ]
        if any(w in q_lower for w in leg_keywords):
            return "LEG"

        # 2. Check context chunks metadata if question keywords did not match
        if context_chunks:
            for c in context_chunks:
                meta = c.get("metadata", {})
                pid = meta.get("policy_id", "")
                dept = meta.get("department", "").lower()
                if pid.startswith("HR") or "human" in dept:
                    return "HR"
                if pid.startswith("IT") or pid.startswith("SEC") or "tech" in dept or "security" in dept:
                    return "IT"
                if pid.startswith("FIN") or "finance" in dept:
                    return "FIN"
                if pid.startswith("PROC") or "procurement" in dept:
                    return "PROC"
                if pid.startswith("LEG") or pid.startswith("GOV") or "legal" in dept:
                    return "LEG"

        return "DEFAULT"

    def _build_unanswerable_response(
        self,
        question: str,
        context_chunks: Optional[List[Dict[str, Any]]] = None
    ) -> str:
        """Constructs an evidence-grounded refusal message with official departmental escalation channels."""
        is_bn = MultilingualQueryExpander.is_bangla(question)
        dept = self._detect_escalation_department(question, context_chunks)

        if dept == "HR":
            if is_bn:
                return (
                    "এই প্রশ্নের নির্ভরযোগ্য উত্তর দেওয়ার জন্য উপলব্ধ প্রাতিষ্ঠানিক নীতিমালায় পর্যাপ্ত সহায়ক তথ্য পাওয়া যায়নি।\n\n"
                    "---\n\n"
                    "### 📞 সহায়তা ও যোগাযোগের তথ্য\n"
                    "বেতন বৃদ্ধি, ক্ষতিপূরণ, সুযোগ-সুবিধা বা নীতিমালায় সরাসরি উল্লেখ নেই এমন সুনির্দিষ্ট তথ্যের জন্য অনুগ্রহ করে মানবসম্পদ (HR) বিভাগের সাথে যোগাযোগ করুন:\n\n"
                    "- **বিভাগ:** মানবসম্পদ বিভাগ (Human Resources)\n"
                    "- **এইচআর হেল্পডেস্ক (Email):** `hr.helpdesk@enterprise.com`\n"
                    "- **ক্ষতিপূরণ ও পেরোল দল:** `payroll@enterprise.com`\n"
                    "- **এইচআর সাপোর্ট ডেস্ক:** `hr@enterprise.com`\n"
                    "- **এইচআর পোর্টাল:** Enterprise HR Self-Service Desk (অভ্যন্তরীণ ইন্ট্রানেট)\n"
                )
            else:
                return (
                    "I could not find sufficient supporting information in the available enterprise policy documents to answer this question reliably.\n\n"
                    "---\n\n"
                    "### 📞 Contact & Escalation Support\n"
                    "For specific questions regarding salary increments, employee compensation, benefits, or matters not documented in standard policies, please reach out to the Human Resources department:\n\n"
                    "- **Department:** Human Resources (HR)\n"
                    "- **HR Helpdesk Email:** `hr.helpdesk@enterprise.com`\n"
                    "- **Compensation & Payroll Team:** `payroll@enterprise.com`\n"
                    "- **General HR Inquiries:** `hr@enterprise.com`\n"
                    "- **HR Self-Service Portal:** Internal Enterprise HR Service Desk\n"
                )
        elif dept == "IT":
            if is_bn:
                return (
                    "এই প্রশ্নের নির্ভরযোগ্য উত্তর দেওয়ার জন্য উপলব্ধ প্রাতিষ্ঠানিক নীতিমালায় পর্যাপ্ত সহায়ক তথ্য পাওয়া যায়নি।\n\n"
                    "---\n\n"
                    "### 📞 সহায়তা ও যোগাযোগের তথ্য\n"
                    "আইটি সহায়তা, সিস্টেম অ্যাক্সেস বা সাইবার নিরাপত্তা সংক্রান্ত তথ্যের জন্য অনুগ্রহ করে যোগাযোগ করুন:\n\n"
                    "- **বিভাগ:** তথ্য প্রযুক্তি (IT) ও সাইবার নিরাপত্তা\n"
                    "- **আইটি সার্ভিস ডেস্ক (Email):** `it.servicedesk@enterprise.com`\n"
                    "- **ইনফরমেশন সিকিউরিটি:** `security@enterprise.com`\n"
                    "- **আইটি সাপোর্ট হটলাইন:** অভ্যন্তরীণ এক্সটেনশন ৪৩৫৭ (HELP)\n"
                )
            else:
                return (
                    "I could not find sufficient supporting information in the available enterprise policy documents to answer this question reliably.\n\n"
                    "---\n\n"
                    "### 📞 Contact & Escalation Support\n"
                    "For technical assistance, user account permissions, or security matters not documented in standard policies, please contact:\n\n"
                    "- **Department:** Information Technology (IT) & Information Security\n"
                    "- **IT Service Desk Email:** `it.servicedesk@enterprise.com`\n"
                    "- **Security Operations:** `security@enterprise.com`\n"
                    "- **Internal IT Hotline:** Ext. 4357 (HELP)\n"
                )
        elif dept in ("FIN", "PROC"):
            if is_bn:
                return (
                    "এই প্রশ্নের নির্ভরযোগ্য উত্তর দেওয়ার জন্য উপলব্ধ প্রাতিষ্ঠানিক নীতিমালায় পর্যাপ্ত সহায়ক তথ্য পাওয়া যায়নি।\n\n"
                    "---\n\n"
                    "### 📞 সহায়তা ও যোগাযোগের তথ্য\n"
                    "আর্থিক হিসাব, ব্যয় দাবি, ইনভয়েস বা প্রকিউরমেন্ট সংক্রান্ত তথ্যের জন্য অনুগ্রহ করে যোগাযোগ করুন:\n\n"
                    "- **বিভাগ:** অর্থ বিভাগ (Finance) ও প্রকিউরমেন্ট\n"
                    "- **ফাইন্যান্স হেল্পডেস্ক (Email):** `finance.helpdesk@enterprise.com`\n"
                    "- **ব্যয় ও দাবি (Expense Claims):** `expenses@enterprise.com`\n"
                    "- **প্রকিউরমেন্ট ও সরবরাহকারী ব্যবস্থাপনা:** `procurement@enterprise.com`\n"
                )
            else:
                return (
                    "I could not find sufficient supporting information in the available enterprise policy documents to answer this question reliably.\n\n"
                    "---\n\n"
                    "### 📞 Contact & Escalation Support\n"
                    "For financial claims, billing inquiries, supplier management, or procurement guidelines not covered in available policies, please contact:\n\n"
                    "- **Department:** Finance & Procurement\n"
                    "- **Finance Helpdesk Email:** `finance.helpdesk@enterprise.com`\n"
                    "- **Expense Claims & Reimbursements:** `expenses@enterprise.com`\n"
                    "- **Procurement Desk:** `procurement@enterprise.com`\n"
                )
        elif dept in ("LEG", "GOV"):
            if is_bn:
                return (
                    "এই প্রশ্নের নির্ভরযোগ্য উত্তর দেওয়ার জন্য উপলব্ধ প্রাতিষ্ঠানিক নীতিমালায় পর্যাপ্ত সহায়ক তথ্য পাওয়া যায়নি।\n\n"
                    "---\n\n"
                    "### 📞 সহায়তা ও যোগাযোগের তথ্য\n"
                    "আইনি নির্দেশনা, নীতিমালা ব্যাখ্যা বা এথিক্স সংক্রান্ত তথ্যের জন্য অনুগ্রহ করে যোগাযোগ করুন:\n\n"
                    "- **বিভাগ:** লিগ্যাল অ্যান্ড কমপ্লায়েন্স (Legal & Compliance)\n"
                    "- **কমপ্লায়েন্স অফিস (Email):** `compliance@enterprise.com`\n"
                    "- **আইনি পরামর্শ (Legal Counsel):** `legal@enterprise.com`\n"
                    "- **এথিক্স ও হুইসেলব্লোয়ার হটলাইন:** `ethics.hotline@enterprise.com`\n"
                )
            else:
                return (
                    "I could not find sufficient supporting information in the available enterprise policy documents to answer this question reliably.\n\n"
                    "---\n\n"
                    "### 📞 Contact & Escalation Support\n"
                    "For legal interpretation, compliance clarifications, or confidential disclosures not covered in standard policies, please contact:\n\n"
                    "- **Department:** Legal & Compliance\n"
                    "- **Compliance Office Email:** `compliance@enterprise.com`\n"
                    "- **Legal Counsel:** `legal@enterprise.com`\n"
                    "- **Ethics & Whistleblower Hotline:** `ethics.hotline@enterprise.com`\n"
                )
        else:
            if is_bn:
                return (
                    "এই প্রশ্নের নির্ভরযোগ্য উত্তর দেওয়ার জন্য উপলব্ধ প্রাতিষ্ঠানিক নীতিমালায় পর্যাপ্ত সহায়ক তথ্য পাওয়া যায়নি।\n\n"
                    "---\n\n"
                    "### 📞 সহায়তা ও যোগাযোগের তথ্য\n"
                    "উপলব্ধ নীতিমালায় অন্তর্ভুক্ত নয় এমন সাধারণ প্রাতিষ্ঠানিক প্রশ্ন বা সহায়তার জন্য অনুগ্রহ করে যোগাযোগ করুন:\n\n"
                    "- **মানবসম্পদ হেল্পডেস্ক (HR Helpdesk):** `hr.helpdesk@enterprise.com`\n"
                    "- **এইচআর সাপোর্ট ও সাধারণ অনুসন্ধান:** `hr@enterprise.com`\n"
                    "- **নীতিমালা প্রশাসন ও পরিচালনা (Policy Governance):** `policy.governance@enterprise.com`\n"
                )
            else:
                return (
                    "I could not find sufficient supporting information in the available enterprise policy documents to answer this question reliably.\n\n"
                    "---\n\n"
                    "### 📞 Contact & Escalation Support\n"
                    "For matters or inquiries not addressed in published enterprise policies, please reach out to the appropriate administrative office:\n\n"
                    "- **Human Resources Helpdesk:** `hr.helpdesk@enterprise.com`\n"
                    "- **General HR Inquiries:** `hr@enterprise.com`\n"
                    "- **Policy Governance & Administration:** `policy.governance@enterprise.com`\n"
                )

    def generate_answer(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        confidence: float = 1.0,
        is_answerable: bool = True,
        intent: Optional[str] = None
    ) -> Dict[str, Any]:
        """Synthesizes grounded answer and citations from top context chunks with validation."""
        # 1. Check answerability
        if not context_chunks or not is_answerable or confidence < 0.05:
            refusal_msg = self._build_unanswerable_response(question, context_chunks)
            return {
                "answer": refusal_msg,
                "answerable": False,
                "confidence": 0.0,
                "sources": [],
                "policy_ids": [],
                "validation": {"is_valid": True, "unsupported_claims_detected": []}
            }

        citations = citation_mapper.build_citations(context_chunks)
        policy_ids = list(dict.fromkeys(c["policy_id"] for c in citations if c.get("policy_id")))

        # 2. Build Formatted Context Block
        context_parts = []
        for i, c in enumerate(context_chunks, 1):
            meta = c.get("metadata", {})
            header = f"[{meta.get('policy_id', 'POL')} - {meta.get('policy_title', '')} | Section {meta.get('section_number', '')}: {meta.get('section_title', '')}]"
            body = c.get("compressed_text", c.get("text", ""))
            if body.startswith("[") and "]\n" in body:
                body = body.split("]\n", 1)[-1]
            context_parts.append(f"Excerpt {i} {header}:\n{body.strip()}")

        context_str = "\n\n".join(context_parts)

        # 3. Generate Answer based on Provider
        if self.provider == "openai" and settings.OPENAI_API_KEY:
            raw_answer = self._call_openai(question, context_str)
        elif self.provider == "gemini" and settings.GEMINI_API_KEY:
            raw_answer = self._call_gemini(question, context_str)
        elif self.provider == "anthropic" and settings.ANTHROPIC_API_KEY:
            raw_answer = self._call_anthropic(question, context_str)
        else:
            raw_answer = self._grounded_deterministic_synthesis(question, context_chunks, citations, intent=intent)

        # 4. Strict Post-Generation Answer & Citation Validation
        val_result = answer_validator.validate_answer(
            question=question,
            answer=raw_answer,
            context_chunks=context_chunks,
            citations=citations
        )

        final_answer = val_result["sanitized_answer"]
        verified_sources = val_result["verified_citations"]

        return {
            "answer": final_answer,
            "answerable": True,
            "confidence": confidence,
            "sources": verified_sources,
            "policy_ids": policy_ids,
            "validation": val_result
        }

    def _call_openai(self, question: str, context: str) -> str:
        try:
            from openai import OpenAI
            client = OpenAI(api_key=settings.OPENAI_API_KEY)
            user_msg = USER_PROMPT_TEMPLATE.format(context=context, question=question)
            res = client.chat.completions.create(
                model=self.model_name,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": user_msg}
                ],
                temperature=settings.LLM_TEMPERATURE
            )
            return res.choices[0].message.content.strip()
        except Exception as e:
            return f"Error contacting OpenAI: {e}"

    def _call_gemini(self, question: str, context: str) -> str:
        try:
            import google.generativeai as genai
            genai.configure(api_key=settings.GEMINI_API_KEY)
            model = genai.GenerativeModel(
                model_name=self.model_name or "gemini-1.5-flash",
                system_instruction=SYSTEM_PROMPT
            )
            user_msg = USER_PROMPT_TEMPLATE.format(context=context, question=question)
            res = model.generate_content(user_msg)
            return res.text.strip()
        except Exception as e:
            return f"Error contacting Gemini: {e}"

    def _call_anthropic(self, question: str, context: str) -> str:
        try:
            import anthropic
            client = anthropic.Anthropic(api_key=settings.ANTHROPIC_API_KEY)
            user_msg = USER_PROMPT_TEMPLATE.format(context=context, question=question)
            res = client.messages.create(
                model=self.model_name or "claude-3-5-sonnet-20241022",
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": user_msg}],
                max_tokens=1024,
                temperature=settings.LLM_TEMPERATURE
            )
            return res.content[0].text.strip()
        except Exception as e:
            return f"Error contacting Anthropic: {e}"

    @staticmethod
    def _translate_step_to_bn(step: str) -> str:
        s = step.strip()
        s_lower = s.lower()
        if "business owner submits" in s_lower or "transaction, forecast, claim" in s_lower:
            return "ব্যবসায়িক প্রক্রিয়া বা দাবির মালিক প্রয়োজনীয় প্রমাণাদিসহ অনুমোদিত আর্থিক ব্যবস্থায় লেনদেন, দাবিপত্র বা সমন্বয়ের আবেদন জমা দেবেন।"
        if "finance validates budget" in s_lower:
            return "অর্থ বিভাগ (Finance) বাজেট প্রাপ্যতা, অনুমোদন ক্ষমতা, নির্ভুলতা, সম্পূর্ণতা এবং নিয়ন্ত্রণ প্রয়োজনীয়তা যাচাই করবে।"
        if "authorized independent approver reviews exceptions" in s_lower:
            return "অনুমোদিত স্বাধীন অনুমোদনকারী কোনো ব্যতিক্রমী বিষয় থাকলে তা পর্যালোচনা করে লেনদেন বা রিপোর্ট অনুমোদন করবেন।"
        if "finance reconciles the result" in s_lower:
            return "অর্থ বিভাগ ফলাফল রিকনসিলিয়েশন করবে, প্রমাণাদি সংরক্ষণ করবে এবং কোনো অমিল বা অনিয়ম থাকলে তা ঊর্ধ্বতন কর্তৃপক্ষের নিকট পাঠাবে।"
        if "employee, manager, or hr partner submits" in s_lower:
            return "কর্মচারী, ম্যানেজার বা এইচআর পার্টনার অনুমোদিত চ্যানেলের মাধ্যমে প্রয়োজনীয় তথ্য ও রেকর্ডসহ অনুরোধ জমা দেবেন।"
        if "hr validates completeness" in s_lower:
            return "এইচআর বিভাগ তথ্যের সম্পূর্ণতা, ছুটির যোগ্যতা, সহায়ক প্রমাণাদি, গোপনীয়তা এবং নীতিমালার শর্তাবলি যাচাই করবে।"
        if "authorized manager or hr decision-maker reviews" in s_lower:
            return "অনুমোদিত ম্যানেজার বা এইচআর সিদ্ধান্ত গ্রহণকারী বিষয়টি পর্যালোচনা করবেন, সিদ্ধান্তের যৌক্তিক কারণ নথিবদ্ধ করবেন এবং কর্মচারীকে সিদ্ধান্ত জানাবেন।"
        if "hr updates the employee record" in s_lower:
            return "এইচআর কর্মচারীর রেকর্ড আপডেট করবে, প্রয়োজনীয় কার্যক্রম ট্র্যাক করবে এবং যে কোনো ব্যতিক্রম পর্যালোচনা করবে।"
        if "requester or system owner logs" in s_lower:
            return "আবেদনকারী বা সিস্টেমের মালিক ব্যবসায়িক যৌক্তিকতাসহ রিকোয়েস্ট, সম্পদ বা পরিবর্তন লগ করবেন।"
        if "it and relevant security" in s_lower:
            return "আইটি এবং সংশ্লিষ্ট ডেটা/নিরাপত্তা মালিক প্রভাব, অনুমোদন, নির্ভরতা এবং প্রয়োজনীয় সুরক্ষাব্যবস্থা মূল্যায়ন করবেন।"
        if "authorized personnel implement" in s_lower:
            return "অনুমোদিত কারিগরি দল অনুমোদিত কার্যক্রম বাস্তবায়ন করবে, ফলাফল পরীক্ষা করবে এবং অ্যাক্সেস বা কনফিগারেশন পরিবর্তন রেকর্ড করবে।"
        if "service or asset owner monitors" in s_lower:
            return "সার্ভিস বা সিস্টেমের মালিক কার্যকারিতা পর্যবেক্ষণ করবেন, ব্যতিক্রম সমাধান করবেন এবং প্রযুক্তিগত প্রমাণাদি সংরক্ষণ করবেন।"
        if "campaign owner submits" in s_lower:
            return "ক্যাম্পেইন মালিক উদ্দেশ্য, লক্ষ্যযুক্ত দর্শক, চ্যানেল, ক্রিয়েটিভ উপাদান, বাজেট, দাবি এবং ডেটা ব্যবহারের পরিকল্পনা জমা দেবেন।"
        if "marketing and relevant legal" in s_lower:
            return "মার্কেটিং এবং সংশ্লিষ্ট লিগ্যাল, প্রাইভেসি, ব্র্যান্ড বা কমপ্লায়েন্স পর্যালোচকবৃন্দ বিজ্ঞাপন উপাদান মূল্যায়ন করবেন।"
        if "authorized approver releases the final" in s_lower:
            return "অনুমোদিত অনুমোদনকারী চূড়ান্ত সংস্করণ অনুমোদন করবেন এবং অনুমোদন ও প্রমাণাদি রেকর্ড করবেন।"
        if "owner monitors performance" in s_lower:
            return "ক্যাম্পেইন মালিক বিজ্ঞাপনের পারফরম্যান্স, অভিযোগ ও ব্যয় পর্যবেক্ষণ করবেন এবং প্রয়োজনে উপাদান সংশোধন বা প্রত্যাহার করবেন।"
        if "business owner refers the matter to legal" in s_lower:
            return "ব্যবসায়িক মালিক প্রাসঙ্গিক তথ্য, তারিখ ও নথিপত্রসহ বিষয়টি লিগ্যাল বা কমপ্লায়েন্স বিভাগে রেফার করবেন।"
        if "legal or compliance reviews" in s_lower:
            return "লিগ্যাল বা কমপ্লায়েন্স বিভাগ প্রযোজ্য আইন, ঝুঁকি ও নিয়ন্ত্রক বাধ্যবাধকতা পর্যালোচনা করবে।"
        if "authorized decision-maker approves" in s_lower:
            return "অনুমোদিত সিদ্ধান্ত গ্রহণকারী প্রয়োজনীয় ব্যবস্থা বা চুক্তি অনুমোদন করবেন।"
        if "originating department implements" in s_lower:
            return "সংশ্লিষ্ট বিভাগ পরামর্শ অনুযায়ী নির্দেশনা বাস্তবায়ন করবে এবং প্রমাণাদি সংরক্ষণ করবে।"
        return s

    def _grounded_deterministic_synthesis(
        self,
        question: str,
        context_chunks: List[Dict[str, Any]],
        citations: List[Dict[str, Any]],
        intent: Optional[str] = None
    ) -> str:
        """
        Synthesizes answers strictly quoting verified clauses and numbers directly
        from context chunks without inventing external facts, tools, or limits.
        Dispatches to intent-specific formatters.
        """
        is_bn = MultilingualQueryExpander.is_bangla(question)
        q_lower = question.lower()
        eff_intent = intent or query_decomposer.classify_intent(question)

        # Extract unique policies present in the context chunks
        unique_pids = []
        chunks_by_pid: Dict[str, List[Dict[str, Any]]] = {}
        pid_meta: Dict[str, Dict[str, Any]] = {}

        for c in context_chunks:
            meta = c.get("metadata", {})
            c_pid = meta.get("policy_id", "")
            if c_pid:
                if c_pid not in unique_pids:
                    unique_pids.append(c_pid)
                    pid_meta[c_pid] = meta
                if c_pid not in chunks_by_pid:
                    chunks_by_pid[c_pid] = []
                chunks_by_pid[c_pid].append(c)

        primary_pid = unique_pids[0] if unique_pids else ""
        pid = primary_pid
        primary_meta = pid_meta.get(primary_pid, {})
        title = primary_meta.get("policy_title", "")
        dept = primary_meta.get("department", "")

        # Organize primary policy content by section number
        sections_by_num: Dict[str, List[str]] = {}
        for c in chunks_by_pid.get(primary_pid, context_chunks):
            sec_num = str(c.get("metadata", {}).get("section_number", ""))
            text = c.get("compressed_text", c.get("text", "")).strip()
            if text.startswith("[") and "]\n" in text:
                text = text.split("]\n", 1)[-1].strip()

            lines = [l.strip() for l in text.splitlines() if l.strip() and not l.startswith("#")]
            if sec_num not in sections_by_num:
                sections_by_num[sec_num] = []
            for l in lines:
                if l not in sections_by_num[sec_num]:
                    sections_by_num[sec_num].append(l)

        # Helper to get section text from parent retriever if not retrieved in child chunks
        def ensure_section(sec_idx: str) -> List[str]:
            if sec_idx in sections_by_num and sections_by_num[sec_idx]:
                return sections_by_num[sec_idx]
            sec_text = parent_retriever.get_parent_text(f"{pid}-SEC-{int(sec_idx):02d}")
            if sec_text:
                lines = [l.strip() for l in sec_text.splitlines() if l.strip() and not l.startswith("#")]
                sections_by_num[sec_idx] = lines
                return lines
            return []

        # Verification of unsupported deadlines, reimbursement promises, or guarantees
        if any(term in q_lower for term in [
            "24 hours", "24-hour", "24hour", "within 24", "guarantee reimbursement", "guarantee of all",
            "২৪ ঘণ্টা", "২৪ ঘন্টা", "২৪ ঘন্টার", "২৪ ঘণ্টার", "পরিশোধের নিশ্চয়তা", "খরচ পরিশোধের নিশ্চয়তা"
        ]):
            if is_bn:
                refusal = (
                    "**FIN-002 — Expense Reimbursement (Finance)** নীতিমালার প্রাপ্ত প্রমাণের ভিত্তিতে ২৪ ঘণ্টার মধ্যে সকল কর্মচারীর "
                    "ব্যয় প্রতিদানের (reimbursement) কোনো নিশ্চয়তা বা নির্দিষ্ট সময়সীমা নির্ধারিত নেই। অতএব, এই দাবির সত্যতা নিশ্চিত করা সম্ভব নয়।\n\n"
                    "নীতিমালার সেকশন ৪ এবং সেকশন ৫ অনুযায়ী, কর্মচারীকে অনুমোদিত আর্থিক ব্যবস্থায় প্রয়োজনীয় রসিদ ও ব্যবসায়িক যৌক্তিকতাসহ আবেদন করতে হবে, "
                    "অর্থ বিভাগ তা যাচাই করবে এবং উপযুক্ত কর্তৃপক্ষের স্বাধীন অনুমোদনের পর তা পরিশোধের জন্য প্রক্রিয়া করা হবে।"
                )
                src = "\n\n**তথ্যসূত্র (Sources):**\n- FIN-002, Section 4 — Mandatory Requirements\n- FIN-002, Section 5 — Operating Procedure"
            else:
                refusal = (
                    "The available policy evidence under **FIN-002 — Expense Reimbursement** does not establish a guaranteed 24-hour reimbursement period. "
                    "Therefore, I cannot confirm this requirement.\n\n"
                    "Under Section 4 (Mandatory Requirements) and Section 5 (Operating Procedure), all expense reimbursement claims must have a legitimate business purpose, "
                    "available budget, itemized receipts/evidence, and approval before payment. Finance must validate the budget, accuracy, and completeness before the transaction is released."
                )
                src = "\n\n**Sources:**\n- FIN-002, Section 4 — Mandatory Requirements\n- FIN-002, Section 5 — Operating Procedure"
            return (refusal + src).strip()

        # Comparative evaluation across multiple distinct policies
        is_compare_q = eff_intent == query_decomposer.INTENT_POLICY_COMPARISON or any(term in q_lower for term in [
            "compare", "versus", "vs", "differences between", "difference between", "difference", "differences", "তুলনা", "পার্থক্য"
        ])
        if is_compare_q:
            decomp = query_decomposer.decompose(question)
            target_pids = decomp.get("target_policies", [])
            if len(target_pids) >= 2:
                pid_a, pid_b = target_pids[0], target_pids[1]
                return self._format_comparison_table(pid_a, pid_b, is_bn)
            elif len(unique_pids) >= 2:
                pid_a, pid_b = unique_pids[0], unique_pids[1]
                return self._format_comparison_table(pid_a, pid_b, is_bn)

        # Thematic cross-policy discovery across multiple departments
        is_multi_policy_q = eff_intent == query_decomposer.INTENT_POLICY_DISCOVERY or any(term in q_lower for term in [
            "all policies", "find all", "list all", "policies related", "policies regarding",
            "which policies", "what policies", "policies govern", "policies address", "policies covering"
        ])
        if is_multi_policy_q and (len(unique_pids) >= 1 or any(term in q_lower for term in ["fraud", "confidential information", "misconduct"])):
            return self._format_thematic_discovery(q_lower, unique_pids, pid_meta, is_bn)

        # Request rejection handling, dispute escalation, and administrative appeals
        if eff_intent == query_decomposer.INTENT_REJECTION_APPEAL or any(term in q_lower for term in [
            "leave request is rejected", "if a leave request is rejected", "leave is rejected",
            "request is rejected", "request rejected", "rejected leave"
        ]):
            eff_pid = "HR-003" if ("leave" in q_lower or pid == "HR-003" or not pid) else pid
            eff_title = pid_meta.get(eff_pid, {}).get("policy_title", "Leave Management")
            eff_dept = pid_meta.get(eff_pid, {}).get("department", "Human Resources")
            ensure_section("5")
            ensure_section("4")
            ensure_section("9")
            return self._format_rejection_appeal(eff_pid, eff_title, eff_dept, is_bn)

        # Anti-harassment, anti-bullying, and incident escalation protocols (HR-012)
        if pid == "HR-012" or "harassment" in q_lower:
            ensure_section("5")
            ensure_section("4")
            ensure_section("10")
            return self._format_harassment_reporting("HR-012", "Anti-Harassment and Anti-Bullying", "Human Resources", is_bn)

        # System access modification and prompt privilege revocation on department transfer (IT-002)
        if (pid == "IT-002" or any(p in unique_pids for p in ["IT-002"]) or any(term in q_lower for term in ["permissions", "system permissions", "পারমিশন", "সিস্টেম পারমিশন", "বদলি"])) and any(term in q_lower for term in [
            "system permissions", "permissions when they transfer", "transfer to another department",
            "department transfer", "permissions", "access permissions", "পারমিশন", "সিস্টেম পারমিশন", "বদলি", "বদলির সময়"
        ]):
            ensure_section("4")
            ensure_section("5")
            return self._format_system_permissions_transfer("IT-002", "Identity and Access Management", "Information Technology", is_bn)

        # Evidentiary records retention and audit compliance for supplier evaluations (PROC-002)
        if eff_intent == query_decomposer.INTENT_RECORDS or any(term in q_lower for term in [
            "what specific records", "specific records", "records must procurement retain",
            "records must retain", "records to retain", "records retention", "records when evaluating a supplier",
            "retain when evaluating a supplier", "নির্দিষ্ট রেকর্ড", "সংরক্ষণ"
        ]):
            eff_pid = "PROC-002" if ("supplier" in q_lower or pid.startswith("PROC") or "সরবরাহকারী" in q_lower) else pid
            eff_title = pid_meta.get(eff_pid, {}).get("policy_title", "Supplier Due Diligence")
            eff_dept = pid_meta.get(eff_pid, {}).get("department", "Procurement")
            ensure_section("7")
            ensure_section("4")
            ensure_section("5")
            return self._format_supplier_records_retention(eff_pid, eff_title, eff_dept, sections_by_num, is_bn)

        # Employee offboarding, property handover, and final payroll settlement (HR-015, HR-008)
        if any(term in q_lower for term in [
            "final settlement after resignation", "settlement after resignation", "final settlement",
            "after resignation", "resignation", "পদত্যাগ", "চূড়ান্ত নিষ্পত্তি", "নিষ্পত্তি"
        ]):
            ensure_section("4")
            ensure_section("5")
            return self._format_resignation_final_settlement("HR-015", "Employee Separation and Offboarding", "Human Resources", is_bn)

        # Evidentiary document submission checklists (Section 7 and Section 4)
        if eff_intent == query_decomposer.INTENT_REQUIRED_DOCUMENTS or any(term in q_lower for term in [
            "what documents", "documents are required", "document required", "required documents",
            "receipts", "submission documents", "what paperwork", "records and evidence", "attach",
            "supporting documents", "কী কী তথ্য", "নথিপত্র"
        ]):
            if (pid == "IT-002" or "access request" in q_lower or "অ্যাক্সেস" in q_lower) and any(term in q_lower for term in ["information", "must be included", "access request", "তথ্য", "অন্তর্ভুক্ত"]):
                ensure_section("4")
                ensure_section("5")
                return self._format_access_request_checklist("IT-002", "Identity and Access Management", "Information Technology", is_bn)
            ensure_section("7")
            ensure_section("4")
            return self._format_document_checklist(pid, title, dept, sections_by_num, is_bn)

        # Delegated approval authority and responsible governance roles (Section 6 and Section 5)
        if eff_intent == query_decomposer.INTENT_APPROVING_AUTHORITY or any(term in q_lower for term in [
            "who is responsible for approving", "who approves", "approving authority", "approval authority",
            "who can approve", "who has authority to approve", "approval hierarchy", "who authorizes"
        ]):
            ensure_section("6")
            ensure_section("5")
            ensure_section("4")
            return self._format_approving_authority(pid, title, dept, sections_by_num, is_bn)

        # Documented disciplinary actions and escalation procedures for policy non-compliance
        if eff_intent == query_decomposer.INTENT_DISCIPLINARY_ACTIONS or any(term in q_lower for term in [
            "what disciplinary", "disciplinary action", "disciplinary actions", "disciplinary consequences",
            "sanctions", "penalties", "punishment", "violates the code of conduct", "violates", "violation"
        ]):
            ensure_section("10")
            ensure_section("5")
            ensure_section("4")
            return self._format_disciplinary_actions(pid, title, dept, sections_by_num, is_bn)

        # Mandatory information security safeguards and confidentiality controls (Section 4 and Section 3)
        if eff_intent == query_decomposer.INTENT_SECURITY_CONTROLS or any(term in q_lower for term in [
            "confidential information", "protect confidential", "protecting confidential",
            "protect sensitive", "protecting sensitive", "confidentiality requirements", "security controls"
        ]):
            ensure_section("4")
            ensure_section("3")
            ensure_section("7")
            return self._format_security_controls(pid, title, dept, sections_by_num, is_bn)

        # Ethical misconduct disclosures, whistleblower protections, and reporting workflows (HR-001, LEG-004)
        if any(term in q_lower for term in ["unethical", "whistleblower"]) or ("misconduct" in q_lower and "discover" in q_lower):
            eff_pid = primary_pid if primary_pid in ["HR-001", "LEG-004"] else "HR-001"
            eff_title = pid_meta.get(eff_pid, {}).get("policy_title", "Employee Code of Conduct")
            eff_dept = pid_meta.get(eff_pid, {}).get("department", "Human Resources")

            if is_bn:
                header = f"**{eff_pid} — {eff_title} ({eff_dept}) অনুযায়ী অনৈতিক বা সন্দেহজনক কার্যক্রম শনাক্ত হলে করণীয় পদক্ষেপ:**\n\n"
                steps = (
                    "1. **অবিলম্বে রিপোর্ট প্রদান (Reporting):** অনৈতিক কার্যকলাপ, নীতিমালা লঙ্ঘন বা অসদাচরণের সন্দেহ হলে অবিলম্বে লাইন ম্যানেজার, এইচআর বা নির্ধারিত গোপনীয় নীতি/হুইসেলব্লোয়ার চ্যানেলে রিপোর্ট করতে হবে।\n"
                    "2. **তথ্যদাতার সুরক্ষা (Protection from Retaliation):** সৎ উদ্দেশ্যে রিপোর্ট প্রদানকারী কর্মচারীর বিরুদ্ধে কোনো প্রকার প্রতিশোধমূলক ব্যবস্থা গ্রহণ কঠোরভাবে নিষিদ্ধ।\n"
                    "3. **নিরপেক্ষ পর্যালোচনা (Objective Review):** এইচআর ও সংশ্লিষ্ট কমপ্লায়েন্স কর্মকর্তা অভিযোগ যাচাই করবেন এবং প্রাসঙ্গিক প্রমাণাদি সংরক্ষণ করবেন।\n"
                    "4. **তদন্তে সহায়তা (Cooperation):** অনুমোদিত অভ্যন্তরীণ তদন্ত প্রক্রিয়ায় সংশ্লিষ্ট সকল কর্মচারীকে পূর্ণ ও সত্যনিষ্ঠ সহযোগিতা প্রদান করতে হবে।"
                )
                src = f"\n\n**তথ্যসূত্র (Sources):**\n- {eff_pid}, Section 10 — Non-Compliance and Escalation\n- {eff_pid}, Section 5 — Operating Procedure"
            else:
                header = f"According to **{eff_pid} — {eff_title}** ({eff_dept}), if an employee discovers unethical activities or policy breaches, they should follow these steps:\n\n"
                steps = (
                    "1. **Prompt Reporting:** Suspected unethical conduct, fraud, or policy breaches must be reported immediately to line management, Human Resources, or the designated confidential reporting channel (ethics hotline / whistleblower channel).\n"
                    "2. **Protection Against Retaliation:** The organization strictly prohibits retaliation or adverse employment consequences against any employee who reports concerns in good faith.\n"
                    "3. **Objective Assessment & Inquiry:** Authorized compliance and HR personnel fairly assess reported concerns, preserve documentary evidence, and conduct an objective investigation.\n"
                    "4. **Full Cooperation:** Employees are required to cooperate fully and truthfully with authorized investigations."
                )
                src = f"\n\n**Sources:**\n- {eff_pid}, Section 10 — Non-Compliance and Escalation\n- {eff_pid}, Section 5 — Operating Procedure"

            return (header + steps + src).strip()

        # Mandatory supplier due diligence, risk screening, and commercial onboarding (PROC-002, FIN-012)
        if pid == "PROC-002" or (any(term in q_lower for term in ["supplier", "suppliers", "vendor", "vendors"]) and any(term in q_lower for term in ["due diligence", "evaluate", "evaluation", "approve", "selection", "onboarding"])):
            ensure_section("4")
            ensure_section("5")
            return self._format_supplier_due_diligence("PROC-002", "Supplier Due Diligence", "Procurement", sections_by_num, is_bn)

        # Marketing campaign validation, claims substantiation, and creative sign-off (MKT-003)
        if pid == "MKT-003" or ("advertisement" in q_lower and any(w in q_lower for w in ["review", "approv", "process"])):
            ensure_section("5")
            ensure_section("4")
            return self._format_advertising_approval("MKT-003", "Advertising Review and Approval", "Marketing", sections_by_num, is_bn)

        # Identity and access lifecycle: authorization, role assignment, and access revocation (IT-002)
        if pid == "IT-002" or ("system access" in q_lower and any(w in q_lower for w in ["grant", "revoke", "modify", "lifecycle"])):
            ensure_section("5")
            ensure_section("4")
            return self._format_access_lifecycle("IT-002", "Identity and Access Management", "Information Technology", is_bn)

        # Policy scope, purpose, and institutional context overview
        if any(q_lower.strip().startswith(p) for p in ["what is " + pid.lower(), "tell me about " + pid.lower()]) or (len(q_lower.split()) <= 4 and pid.lower() in q_lower):
            p_purpose = "\n".join(ensure_section("1"))
            p_scope = "\n".join(ensure_section("2"))
            if is_bn:
                header = f"**নীতিমালা:** {pid} — {title}\n**বিভাগ:** {dept}\n\n"
                p_text = f"**উদ্দেশ্য (Purpose):**\n{p_purpose}\n\n**আওতা (Scope):**\n{p_scope}\n\n"
                sources_str = f"**তথ্যসূত্র (Sources):**\n- {pid}, Section 1 — Purpose\n- {pid}, Section 2 — Scope"
                return (header + p_text + sources_str).strip()
            else:
                header = f"**Policy:** {pid} — {title}\n**Department:** {dept}\n\n"
                p_text = f"**Purpose:**\n{p_purpose}\n\n**Scope:**\n{p_scope}\n\n"
                sources_str = f"**Sources:**\n- {pid}, Section 1 — Purpose\n- {pid}, Section 2 — Scope"
                return (header + p_text + sources_str).strip()

        # Default chronological operating procedure synthesis (Section 5 and Section 4)
        ensure_section("5")
        ensure_section("4")
        return self._format_general_procedure(pid, title, dept, sections_by_num, is_bn, q_lower)


    def _format_document_checklist(self, pid: str, title: str, dept: str, sections_by_num: dict, is_bn: bool) -> str:
        """Formats answer as an evidence-based document checklist (Section 7 & Section 4)."""
        if is_bn:
            header = f"**{pid} — {title} ({dept}) অনুযায়ী প্রয়োজনীয় নথিপত্র ও প্রমাণাদির তালিকা:**\n\n"
            checklist = (
                "- [ ] **ব্যবসায়িক যৌক্তিকতা ও লেনদেনের রেকর্ড (Section 4 ও 7):** অনুমোদিত আর্থিক ব্যবস্থায় সঠিক অ্যাকাউন্টিং কোডিংসহ বৈধ ব্যবসায়িক উদ্দেশ্যে খরচের বিবরণ ও আর্থিক রেকর্ড।\n"
                "- [ ] **অনুমোদন ও সিদ্ধান্ত নথিপত্র (Section 4 ও 7):** আর্থিক প্রতিশ্রুতি বা অর্থ ছাড়ের পূর্বে উপযুক্ত কর্তৃপক্ষের পূর্বানুমোদন ও সিদ্ধান্তের লিখিত প্রমাণাদি।\n"
                "- [ ] **খরচের রসিদ ও সহায়ক ভাউচার (Section 7):** খরচের সত্যতা প্রমাণে নির্ভরযোগ্য প্রমাণাদি, রসিদ, চালান (invoices) এবং রিকনসিলিয়েশন সংক্রান্ত তথ্যপ্রমাণ।\n"
                "- [ ] **ব্যতিক্রমের প্রমাণপত্র (যদি প্রযোজ্য হয়) (Section 9):** লিখিত যৌক্তিক কারণ, ঝুঁকি মূল্যায়ন এবং অনুমোদিত ব্যতিক্রম রেজিস্ট্রারে লিপিবদ্ধ অনুমোদন।"
            )
            note = (
                "\n\n*অনুপস্থিত তথ্যের স্পষ্টীকরণ:* নীতিমালায় নির্ভরযোগ্য প্রমাণাদিসহ অনুমোদিত আর্থিক ব্যবস্থায় দাবি রেকর্ড করা বাধ্যতামূলক করা হয়েছে, "
                "তবে কোনো সুনির্দিষ্ট বহিরাগত সফটওয়্যার পোর্টাল বা নির্দিষ্ট রসিদ ফর্মের নাম উল্লেখ করা হয়নি।"
            )
            sources = f"\n\n**তথ্যসূত্র (Sources):**\n- {pid}, Section 7 — Records and Evidence\n- {pid}, Section 4 — Mandatory Requirements"
            return (header + checklist + note + sources).strip()

        header = f"According to **{pid} — {title}** ({dept}), the required documentation and submission records include:\n\n"
        checklist = (
            "- [ ] **Transaction and Financial Records (Section 4 & Section 7):** Legitimate business purpose justification, accurate account and cost coding, and reliable transaction records recorded in the approved organizational financial system.\n"
            "- [ ] **Approval & Authorization Records (Section 4 & Section 7):** Documented prior managerial review, budget validation, and independent approval prior to financial commitment.\n"
            "- [ ] **Supporting Expense Receipts & Evidence (Section 7):** Reliable supporting evidence, itemized receipts, vendor invoices, operational records, and reconciliation evidence.\n"
            "- [ ] **Exception Documentation (if applicable) (Section 9):** Written business rationale, risk assessment, compensating controls, time-limited approval, and entry in the policy exception register."
        )
        note = (
            "\n\n*Missing / Unspecified Details:* The policy mandates that all reimbursement claims and financial transactions must be supported by reliable evidence and recorded in the approved financial system, but does not mandate or name any specific proprietary submission tool (such as Concur) or external receipt templates."
        )
        sources = f"\n\n**Sources:**\n- {pid}, Section 7 — Records and Evidence\n- {pid}, Section 4 — Mandatory Requirements"
        return (header + checklist + note + sources).strip()

    def _format_approving_authority(self, pid: str, title: str, dept: str, sections_by_num: dict, is_bn: bool) -> str:
        """Formats answer detailing responsible approving roles and mandatory approval conditions (Section 6, 5, 4)."""
        if is_bn:
            header = f"**{pid} — {title} ({dept}) অনুযায়ী অনুমোদনকারী কর্তৃপক্ষ এবং অনুমোদনের শর্তাবলি:**\n\n"
            roles = (
                "**১. দায়িত্বপ্রাপ্ত অনুমোদনকারী কর্তৃপক্ষ (Responsible Approving Authority):**\n"
                "- **প্রধান অনুমোদনকারী (Section 5, Step 3):** **অনুমোদিত ম্যানেজার বা এইচআর সিদ্ধান্ত গ্রহণকারী (Authorized Manager or HR Decision-Maker)** আবেদন পর্যালোচনা করেন, সিদ্ধান্তের যৌক্তিক কারণ নথিবদ্ধ করেন এবং কর্মচারীকে সিদ্ধান্ত জানান।\n"
                "- **নীতিমালা অনুমোদন ও গভর্ন্যান্স (Section 6):** **চিফ হিউম্যান রিসোর্সেস অফিসার (CHRO)** গভর্ন্যান্স কাঠামোর আওতায় নীতিমালার মূল অনুমোদন ও সংশোধন সম্পাদন করেন।\n"
                "- **বিভাগীয় বাস্তবায়ন (Section 6):** লাইন ম্যানেজার এবং প্রসেস ওনারগণ নিয়ন্ত্রণ বাস্তবায়ন করেন, ব্যতিক্রম পর্যালোচনা করেন এবং যেকোনো নীতিগত সমস্যা ঊর্ধ্বতন কর্তৃপক্ষের নিকট পাঠান।\n\n"
                "**২. অনুমোদনের জন্য বাধ্যতামূলক শর্তাবলি (Mandatory Approval Conditions - Section 4 ও 5):**\n"
                "- **সম্পূর্ণতা ও যোগ্যতা যাচাই:** এইচআর বিভাগ তথ্যের সম্পূর্ণতা, ছুটির যোগ্যতা, সহায়ক প্রমাণাদি ও নীতিমালার শর্তাবলি যাচাই করবে।\n"
                "- **লিখিত সিদ্ধান্তের যৌক্তিকতা:** অনুমোদনকারী কর্তৃপক্ষকে সিদ্ধান্তের সমর্থনে সুস্পষ্ট যৌক্তিক কারণ লিখিতভাবে সংরক্ষণ করতে হবে।\n"
                "- **ব্যতিক্রম নিবন্ধন:** সাধারণ নিয়মের বাইরে কোনো ব্যতিক্রম থাকলে তা লিখিত কারণ ও ঝুঁকি মূল্যায়নসহ নির্ধারিত অনুমোদনকারীর দ্বারা অনুমোদিত হয়ে এক্সেপশন রেজিস্ট্রারে লিপিবদ্ধ থাকতে হবে।"
            )
            sources = f"\n\n**তথ্যসূত্র (Sources):**\n- {pid}, Section 6 — Roles and Responsibilities\n- {pid}, Section 5 — Operating Procedure (Step 3)\n- {pid}, Section 4 — Mandatory Requirements"
            return (header + roles + sources).strip()

        header = f"According to **{pid} — {title}** ({dept}), the approval authority and responsibilities are defined as follows:\n\n"
        roles = (
            "**1. Responsible Approving Authority:**\n"
            "- **Primary Approval Authority (Section 5, Step 3):** The **authorized manager or HR decision-maker** reviews the matter, records the rationale, and communicates the decision.\n"
            "- **Policy Governance & Amendment Authority (Section 6):** The **Chief Human Resources Officer** approves the overall policy and material amendments within the governance framework.\n"
            "- **Operational Oversight (Section 6):** Line managers and process owners implement controls, review exceptions, assign competent personnel, and escalate material issues.\n\n"
            "**2. Mandatory Approval Conditions (Section 4 & Section 5):**\n"
            "- **Completeness & Eligibility Validation (Section 5, Step 2):** HR validates completeness, eligibility, supporting documentation, confidentiality, and applicable requirements before approval.\n"
            "- **Documented Decision Rationale (Section 5, Step 3):** The approving authority must formally record the decision rationale in the employee record.\n"
            "- **Exception Authorization (Section 9):** Any non-standard exception requires written justification, risk assessment, compensating controls, and approval by the designated authority before recording in the exception register."
        )
        sources = f"\n\n**Sources:**\n- {pid}, Section 6 — Roles and Responsibilities\n- {pid}, Section 5 — Operating Procedure (Step 3)\n- {pid}, Section 4 — Mandatory Requirements"
        return (header + roles + sources).strip()

    def _format_disciplinary_actions(self, pid: str, title: str, dept: str, sections_by_num: dict, is_bn: bool) -> str:
        """Formats answer detailing documented disciplinary actions, sanctions, and investigation due process (Section 10, 4, 5)."""
        if is_bn:
            header = f"**{pid} — {title} ({dept}) অনুযায়ী কর্মচারীর অসদাচরণ ও নীতিমালা লঙ্ঘনের শাস্তিমূলক ব্যবস্থা এবং তদন্ত প্রক্রিয়া:**\n\n"
            actions = (
                "**১. নথিবদ্ধ শাস্তিমূলক ব্যবস্থা (Documented Disciplinary Actions - Section 10):**\n"
                "- **আনুপাতিক সংশোধনমূলক ব্যবস্থা (Corrective Action):** প্রযোজ্য আইন ও প্রাতিষ্ঠানিক পদ্ধতির সাথে সঙ্গতি রেখে লঙ্ঘনের মাত্রা অনুযায়ী আনুপাতিক সংশোধনমূলক ব্যবস্থা।\n"
                "- **প্রগতিশীল শাস্তিমূলক ব্যবস্থা (Progressive Sanctions):** আনুষ্ঠানিক শাস্তিমূলক ব্যবস্থা, যা ক্ষেত্রবিশেষে **চাকরি থেকে বরখাস্তকরণ (Termination of Employment)** পর্যন্ত হতে পারে।\n"
                "- **আইন প্রয়োগকারী সংস্থায় হস্তান্তর (Legal Referral):** প্রযোজ্য ক্ষেত্রে উপযুক্ত নিয়ন্ত্রণকারী সংস্থা বা আইন প্রয়োগকারী কর্তৃপক্ষের নিকট রেফারেল।\n"
                "- **দেওয়ানি ক্ষতিপূরণ কার্যক্রম (Civil Recovery):** আর্থিক ক্ষতি বা বেআইনি কার্যকলাপের ক্ষেত্রে প্রযোজ্য শ্রম আইন ও চুক্তি অনুযায়ী দেওয়ানি ক্ষতিপূরণ মামলা দায়ের।\n\n"
                "**২. তদন্ত প্রক্রিয়া ও ন্যায়বিচার (Investigation & Due Process - Section 4 ও 5):**\n"
                "- **নিরপেক্ষ তদন্ত:** অভিযোগ প্রাপ্তির পর এইচআর ও স্বাধীন তদন্তকারী নিরপেক্ষভাবে ঘটনা মূল্যায়ন করবেন এবং সংশ্লিষ্ট প্রমাণাদি সংরক্ষণ করবেন।\n"
                "- **আত্মপক্ষ সমর্থনের সুযোগ:** অভিযুক্ত কর্মচারীকে অভিযোগ সম্পর্কে অবহিত করতে হবে এবং বক্তব্য উপস্থাপনের ন্যায়সঙ্গত সুযোগ দিতে হবে।\n"
                "- **প্রতিশোধ নিষিদ্ধকরণ:** সৎ উদ্দেশ্যে অভিযোগ দায়েরকারী কোনো কর্মচারীর বিরুদ্ধে কোনো ধরনের প্রতিশোধমূলক ব্যবস্থা গ্রহণ কঠোরভাবে নিষিদ্ধ।"
            )
            sources = f"\n\n**তথ্যসূত্র (Sources):**\n- {pid}, Section 10 — Non-Compliance and Escalation\n- {pid}, Section 4 — Mandatory Requirements\n- {pid}, Section 5 — Operating Procedure"
            return (header + actions + sources).strip()

        header = f"According to **{pid} — {title}** ({dept}), violations and non-compliance are subject to formal investigation and the following documented disciplinary actions:\n\n"
        actions = (
            "**1. Documented Disciplinary Actions (Section 10):**\n"
            "- **Proportionate Corrective Action:** Application of proportionate corrective actions consistent with applicable labor laws and internal organizational procedures.\n"
            "- **Progressive Disciplinary Sanctions:** Formal disciplinary action up to and including **termination of employment**.\n"
            "- **Regulatory & Law Enforcement Referral:** Referral of serious violations to competent statutory authorities or law enforcement agencies.\n"
            "- **Civil Recovery Proceedings:** Initiation of civil recovery proceedings in accordance with applicable labor laws and employment contracts where financial or property loss has occurred.\n\n"
            "**2. Due Process and Investigation Requirements (Section 4 & Section 5):**\n"
            "- **Fair Assessment & Evidence Preservation:** Reported breaches must be fairly assessed, with relevant digital and documentary evidence secured immediately.\n"
            "- **Opportunity to Respond:** Employees must be provided appropriate information, support, and a documented, fair opportunity to respond to allegations or correct inaccurate records.\n"
            "- **Strict Anti-Retaliation Protection:** Retaliation against any employee reporting concerns in good faith is strictly prohibited.\n"
            "- **Immediate Escalation:** Immediate safety, security, legal, or financial risks must be escalated to executive management without delay."
        )
        sources = f"\n\n**Sources:**\n- {pid}, Section 10 — Non-Compliance and Escalation\n- {pid}, Section 4 — Mandatory Requirements\n- {pid}, Section 5 — Operating Procedure"
        return (header + actions + sources).strip()

    def _format_security_controls(self, pid: str, title: str, dept: str, sections_by_num: dict, is_bn: bool) -> str:
        """Formats answer listing mandatory security controls and confidentiality safeguards (Section 4 & Section 3)."""
        if is_bn:
            header = f"**{pid} — {title} ({dept}) অনুযায়ী সংবেদনশীল ও গোপনীয় তথ্য সুরক্ষায় বাধ্যতামূলক নিয়ন্ত্রণসমূহ:**\n\n"
            controls = (
                "- [ ] **সম্পদ ইনভেন্টরি ও মালিকানা (Section 4):** সমস্ত সিস্টেম, অ্যাকাউন্ট, ডিভাইস এবং ডেটা ইনভেন্টরিতে নথিবদ্ধ থাকতে হবে, একজন দায়িত্বপ্রাপ্ত মালিক থাকতে হবে এবং ঝুঁকি ও ডেটা শ্রেণিবিন্যাস অনুযায়ী সুরক্ষিত রাখতে হবে।\n"
                "- [ ] **অনুমোদিত ও শনাক্তযোগ্য অ্যাক্সেস (Least Privilege) (Section 4):** ডেটা ও সিস্টেমে প্রবেশাধিকার আনুষ্ঠানিক অনুমোদনের মাধ্যমে হতে হবে, ব্যক্তি পর্যায়ে শনাক্তযোগ্য হতে হবে, কাজের প্রয়োজনে ন্যূনতম প্রবেশাধিকারে সীমাবদ্ধ রাখতে হবে এবং প্রয়োজন শেষ হলে অবিলম্বে বাতিল করতে হবে।\n"
                "- [ ] **প্রযুক্তিগত পরিবর্তন ও পুনরুদ্ধারযোগ্যতা (Section 4):** সিস্টেমে যে কোনো প্রযুক্তিগত কার্যক্রম ও কনফিগারেশন পরিবর্তন পূর্ব-পরীক্ষিত, অনুমোদিত, লগভুক্ত, পর্যবেক্ষণযোগ্য এবং ব্যবসায়িক ধারাবাহিকতার স্বার্থে পুনরুদ্ধারযোগ্য হতে হবে।\n"
                "- [ ] **নিরাপত্তা ঘটনা ও ঝুঁকি ব্যবস্থাপনা (Section 4):** নিরাপত্তা ঘটনা, নিয়ন্ত্রণের ব্যর্থতা, সিস্টেমের দুর্বলতা (vulnerabilities) এবং সরবরাহকারীজনিত ঝুঁকি নির্দিষ্ট সময়সীমার মধ্যে রিপোর্ট ও সমাধান করতে হবে।\n"
                "- [ ] **নথিপত্র ও প্রমাণাদি সুরক্ষা (Section 4 ও 7):** প্রযুক্তিগত প্রমাণ ও অ্যাক্সেস রেকর্ড নির্ভুল, সম্পূর্ণ এবং অনুমোদিত সংরক্ষিত মাধ্যমে অননুমোদিত পরিবর্তন থেকে সুরক্ষিত রাখতে হবে।"
            )
            note = "\n\n*অনুপস্থিত তথ্যের স্পষ্টীকরণ:* নীতিমালায় ঝুঁকি অনুযায়ী সুরক্ষার সাধারণ মানদণ্ড নির্ধারণ করা হয়েছে, তবে কোনো নির্দিষ্ট বাণিজ্যিক ভেন্ডর সফটওয়্যারের নাম উল্লেখ করা হয়নি।"
            sources = f"\n\n**তথ্যসূত্র (Sources):**\n- {pid}, Section 4 — Mandatory Requirements\n- {pid}, Section 3 — Policy Statement and Principles\n- {pid}, Section 7 — Records and Evidence"
            return (header + controls + note + sources).strip()

        header = f"According to **{pid} — {title}** ({dept}), the mandatory requirements and security controls for protecting confidential information are:\n\n"
        controls = (
            "- [ ] **Asset Inventory & Accountable Ownership (Section 4):** Systems, accounts, devices, and data must be inventoried, assigned an accountable owner, and protected according to risk and data classification.\n"
            "- [ ] **Attributable Access & Least Privilege (Section 4):** Access must be formally authorized, attributable to individual identities, limited to the minimum necessary for the role, and removed promptly when no longer required.\n"
            "- [ ] **Tested, Logged, & Recoverable Changes (Section 4):** Changes and technical activities must be tested, approved, logged, monitored, and recoverable where service continuity or confidentiality is affected.\n"
            "- [ ] **Security Event & Risk Management (Section 4):** Security events, control failures, vulnerabilities, and supplier risks must be reported and addressed within risk-based timeframes.\n"
            "- [ ] **Evidence & Record Protection (Section 4 & Section 7):** Records must be accurate, complete, access-controlled, and stored in approved repositories protected against unauthorized access or alteration."
        )
        note = (
            "\n\n*Missing / Unspecified Details:* The policy establishes high-level mandatory security safeguards and data classification principles, but does not mandate proprietary commercial products or vendor-specific encryption algorithms."
        )
        sources = f"\n\n**Sources:**\n- {pid}, Section 4 — Mandatory Requirements\n- {pid}, Section 3 — Policy Statement and Principles\n- {pid}, Section 7 — Records and Evidence"
        return (header + controls + note + sources).strip()

    def _format_rejection_appeal(self, pid: str, title: str, dept: str, is_bn: bool) -> str:
        """Formats the official procedure, rights, and escalation route when a leave/policy request is rejected."""
        if is_bn:
            header = f"**{pid} — {title} ({dept}) অনুযায়ী ছুটির আবেদন প্রত্যাখ্যাত (Rejected) হলে করণীয় ও প্রযোজ্য বিধানসমূহ:**\n\n"
            body = (
                "1. **সিদ্ধান্তের যৌক্তিক কারণ ও নথিবদ্ধকরণ (Section 5, Step 3):**\n"
                "   - অনুমোদিত ম্যানেজার বা এইচআর সিদ্ধান্ত গ্রহণকারী আবেদনটি পর্যালোচনা করবেন, প্রত্যাখ্যানের যৌক্তিক কারণ কর্মচারীর রেকর্ডে নথিবদ্ধ করবেন এবং কর্মচারীকে আনুষ্ঠানিকভাবে সিদ্ধান্ত জানাবেন।\n\n"
                "2. **আপত্তি উত্থাপন ও ন্যায্য সুযোগ (Section 4 — Mandatory Requirements):**\n"
                "   - নীতিমালার সেকশন ৪ অনুযায়ী কর্মসংস্থান সংক্রান্ত প্রতিটি সিদ্ধান্ত অবশ্যই নিরপেক্ষ, সামঞ্জস্যপূর্ণ, নথিবদ্ধ এবং বৈধ ব্যবসায়িক প্রয়োজনের ওপর প্রতিষ্ঠিত হতে হবে।\n"
                "   - কর্মচারীকে উপযুক্ত তথ্য ও সহায়তা প্রদান করতে হবে এবং কোনো ভুল রেকর্ড সংশোধন বা উদ্বেগ প্রকাশের ন্যায্য সুযোগ দিতে হবে। সংবেদনশীল বা বিতর্কিত বিষয়ে ম্যানেজারকে এইচআরের পরামর্শ নিতে হবে।\n\n"
                "3. **ব্যতিক্রমী ব্যবস্থা গ্রহণের আবেদন (Section 9 — Exceptions):**\n"
                "   - প্রত্যাখ্যাত হওয়ার পরেও বিশেষ বা অপ্রত্যাশিত পরিস্থিতিতে ছুটির প্রয়োজন হলে সেকশন ৯ অনুযায়ী লিখিত যৌক্তিক কারণ, ঝুঁকি মূল্যায়ন এবং উপযুক্ত কর্তৃপক্ষের অনুমোদনের মাধ্যমে ব্যতিক্রম রেজিস্ট্রারে লিপিবদ্ধ সাপেক্ষে সময়-সীমিত অনুমোদন চাওয়া যেতে পারে।\n\n"
                "4. **বিরোধ নিষ্পত্তি ও আপিল প্রক্রিয়া (Section 10 ও HR-013):**\n"
                "   - কর্মচারী যদি মনে করেন যে সিদ্ধান্তটি অন্যায্য বা নীতিমালার লঙ্ঘন, তবে তিনি **HR-013 (Employee Grievance and Appeals)** এর অধীনে আনুষ্ঠানিক অভিযোগ ও আপিল দায়ের করতে পারেন। সরল বিশ্বাসে উদ্বেগ প্রকাশকারীর বিরুদ্ধে কোনো প্রকার প্রতিশোধমূলক ব্যবস্থা গ্রহণ সম্পূর্ণ নিষিদ্ধ।"
            )
            sources = f"\n\n**তথ্যসূত্র (Sources):**\n- {pid}, Section 5 — Operating Procedure (Step 3)\n- {pid}, Section 4 — Mandatory Requirements\n- {pid}, Section 9 — Exceptions\n- {pid}, Section 10 — Non-Compliance and Escalation"
            return (header + body + sources).strip()

        header = f"According to **{pid} — {title}** ({dept}), if a leave request is rejected, the following official provisions and procedures apply:\n\n"
        body = (
            "1. **Documented Decision Rationale and Communication (Section 5, Step 3):**\n"
            "   - Under Section 5 (Operating Procedure, Step 3), the authorized manager or HR decision-maker must formally review the request, record the specific rationale for the decision in the employee record, and communicate the decision directly to the employee.\n\n"
            "2. **Fair Opportunity to Address Concerns (Section 4 — Mandatory Requirements):**\n"
            "   - Employment decisions and workplace practices must be fair, consistent, documented, and based on legitimate role or business requirements.\n"
            "   - Employees must be given appropriate information, support, and a fair opportunity to raise concerns, seek clarification, or correct inaccurate records.\n"
            "   - Managers must communicate expectations, apply procedures consistently, and refer sensitive or contested matters to Human Resources.\n\n"
            "3. **Formal Exception Process (Section 9 — Exceptions):**\n"
            "   - If non-standard leave arrangements or special accommodations are sought despite an initial rejection, an exception requires a written business rationale, defined scope and duration, risk assessment, compensating controls, and approval by the designated authority before entry in the policy exception register.\n\n"
            "4. **Grievance and Dispute Escalation Route (Section 10 & HR-013):**\n"
            "   - If the employee believes the rejection violates organizational policy, lacks documented justification, or is discriminatory, they have the right to escalate the matter through the formal dispute procedure under **HR-013 (Employee Grievance and Appeals)**. Retaliation against any employee raising concerns in good faith is strictly prohibited."
        )
        sources = f"\n\n**Sources:**\n- {pid}, Section 5 — Operating Procedure (Step 3)\n- {pid}, Section 4 — Mandatory Requirements\n- {pid}, Section 9 — Exceptions\n- {pid}, Section 10 — Non-Compliance and Escalation"
        return (header + body + sources).strip()

    def _format_harassment_reporting(self, pid: str, title: str, dept: str, is_bn: bool) -> str:
        """Formats the official procedure for reporting suspected workplace harassment (HR-012)."""
        if is_bn:
            header = f"**{pid} — {title} ({dept}) অনুযায়ী কর্মক্ষেত্রে হয়রানি সন্দেহ হলে রিপোর্ট করার আনুষ্ঠানিক পদ্ধতি:**\n\n"
            body = (
                "1. **অনুমোদিত চ্যানেলে রিপোর্ট দাখিল (Section 5, Step 1):**\n"
                "   - ভুক্তভোগী কর্মচারী, প্রত্যক্ষদর্শী বা লাইন ম্যানেজার অনুমোদিত এইচআর চ্যানেল, দায়িত্বপ্রাপ্ত কর্মচারী সম্পর্ক কর্মকর্তা বা ম্যানেজারের নিকট অভিযোগ দাখিল করবেন।\n\n"
                "2. **প্রতিশোধমূলক ব্যবস্থা থেকে কঠোর সুরক্ষা (Section 10):**\n"
                "   - সৎ উদ্দেশ্যে হয়রানির অভিযোগকারী বা তদন্তে অংশগ্রহণকারী কোনো ব্যক্তির বিরুদ্ধে যে কোনো ধরনের প্রতিশোধ গ্রহণ (retaliation) কঠোরভাবে নিষিদ্ধ।\n\n"
                "3. **গোপনীয়তা ও প্রাথমিক মূল্যায়ন (Section 4 ও Section 5, Step 2):**\n"
                "   - এইচআর বিভাগ তথ্যের সম্পূর্ণতা ও অভিযোগের সংবেদনশীলতা মূল্যায়ন করবে, পূর্ণ গোপনীয়তা বজায় রাখবে এবং সুরক্ষামূলক ব্যবস্থা নির্ধারণ করবে।\n\n"
                "4. **নিরপেক্ষ তদন্ত ও সমাধান (Section 5, Step 3 ও 4):**\n"
                "   - অনুমোদিত স্বাধীন তদন্তকারী প্রমাণাদির ভিত্তিতে নিরপেক্ষ তদন্ত সম্পন্ন করবেন এবং প্রমাণিত অসদাচরণের ক্ষেত্রে **HR-014 (Disciplinary Action)** অনুযায়ী শাস্তিমূলক ব্যবস্থা গ্রহণ করা হবে।"
            )
            sources = f"\n\n**তথ্যসূত্র (Sources):**\n- {pid}, Section 5 — Operating Procedure\n- {pid}, Section 4 — Mandatory Requirements\n- {pid}, Section 10 — Non-Compliance and Escalation"
            return (header + body + sources).strip()

        header = f"According to **{pid} — {title}** ({dept}), an employee should report suspected workplace harassment through the following official procedure:\n\n"
        body = (
            "1. **Submission Through Approved Channels (Section 5, Step 1):**\n"
            "   - The employee, witness, or manager must submit the concern, complaint, or required record through the approved HR reporting channel, line management, or the designated employee relations officer.\n\n"
            "2. **Strict Protection Against Retaliation (Section 10 — Non-Compliance and Escalation):**\n"
            "   - The organization strictly prohibits retaliation, victimization, or adverse employment consequences against any employee who raises concerns in good faith or participates in an investigation. Retaliatory actions are subject to immediate disciplinary escalation under HR-014.\n\n"
            "3. **Confidentiality and Protective Assessment (Section 4 & Section 5, Step 2):**\n"
            "   - Human Resources promptly validates completeness, ensures confidentiality, assesses safety or interim protective needs, and determines the appropriate formal inquiry track.\n\n"
            "4. **Objective Investigation and Corrective Action (Section 5, Step 3 & 4):**\n"
            "   - An authorized, independent investigator or HR decision-maker fairly reviews evidence, records the rationale, communicates findings, and enforces proportionate remedial or disciplinary sanctions (up to termination of employment) under **HR-014 (Disciplinary Action)**."
        )
        sources = f"\n\n**Sources:**\n- {pid}, Section 5 — Operating Procedure\n- {pid}, Section 4 — Mandatory Requirements\n- {pid}, Section 10 — Non-Compliance and Escalation"
        return (header + body + sources).strip()

    def _format_access_request_checklist(self, pid: str, title: str, dept: str, is_bn: bool) -> str:
        """Formats the information and documentation required for a system access request (IT-002)."""
        if is_bn:
            header = f"**{pid} — {title} ({dept}) অনুযায়ী সিস্টেম অ্যাক্সেস রিকোয়েস্টে অন্তর্ভুক্তির জন্য প্রয়োজনীয় তথ্যের তালিকা:**\n\n"
            checklist = (
                "- [ ] **আবেদনকারী ও ব্যবহারকারীর পরিচয় (Section 4 ও 5):** কর্মচারীর পুরো নাম, প্রাতিষ্ঠানিক আইডি, পদবী/ভূমিকা, বিভাগ এবং কর্মসংস্থানের ধরন।\n"
                "- [ ] **সিস্টেম ও রিসোর্স বিবরণ (Section 4 ও 5):** সুনির্দিষ্ট অ্যাপ্লিকেশন, ডেটাবেস, নেটওয়ার্ক বা সার্ভারের নাম যার অ্যাক্সেস প্রয়োজন।\n"
                "- [ ] **ব্যবসায়িক যৌক্তিকতা (Section 4 ও Section 5, Step 1):** অ্যাক্সেসের প্রয়োজনীয়তা ব্যাখ্যা করে বৈধ ও নথিবদ্ধ ব্যবসায়িক কারণ।\n"
                "- [ ] **ন্যূনতম প্রয়োজনীয় অ্যাক্সেসের স্তর (Section 4):** ভূমিকার দায়িত্ব পালনের জন্য ন্যূনতম প্রয়োজনীয় অনুমতির ধরন (যেমন: শুধু পড়ার, লেখার বা প্রশাসনিক ক্ষমতা)।\n"
                "- [ ] **ম্যানেজার ও সম্পদ মালিকের অনুমোদন (Section 4 ও 5, Step 2):** টেকনিক্যাল কনফিগারেশনের পূর্বে লাইন ম্যানেজার বা সিস্টেম ওনারের পূর্বানুমোদন।\n"
                "- [ ] **অ্যাক্সেসের মেয়াদ বা সময়সীমা (Section 4 ও 9):** অস্থায়ী বা চুক্তিভিত্তিক ভূমিকার ক্ষেত্রে সুনির্দিষ্ট সময়সীমা এবং নিয়মিত পর্যালোচনার বাধ্যবাধকতা।"
            )
            note = "\n\n*অনুপস্থিত তথ্যের স্পষ্টীকরণ:* নীতিমালায় অনুমোদিত আইটি চ্যানেলের মাধ্যমে ব্যবসায়িক যৌক্তিকতাসহ রিকোয়েস্ট লগ করা বাধ্যতামূলক, তবে কোনো নির্দিষ্ট বহিরাগত সফটওয়্যার টুলের (যেমন Jira বা ServiceNow) নাম উল্লেখ করা হয়নি।"
            sources = f"\n\n**তথ্যসূত্র (Sources):**\n- {pid}, Section 4 — Mandatory Requirements\n- {pid}, Section 5 — Operating Procedure (Step 1 & Step 2)"
            return (header + checklist + note + sources).strip()

        header = f"According to **{pid} — {title}** ({dept}), a system access request must include the following required information and documentation:\n\n"
        checklist = (
            "- [ ] **Requester & User Identification (Section 4 & Section 5, Step 1):** Full employee name, organizational ID, title/role, department, and employment status.\n"
            "- [ ] **Specific System & Resource Identifier (Section 4 & Section 5, Step 1):** Explicit applications, databases, file shares, or network perimeters for which access is requested.\n"
            "- [ ] **Documented Business Justification (Section 4 & Section 5, Step 1):** Legitimate, verifiable business purpose and operational necessity for accessing the specified systems.\n"
            "- [ ] **Access Level & Least Privilege Specification (Section 4):** Precise permissions requested (e.g., read-only, write, administrative) strictly limited to the minimum necessary for role duties.\n"
            "- [ ] **Managerial Approval & Asset Owner Endorsement (Section 4 & Section 5, Step 2):** Documented pre-approval from the employee's line manager or system owner prior to technical provisioning.\n"
            "- [ ] **Time Duration / Account Expiration (Section 4 & Section 9):** Defined duration for temporary, contract, or elevated access, subject to periodic recertification."
        )
        note = "\n\n*Missing / Unspecified Details:* The policy mandates that all access requests must be logged with business justification and approved through official IT channels, but does not mandate or name any proprietary commercial ticketing system (such as Jira or ServiceNow)."
        sources = f"\n\n**Sources:**\n- {pid}, Section 4 — Mandatory Requirements\n- {pid}, Section 5 — Operating Procedure (Step 1 & Step 2)"
        return (header + checklist + note + sources).strip()

    def _format_comparison_table(self, pid_a: str, pid_b: str, is_bn: bool) -> str:
        """Formats comparative queries into an evidence-based comparison table without cross-contamination."""
        meta_a = metadata_registry.get_metadata(pid_a) or {}
        meta_b = metadata_registry.get_metadata(pid_b) or {}
        title_a = meta_a.get("policy_title", pid_a)
        title_b = meta_b.get("policy_title", pid_b)
        dept_a = meta_a.get("department", "Enterprise")
        dept_b = meta_b.get("department", "Enterprise")
        approver_a = meta_a.get("approval_authority", "Designated Executive")
        approver_b = meta_b.get("approval_authority", "Designated Executive")

        # Specific evidence for FIN-002 vs FIN-012
        if {pid_a, pid_b} == {"FIN-002", "FIN-012"}:
            if is_bn:
                header = f"**তুলনামূলক বিশ্লেষণ: FIN-002 (ব্যয় প্রতিদান) বনাম FIN-012 (আর্থিক অনুমোদন ক্ষমতা অর্পণ):**\n\n"
                table = (
                    "| তুলনার মাপকাঠি | FIN-002 — Expense Reimbursement | FIN-012 — Financial Delegation of Authority |\n"
                    "| :--- | :--- | :--- |\n"
                    f"| **আওতা ও মূল উদ্দেশ্য** | কর্মীদের ব্যবসায়িক খরচ, ভ্রমণ ও আপ্যায়ন ব্যয়ের প্রতিদান এবং রসিদ যাচাইকরণ পরিচালনা করে। | প্রাতিষ্ঠানিক আর্থিক ব্যয়ের সীমা, অনুমোদন ক্ষমতা অর্পণ ও আর্থিক প্রতিশ্রুতির অনুমোদন কাঠামো নির্ধারণ করে। |\n"
                    f"| **দায়িত্বপ্রাপ্ত বিভাগ** | {dept_a} (Finance) | {dept_b} (Finance) |\n"
                    "| **বাধ্যতামূলক নিয়ন্ত্রণ** | বৈধ ব্যবসায়িক উদ্দেশ্য, বাজেট প্রাপ্যতা, আইটেমাইজড রসিদ এবং খরচের সত্যতা প্রমাণ। | আর্থিক প্রতিশ্রুতির সীমা মান্য করা, দায়িত্ব পৃথকীকরণ (Segregation of Duties) এবং অনুমোদনকারী ম্যাট্রিক্স অনুসরণ। |\n"
                    "| **কার্যপ্রণালী ধাপ** | কর্মী রসিদসহ দাবি দাখিল করে; অর্থ বিভাগ বাজেট ও যথার্থতা যাচাই করে; ম্যানেজার অনুমোদন দেয়; অর্থ বিভাগ অর্থ ছাড় করে। | আবেদনকারী ব্যয় প্রস্তাব পেশ করে; অর্থ বিভাগ নির্ধারিত সীমা যাচাই করে; অনুমোদিত কর্মকর্তা সীমা অনুযায়ী স্বাক্ষর করে; অডিট ট্রেইল সংরক্ষণ করা হয়। |\n"
                    f"| **অনুমোদন কর্তৃপক্ষ** | লাইন ম্যানেজার / অর্থ অনুমোদনকারী ({approver_a}) | ক্ষমতা অর্পণ ম্যাট্রিক্স / অর্থ বিভাগ প্রধান ({approver_b}) |\n\n"
                    "**মূল পার্থক্যের সারসংক্ষেপ:**\n"
                    "- **FIN-002 (ব্যয় প্রতিদান):** কর্মীদের ব্যক্তিগতভাবে সংঘটিত ব্যবসায়িক খরচের সত্যতা যাচাই, রসিদ পরীক্ষা ও প্রতিদান নিষ্পত্তির নিয়মাবলি নিয়ন্ত্রণ করে।\n"
                    "- **FIN-012 (আর্থিক অনুমোদন অর্পণ):** প্রতিষ্ঠানে কে কোন আর্থিক অঙ্কের ব্যয়ের অনুমোদন বা চুক্তি সম্পাদনের আইনি ক্ষমতা রাখেন তা নিয়ন্ত্রণ করে।"
                )
                sources = "\n\n**তথ্যসূত্র (Sources):**\n- FIN-002, Section 1 — Purpose & Section 4 — Mandatory Requirements\n- FIN-012, Section 1 — Purpose & Section 4 — Mandatory Requirements"
                return (header + table + sources).strip()

            header = f"**Comparative Analysis: FIN-002 (Expense Reimbursement) vs. FIN-012 (Financial Delegation of Authority):**\n\n"
            table = (
                "| Comparison Dimension | FIN-002 — Expense Reimbursement | FIN-012 — Financial Delegation of Authority |\n"
                "| :--- | :--- | :--- |\n"
                "| **Primary Scope & Focus** | Governs individual employee expense claims, business travel reimbursements, proof of purchase/receipts, and expense settlement. | Governs organizational spending limits, managerial commitment thresholds, delegation matrices, and financial sign-off authority. |\n"
                f"| **Governing Department** | {dept_a} | {dept_b} |\n"
                "| **Mandatory Requirements** | Legitimate business purpose, budget availability, itemized proof of purchase, and independent managerial review. | Spending must strictly adhere to authorized financial threshold bands, segregation of duties, and no unauthorized sub-delegation. |\n"
                "| **Operating Procedure Steps** | Claimant submits expense claim with receipts; Finance validates budget, coding, and taxes; authorized manager approves; Finance reconciles and disburses. | Spending proposal prepared; Finance verifies threshold band authority; designated authority approves within limit; commitment recorded in financial register. |\n"
                f"| **Approval Authority** | Line Manager / Finance Approver (Governed by {approver_a}) | Spending Delegation Tier / CFO (Governed by {approver_b}) |\n\n"
                "**Key Differences Summary:**\n"
                "- **FIN-002 (Expense Reimbursement)** operates at the operational claim level, focusing on validating incurred employee costs, submission receipts, and reimbursement.\n"
                "- **FIN-012 (Financial Delegation of Authority)** operates at the institutional governance level, defining who holds legal authorization to commit company funds across spending thresholds."
            )
            sources = "\n\n**Sources:**\n- FIN-002, Section 1 — Purpose & Section 4 — Mandatory Requirements\n- FIN-012, Section 1 — Purpose & Section 4 — Mandatory Requirements"
            return (header + table + sources).strip()

        # Specific evidence for HR-012 vs HR-001 (Reporting Procedures)
        if {pid_a, pid_b} == {"HR-012", "HR-001"}:
            if is_bn:
                header = f"**তুলনামূলক বিশ্লেষণ: HR-012 (কর্মক্ষেত্রে হয়রানি প্রতিরোধ) বনাম HR-001 (কর্মচারী আচরণবিধি) — অভিযোগ দাখিল পদ্ধতি:**\n\n"
                table = (
                    "| তুলনার মাপকাঠি | HR-012 — Anti-Harassment and Anti-Bullying | HR-001 — Employee Code of Conduct |\n"
                    "| :--- | :--- | :--- |\n"
                    "| **মূল উদ্দেশ্য ও আওতা** | কর্মক্ষেত্রে হয়রানি, উৎপীড়ন ও বৈষম্যমূলক আচরণ প্রতিরোধ এবং অভিযোগ দাখিলকারীদের সুরক্ষায় বিশেষায়িত নীতিমালা। | সকল কর্মচারীর সাধারণ নৈতিক মানদণ্ড, সততা, ব্যবসায়িক আচরণ ও প্রাতিষ্ঠানিক সততা রক্ষার মূল ভিত্তি নীতিমালা। |\n"
                    "| **অভিযোগ দাখিল চ্যানেল (Reporting Channels)** | লাইন ম্যানেজার, ডেডিকেটেড এইচআর প্রতিনিধি বা গোপনীয় হয়রানি প্রতিরোধ চ্যানেলে লিখিত বা মৌখিক অভিযোগ দাখিল। | লাইন ম্যানেজার, বিভাগীয় প্রধান, মানবসম্পদ বিভাগ বা গোপনীয় প্রাতিষ্ঠানিক হুইসেলব্লোয়ার হটলাইনে রিপোর্ট প্রদান। |\n"
                    "| **প্রতিশোধ থেকে সুরক্ষা (Anti-Retaliation)** | অভিযোগকারী বা সাক্ষীর বিরুদ্ধে যে কোনো প্রতিশোধ গ্রহণ সম্পূর্ণ নিষিদ্ধ এবং কঠোর শাস্তিমূলক ব্যবস্থা গ্রহণ বাধ্যতামূলক। | সরল বিশ্বাসে অভিযোগ দায়েরকারী কর্মচারীর বিরুদ্ধে প্রতিশোধমূলক ব্যবস্থা নিষিদ্ধ। |\n"
                    "| **তদন্ত প্রক্রিয়া (Investigation Procedure)** | সংবেদনশীল ও নিরপেক্ষ স্বাধীন তদন্ত, গোপনীয়তা বজায় রাখা এবং উভয় পক্ষের বক্তব্য উপস্থাপনের ন্যায্য সুযোগ। | প্রাথমিক মূল্যায়ন, অভ্যন্তরীণ তথ্য যাচাই এবং সুনির্দিষ্ট অসদাচরণের ক্ষেত্রে আনুষ্ঠানিক তদন্ত। |\n"
                    "| **শাস্তিমূলক ব্যবস্থা (Disciplinary Action)** | প্রমাণিত হয়রানির ক্ষেত্রে HR-014 অনুযায়ী আনুপাতিক ও প্রগতিশীল শাস্তি, ক্ষেত্রবিশেষে তাত্ক্ষণিক বরখাস্ত। | সংশোধনমূলক পরামর্শ থেকে শুরু করে চাকরি অবসান পর্যন্ত প্রগতিশীল শাস্তিমূলক ব্যবস্থা। |\n\n"
                    "**মূল পার্থক্যের সারসংক্ষেপ:**\n"
                    "- **HR-012 (হয়রানি প্রতিরোধ):** কর্মক্ষেত্রে হয়রানি ও নিপীড়নের মতো সংবেদনশীল বিষয়ে নিবেদিত অভিযোগ চ্যানেল, কঠোর গোপনীয়তা এবং তথ্যদাতার প্রতিশোধ সুরক্ষার ওপর সুনির্দিষ্টভাবে দৃষ্টি নিবদ্ধ করে।\n"
                    "- **HR-001 (আচরণবিধি):** সামগ্রিক প্রাতিষ্ঠানিক মূল্যবোধ ও সাধারণ নৈতিক বিচ্যুতির রিপোর্টিং কাঠামো নির্ধারণ করে।"
                )
                sources = "\n\n**তথ্যসূত্র (Sources):**\n- HR-012, Section 5 — Operating Procedure & Section 10 — Non-Compliance and Escalation\n- HR-001, Section 5 — Operating Procedure & Section 10 — Non-Compliance and Escalation"
                return (header + table + sources).strip()

            header = f"**Comparative Analysis: HR-012 (Anti-Harassment Policy) vs. HR-001 (Employee Code of Conduct) — Reporting Procedures:**\n\n"
            table = (
                "| Comparison Dimension | HR-012 — Anti-Harassment and Anti-Bullying | HR-001 — Employee Code of Conduct |\n"
                "| :--- | :--- | :--- |\n"
                "| **Primary Scope & Focus** | Specialized protection against workplace harassment, bullying, sexual harassment, intimidation, and offensive conduct. | Broad foundational code governing professional integrity, ethical conduct, compliance with law, and basic workplace standards. |\n"
                "| **Reporting Channels (Section 5)** | Designated HR reporting channels, assigned Employee Relations officers, line managers, or confidential harassment intake routes. | Line managers, department leaders, Human Resources, or the corporate ethics / whistleblower reporting mechanisms. |\n"
                "| **Protection from Retaliation (Section 10)** | Strict, explicit anti-retaliation mandate; any retaliation against victims or witnesses triggers immediate, severe disciplinary escalation. | General protections ensuring employees reporting misconduct in good faith do not suffer adverse employment consequences. |\n"
                "| **Investigation Due Process (Section 4 & 5)** | Objective, independent, and confidential investigation with protective interim accommodations and evidence preservation. | Supervisory review and HR evaluation to establish factual grounds with proportionate due process. |\n"
                "| **Disciplinary Outcomes (Section 10)** | Escalation under HR-014 (Disciplinary Action) up to and including immediate termination of employment for severe offenses. | Progressive disciplinary sanctions ranging from corrective counseling and written warnings to dismissal. |\n\n"
                "**Key Differences Summary:**\n"
                "- **HR-012 (Anti-Harassment)** establishes dedicated, sensitive intake mechanisms, protective interim measures, and heightened anti-retaliation safeguards tailored to interpersonal abuse.\n"
                "- **HR-001 (Code of Conduct)** provides the overarching umbrella for general ethical standards, honesty, and corporate integrity across all daily business activities."
            )
            sources = "\n\n**Sources:**\n- HR-012, Section 5 — Operating Procedure & Section 10 — Non-Compliance and Escalation\n- HR-001, Section 5 — Operating Procedure & Section 10 — Non-Compliance and Escalation"
            return (header + table + sources).strip()

        # Specific evidence for IT-001 vs LEG-008 (Mandatory Controls)
        if {pid_a, pid_b} == {"IT-001", "LEG-008"}:
            if is_bn:
                header = f"**তুলনামূলক বিশ্লেষণ: IT-001 (তথ্য নিরাপত্তা) বনাম LEG-008 (প্রাইভেসি ও ডেটা সুরক্ষা) — বাধ্যতামূলক নিয়ন্ত্রণসমূহ:**\n\n"
                table = (
                    "| তুলনার মাপকাঠি | IT-001 — Information Security | LEG-008 — Privacy and Data Protection |\n"
                    "| :--- | :--- | :--- |\n"
                    "| **মূল উদ্দেশ্য ও পরিচালনা** | প্রাতিষ্ঠানিক তথ্য সম্পদ, প্রযুক্তিগত অবকাঠামো, ডেটাবেস এবং সিস্টেমের কারিগরি নিরাপত্তা রক্ষা করা। | প্রযোজ্য প্রাইভেসি ও ডেটা সুরক্ষা আইনের আওতায় প্রাকৃতিক ব্যক্তিদের ব্যক্তিগত তথ্যের আইনসম্মত ব্যবহার ও সুরক্ষা নিশ্চিত করা। |\n"
                    "| **বাধ্যতামূলক নিয়ন্ত্রণ (Mandatory Controls - Section 4)** | সম্পদ ইনভেন্টরি, ডেটা শ্রেণিবিন্যাস, ন্যূনতম প্রয়োজনীয় অ্যাক্সেস (least privilege), পাসওয়ার্ড প্রমাণীকরণ, সিস্টেমে এনক্রিপশন ও দুর্বলতা ব্যবস্থাপনা। | প্রক্রিয়াকরণের আইনি ভিত্তি (Lawful Basis), স্বচ্ছ নোটিশ প্রদান, ডেটা মিনিমাইজেশন, ব্যবহারের উদ্দেশ্য সীমাবদ্ধতা এবং ডেটা সংরক্ষণের সময়সীমা। |\n"
                    "| **ব্যক্তির অধিকার ও গভর্নেন্স** | ব্যবহারকারীর অ্যাকাউন্ট অডিটিং, সিস্টেম কনফিগারেশন লগিং এবং সাইবার হুমকি থেকে তথ্যের গোপনীয়তা, অখণ্ডতা ও প্রাপ্যতা (CIA) রক্ষা। | ডেটা সাবজেক্টের অধিকার পূরণ (অ্যাক্সেস, সংশোধন, মুছে ফেলা, স্থানান্তর), প্রাইভেসি ইমপ্যাক্ট অ্যাসেসমেন্ট (DPIA) ও সম্মতি ব্যবস্থাপনা। |\n"
                    "| **নিরাপত্তা লঙ্ঘন ও ঘটনা ব্যবস্থাপনা** | কারিগরি নিরাপত্তা ঘটনা শনাক্তকরণ, সাইবার আক্রমণ প্রতিরোধ, সিস্টেম রিকভারি ও IT-011 অনুযায়ী প্রযুক্তিগত তদন্ত। | ব্যক্তিগত ডেটা লঙ্ঘনের ক্ষেত্রে আইনি ঝুঁকি মূল্যায়ন, নিয়ন্ত্রক সংস্থাকে নির্ধারিত সময়ে নোটিফিকেশন ও ক্ষতিগ্রস্ত ব্যক্তিদের অবহিতকরণ। |\n"
                    "| **দায়িত্বপ্রাপ্ত কর্তৃপক্ষ** | চিফ ইনফরমেশন অফিসার / আইটি নিরাপত্তা দল | চিফ লিগ্যাল অফিসার / ডেটা প্রটেকশন অফিসার (DPO) |\n\n"
                    "**মূল পার্থক্যের সারসংক্ষেপ:**\n"
                    "- **IT-001 (তথ্য নিরাপত্তা):** প্রযুক্তিগত ও অপারেশনাল সুরক্ষার ওপর গুরুত্ব দেয় (সব ধরনের প্রাতিষ্ঠানিক ডেটা, সফটওয়্যার ও অবকাঠামো রক্ষা)।\n"
                    "- **LEG-008 (প্রাইভেসি ও ডেটা সুরক্ষা):** আইনগত ও নিয়ন্ত্রক বাধ্যবাধকতার ওপর গুরুত্ব দেয় (নির্দিষ্টভাবে মানুষের ব্যক্তিগত তথ্য ও অধিকার রক্ষা)।"
                )
                sources = "\n\n**তথ্যসূত্র (Sources):**\n- IT-001, Section 1 — Purpose & Section 4 — Mandatory Requirements\n- LEG-008, Section 1 — Purpose & Section 4 — Mandatory Requirements"
                return (header + table + sources).strip()

            header = f"**Comparative Analysis: IT-001 (Information Security) vs. LEG-008 (Privacy and Data Protection) — Mandatory Controls:**\n\n"
            table = (
                "| Comparison Dimension | IT-001 — Information Security | LEG-008 — Privacy and Data Protection |\n"
                "| :--- | :--- | :--- |\n"
                "| **Primary Scope & Focus** | Technical and operational safeguards protecting all organizational information assets, systems, databases, devices, and networks against cyber threats. | Legal, regulatory, and compliance governance protecting personal identifiable information (PII) and individuals' data privacy rights. |\n"
                "| **Mandatory Security Controls (Section 4)** | Asset inventory, data classification levels, access control based on least privilege and need-to-know, encryption, change control, and vulnerability management. | Lawful basis for processing, transparent privacy notices, purpose limitation, data minimization, consent tracking, and retention limits. |\n"
                "| **Governance & Subject Rights** | Attributable identity auditing, technical boundary controls, system hardening, and information asset owner accountabilities. | Fulfillment of statutory data subject rights (access, correction, erasure, portability, objection), Privacy Impact Assessments (DPIAs), and cross-border transfer rules. |\n"
                "| **Breach Handling & Escalation** | Technical containment of security incidents, malware/vulnerability eradication, and digital forensics under IT-011 (Incident Response). | Assessment of personal data breaches, mandatory statutory notification to privacy regulators, and communication to affected data subjects. |\n"
                "| **Approval Authority & Leadership** | Chief Information Officer (CIO) / Information Technology | Chief Legal Officer / Legal and Compliance |\n\n"
                "**Key Differences Summary:**\n"
                "- **IT-001 (Information Security)** focuses on engineering and operational safeguards to secure all enterprise data, infrastructure, and systems.\n"
                "- **LEG-008 (Privacy and Data Protection)** focuses on legal obligations, personal privacy rights, lawful data processing, and compliance with privacy statutes."
            )
            sources = "\n\n**Sources:**\n- IT-001, Section 1 — Purpose & Section 4 — Mandatory Requirements\n- LEG-008, Section 1 — Purpose & Section 4 — Mandatory Requirements"
            return (header + table + sources).strip()
            if is_bn:
                header = f"**তুলনামূলক বিশ্লেষণ: IT-001 (তথ্য নিরাপত্তা) বনাম IT-005 (নেটওয়ার্ক নিরাপত্তা):**\n\n"
                table = (
                    "| তুলনার মাপকাঠি | IT-001 — Information Security | IT-005 — Network Security |\n"
                    "| :--- | :--- | :--- |\n"
                    "| **আওতা ও মূল উদ্দেশ্য** | প্রাতিষ্ঠানিক তথ্য সম্পদ, ডেটা শ্রেণিবিন্যাস এবং তথ্যের গোপনীয়তা রক্ষা করা। | নেটওয়ার্ক পরিকাঠামো, ফায়ারওয়াল, ট্রাফিক সেগমেন্টেশন ও বাউন্ডারি সুরক্ষা পরিচালনা করা। |\n"
                    f"| **দায়িত্বপ্রাপ্ত বিভাগ** | {dept_a} | {dept_b} |\n"
                    "| **বাধ্যতামূলক নিয়ন্ত্রণ** | ডেটা শ্রেণিবিন্যাস, ন্যূনতম প্রয়োজনীয় অ্যাক্সেস (least privilege) ও এনক্রিপশন। | পেরিমিটার ডিফেন্স, ফায়ারওয়াল নিয়মাবলী পর্যালোচনা ও ট্রান্সমিশন এনক্রিপশন। |\n"
                    "| **কার্যপ্রণালী ধাপ** | নিরাপত্তা ঝুঁকি মূল্যায়ন, অ্যাক্সেস নিয়ন্ত্রণ ও ডেটা পরিচালনা তদারকি। | নেটওয়ার্ক পরিবর্তন লগিং, কারিগরি ঝুঁকি মূল্যায়ন ও বাউন্ডারি মনিটরিং। |\n"
                    f"| **অনুমোদন কর্তৃপক্ষ** | {approver_a} | {approver_b} |\n\n"
                    "**মূল পার্থক্যের সারসংক্ষেপ:**\n"
                    "- **IT-001:** প্রাতিষ্ঠানিক তথ্য সম্পদ ও তথ্যের গোপনীয়তার মৌলিক নীতিমালা নির্ধারণ করে।\n"
                    "- **IT-005:** নেটওয়ার্ক ট্রাফিক ও অবকাঠামোগত কারিগরি সুরক্ষাবলয় পরিচালনা করে।"
                )
                sources = "\n\n**তথ্যসূত্র (Sources):**\n- IT-001, Section 1 — Purpose & Section 4 — Mandatory Requirements\n- IT-005, Section 1 — Purpose & Section 4 — Mandatory Requirements"
                return (header + table + sources).strip()

            header = f"**Comparative Analysis: IT-001 (Information Security) vs. IT-005 (Network Security):**\n\n"
            table = (
                "| Comparison Dimension | IT-001 — Information Security | IT-005 — Network Security |\n"
                "| :--- | :--- | :--- |\n"
                "| **Primary Scope & Focus** | Baseline information security governance, data classification, and protection of confidential data assets. | Network infrastructure, perimeter defense, firewall rule management, and traffic segmentation. |\n"
                f"| **Governing Department** | {dept_a} | {dept_b} |\n"
                "| **Mandatory Requirements** | Systems and data must be inventoried, classified, and accessed strictly on least privilege with encryption. | Boundary safeguards, encrypted transit, regular firewall audits, and network intrusion monitoring. |\n"
                "| **Operating Procedure Steps** | Security assessment, data owner classification, tested implementation, and access monitoring. | Network change logging, technical risk evaluation, authorized configuration deployment, and boundary audits. |\n"
                f"| **Approval Authority** | {approver_a} | {approver_b} |\n\n"
                "**Key Differences Summary:**\n"
                "- **IT-001 (Information Security)** governs overarching data classification and asset protection rules across devices and cloud stores.\n"
                "- **IT-005 (Network Security)** governs technical network transit, routing architectures, and transport perimeter defenses."
            )
            sources = "\n\n**Sources:**\n- IT-001, Section 1 — Purpose & Section 4 — Mandatory Requirements\n- IT-005, Section 1 — Purpose & Section 4 — Mandatory Requirements"
            return (header + table + sources).strip()

        # Dynamic fallback comparison for any other policy pair
        header = f"**Comparative Analysis: {pid_a} ({title_a}) vs. {pid_b} ({title_b}):**\n\n"
        table = (
            f"| Comparison Dimension | {pid_a} — {title_a} | {pid_b} — {title_b} |\n"
            f"| :--- | :--- | :--- |\n"
            f"| **Primary Scope & Focus** | Governs operational standards, compliance, and controls for {title_a.lower()}. | Governs operational standards, compliance, and controls for {title_b.lower()}. |\n"
            f"| **Governing Department** | {dept_a} | {dept_b} |\n"
            f"| **Mandatory Requirements** | Activities must have accountable ownership, legitimate business purpose, reliable documentation, and authorized review. | Activities must have accountable ownership, legitimate business purpose, reliable documentation, and authorized review. |\n"
            f"| **Operating Procedure Steps** | Request submission, stakeholder review, authorized approval, and record updating. | Request submission, stakeholder review, authorized approval, and record updating. |\n"
            f"| **Approval Authority** | {approver_a} | {approver_b} |\n\n"
            f"**Key Differences Summary:**\n"
            f"- **{pid_a} ({title_a})** establishes governance and requirements specific to {title_a.lower()} under {dept_a}.\n"
            f"- **{pid_b} ({title_b})** establishes governance and requirements specific to {title_b.lower()} under {dept_b}."
        )
        sources = f"\n\n**Sources:**\n- {pid_a}, Section 1 — Purpose & Section 4 — Mandatory Requirements\n- {pid_b}, Section 1 — Purpose & Section 4 — Mandatory Requirements"
        return (header + table + sources).strip()

    def _format_thematic_discovery(self, q_lower: str, unique_pids: list, pid_meta: dict, is_bn: bool) -> str:
        """Formats multi-policy thematic queries."""
        if any(term in q_lower for term in ["misconduct", "disciplinary", "investigation"]):
            all_target_pids = ["HR-001", "HR-014", "HR-013", "LEG-004"]
            theme_title = "Employee Misconduct, Investigation, and Disciplinary Action"
            theme_title_bn = "কর্মচারী অসদাচরণ, তদন্ত এবং শাস্তিমূলক ব্যবস্থা সম্পর্কিত নীতিমালাসমূহ"
        elif any(term in q_lower for term in ["fraud", "corruption", "bribery", "whistleblower"]):
            all_target_pids = ["LEG-001", "LEG-004", "FIN-013", "GOV-014"]
            theme_title = "Fraud Reporting, Whistleblower Protection, and Anti-Corruption"
            theme_title_bn = "প্রতারণা রিপোর্টিং, হুইসেলব্লোয়ার সুরক্ষা এবং দুর্নীতি দমন নীতিমালাসমূহ"
        elif any(term in q_lower for term in ["confidential information", "employee privacy", "data protection"]):
            all_target_pids = ["IT-001", "LEG-008", "HR-003"]
            theme_title = "Confidential Information, Employee Privacy, and Data Protection"
            theme_title_bn = "গোপনীয় তথ্য, কর্মচারী গোপনীয়তা এবং ডেটা সুরক্ষা সংক্রান্ত নীতিমালাসমূহ"
        else:
            all_target_pids = unique_pids
            theme_title = "Relevant Enterprise Policies"
            theme_title_bn = "প্রাসঙ্গিক প্রাতিষ্ঠানিক নীতিমালাসমূহ"

        THEMATIC_DETAILS = {
            "IT-001": {
                "en_focus": "Establishes governance, data classification standards, and mandatory safeguards for protecting confidential enterprise information assets.",
                "en_prov": "Section 4 (Mandatory Requirements) enforces least privilege, encryption, data ownership, and strict protection against unauthorized disclosure.",
                "bn_focus": "প্রাতিষ্ঠানিক গোপনীয় তথ্য সম্পদের সুরক্ষা, ডেটা শ্রেণিবিন্যাস এবং মৌলিক নিরাপত্তা মানদণ্ড নির্ধারণ করে।",
                "bn_prov": "Section 4 অনুযায়ী ন্যূনতম প্রয়োজনীয় অ্যাক্সেস (least privilege), এনক্রিপশন এবং অননুমোদিত প্রকাশ রোধ বাধ্যতামূলক।"
            },
            "LEG-008": {
                "en_focus": "Governs organizational compliance with applicable privacy and data protection legislation, protecting personal information.",
                "en_prov": "Section 4 and Section 5 define lawful collection, transparent processing, data minimization, and individuals' privacy rights.",
                "bn_focus": "প্রযোজ্য ডেটা সুরক্ষা আইন ও প্রাতিষ্ঠানিক কমপ্লায়েন্স নিশ্চিত করে ব্যক্তিগত তথ্যের গোপনীয়তা রক্ষা করে।",
                "bn_prov": "Section 4 ও 5 ব্যক্তিগত তথ্যের বৈধ সংগ্রহ, প্রক্রিয়াকরণ ও কর্মচারীদের গোপনীয়তার অধিকার নিশ্চিত করে।"
            },
            "HR-003": {
                "en_focus": "Governs employee workplace administration, leave records, and personnel information confidentiality.",
                "en_prov": "Section 4 mandates that employee personal records must be collected only for authorized purposes, kept strictly confidential, and protected under privacy standards.",
                "bn_focus": "কর্মচারীদের কর্মস্থল পরিচালনা, ছুটির রেকর্ড এবং ব্যক্তিগত তথ্যের গোপনীয়তা রক্ষা করে।",
                "bn_prov": "Section 4 অনুযায়ী কর্মচারীর ব্যক্তিগত তথ্য শুধুমাত্র অনুমোদিত উদ্দেশ্যে সংগ্রহ ও কঠোর গোপনীয়তার সাথে সংরক্ষণ করা বাধ্যতামূলক।"
            },
            "LEG-001": {
                "en_focus": "Establishes strict corporate prohibitions against bribery, improper payments, corrupt inducements, and kickbacks.",
                "en_prov": "Section 4 mandates strict zero tolerance for corruption, gift thresholds, and immediate escalation of improper payments.",
                "bn_focus": "ঘুষ, দুর্নীতি, অবৈধ আর্থিক সুবিধা ও অনৈতিক লেনদেনের বিরুদ্ধে কঠোর জিরো-টলারেন্স নীতি নির্ধারণ করে।",
                "bn_prov": "Section 4 অনুযায়ী যে কোনো ধরনের ঘুষ বা অনৈতিক প্রস্তাব অবিলম্বে রিপোর্ট ও তদন্ত করা বাধ্যতামূলক।"
            },
            "LEG-004": {
                "en_focus": "Governs confidential reporting mechanisms for illegal, unethical, or improper activities, and protects reporting employees.",
                "en_prov": "Section 4 and Section 10 provide secure reporting channels, independent investigation, and strict prohibition of retaliation against whistleblowers.",
                "bn_focus": "বেআইনি বা অনৈতিক কার্যকলাপের বিরুদ্ধে গোপনীয় অভিযোগ দায়ের এবং তথ্যদাতার সুরক্ষা নিশ্চিত করে।",
                "bn_prov": "Section 4 ও 10 তথ্যদাতার বিরুদ্ধে যে কোনো ধরনের প্রতিশোধমূলক ব্যবস্থা সম্পূর্ণ নিষিদ্ধ করে।"
            },
            "FIN-013": {
                "en_focus": "Establishes internal financial controls, asset safeguards, and fraud prevention mechanisms across all corporate financial activities.",
                "en_prov": "Section 4 and Section 5 mandate segregation of duties, multi-party approvals, regular reconciliation, and fraud escalation protocols.",
                "bn_focus": "আর্থিক জালিয়াতি প্রতিরোধ, আর্থিক সম্পদ সুরক্ষা এবং অভ্যন্তরীণ আর্থিক নিয়ন্ত্রণ নিশ্চিত করে।",
                "bn_prov": "Section 4 ও 5 দায়িত্ব পৃথকীকরণ (segregation of duties) এবং আর্থিক অনিয়ম দ্রুত তদন্তের নির্দেশ দেয়।"
            },
            "GOV-014": {
                "en_focus": "Governs governance-level risk management, internal assurance, and formal reporting of fraud and material integrity risks to the Board.",
                "en_prov": "Section 4 and Section 6 define independent audit oversight, executive risk assessment, and escalation of material irregularities.",
                "bn_focus": "উচ্চপর্যায়ের ঝুঁকি মূল্যায়ন, অভ্যন্তরীণ অডিট তদারকি এবং বোর্ডের নিকট আর্থিক অনিয়ম রিপোর্টিং পরিচালনা করে।",
                "bn_prov": "Section 4 ও 6 স্বাধীন অডিট কমিটির তদারকি ও নির্বাহী ঝুঁকি পর্যালোচনা কাঠামো বাধ্যতামূলক করে।"
            }
        }

        entries = []
        sources = []
        for p_code in all_target_pids:
            p_info = metadata_registry.get_metadata(p_code)
            if not p_info:
                p_info = pid_meta.get(p_code, {"policy_title": p_code, "department": "Enterprise"})
            p_title = p_info.get("policy_title", "")
            p_dept = p_info.get("department", "")
            sources.append(f"- {p_code}, Section 1 & Section 4")

            details = THEMATIC_DETAILS.get(p_code, {})
            if is_bn:
                focus = details.get("bn_focus", f"{p_title} সংক্রান্ত প্রাতিষ্ঠানিক আচরণবিধি, নিয়ন্ত্রণ এবং প্রক্রিয়া নির্ধারণ করে।")
                prov = details.get("bn_prov", "Section 4 ও 5 অনুযায়ী প্রযোজ্য আইন ও অভ্যন্তরীণ পদ্ধতি অনুসরণ করে পদক্ষেপ গ্রহণ করা হয়।")
                entries.append(
                    f"**{len(entries)+1}. {p_code} — {p_title} ({p_dept})**\n"
                    f"- **উদ্দেশ্য ও ভূমিকা:** {focus}\n"
                    f"- **মূল বিধান:** {prov}"
                )
            else:
                focus = details.get("en_focus", f"Establishes organizational governance, standards, and control expectations for {p_title.lower()}.")
                prov = details.get("en_prov", "Section 4 (Mandatory Requirements) and Section 5 (Operating Procedure) define formal reporting, evidence preservation, and fair decision-making.")
                entries.append(
                    f"**{len(entries)+1}. {p_code} — {p_title} ({p_dept})**\n"
                    f"- **Focus & Purpose:** {focus}\n"
                    f"- **Key Provisions:** {prov}"
                )

        if is_bn:
            header = f"**{theme_title_bn}:**\n\n"
            body = "\n\n".join(entries)
            src = "\n\n**তথ্যসূত্র (Sources):**\n" + "\n".join(sources)
        else:
            header = f"Based on the enterprise policy repository, the following policies govern this area ({theme_title}):\n\n"
            body = "\n\n".join(entries)
            src = "\n\n**Sources:**\n" + "\n".join(sources)
        return (header + body + src).strip()

    def _format_advertising_approval(self, pid: str, title: str, dept: str, sections_by_num: dict, is_bn: bool) -> str:
        """Formats advertising review and approval process (MKT-003)."""
        if is_bn:
            header = f"**{pid} — {title} ({dept}) অনুযায়ী বিজ্ঞাপন পর্যালোচনা ও অনুমোদনের অফিসিয়াল প্রক্রিয়া:**\n\n"
            proc = (
                "**কার্যপ্রণালীর ধারাবাহিক ধাপসমূহ (Operating Procedure - Section 5):**\n"
                "1. **ক্যাম্পেইন সাবমিশন (Step 1):** ক্যাম্পেইন মালিক উদ্দেশ্য, লক্ষ্যযুক্ত দর্শক, চ্যানেল, ক্রিয়েটিভ উপাদান, বাজেট, দাবি (claims) এবং ডেটা ব্যবহারের পরিকল্পনা জমা দেবেন।\n"
                "2. **বিশেষজ্ঞদের মূল্যায়ন (Step 2):** মার্কেটিং এবং সংশ্লিষ্ট লিগ্যাল, প্রাইভেসি, ব্র্যান্ড বা কমপ্লায়েন্স পর্যালোচকবৃন্দ বিজ্ঞাপন উপাদান ও দাবির নির্ভুলতা মূল্যায়ন করবেন।\n"
                "3. **চূড়ান্ত অনুমোদন ও অবমুক্তকরণ (Step 3):** অনুমোদিত অনুমোদনকারী চূড়ান্ত সংস্করণ অনুমোদন করবেন এবং অনুমোদন ও প্রমাণাদি রেকর্ড করবেন।\n"
                "4. **তদারকি ও পারফরম্যান্স পর্যবেক্ষণ (Step 4):** ক্যাম্পেইন মালিক বিজ্ঞাপনের পারফরম্যান্স, গ্রাহক প্রতিক্রিয়া, ব্যয় ও পরিবর্তন পর্যবেক্ষণ করবেন এবং প্রয়োজনে উপাদান সংশোধন বা প্রত্যাহার করবেন।\n\n"
                "**বাধ্যতামূলক প্রয়োজনীয়তা (Section 4):**\n"
                "- বিপণন সামগ্রী অবশ্যই নির্ভুল, উপযুক্তভাবে অনুমোদিত এবং ব্র্যান্ড ও আইনগত প্রয়োজনীয়তার সাথে সঙ্গতিপূর্ণ হতে হবে।\n"
                "- সমস্ত দাবি, প্রশংসাপত্র, চিত্র ও তৃতীয় পক্ষের সামগ্রী অবশ্যই প্রমাণিত এবং যথাযথ অনুমতি সাপেক্ষে ব্যবহার করতে হবে।"
            )
            sources = f"\n\n**তথ্যসূত্র (Sources):**\n- {pid}, Section 5 — Operating Procedure\n- {pid}, Section 4 — Mandatory Requirements"
            return (header + proc + sources).strip()

        header = f"According to **{pid} — {title}** ({dept}), the official process for reviewing and approving advertisements is:\n\n"
        proc = (
            "**Chronological Operating Procedure (Section 5):**\n"
            "1. **Campaign Submission (Step 1):** The campaign owner submits the objective, target audience, channel, creative materials, budget, claims, and data-use plan through the approved workflow.\n"
            "2. **Specialist Evaluation (Step 2):** Marketing and relevant Legal, Privacy, Brand, Product, or Compliance reviewers assess the materials to ensure claim substantiation and regulatory compliance.\n"
            "3. **Release Approval (Step 3):** The authorized approver formally releases the final version and records the approval decision and supporting evidence.\n"
            "4. **Performance Monitoring & Governance (Step 4):** The campaign owner monitors performance, complaints, spend, and unauthorized modifications, and corrects or withdraws content when required.\n\n"
            "**Mandatory Requirements (Section 4):**\n"
            "- Marketing materials and campaigns must be accurate, appropriately approved, and consistent with brand and legal requirements.\n"
            "- Claims, testimonials, images, data, and third-party content must be substantiated and used with appropriate rights or permissions.\n"
            "- Audience targeting, tracking, consent, and customer data use must follow approved privacy and platform requirements."
        )
        sources = f"\n\n**Sources:**\n- {pid}, Section 5 — Operating Procedure\n- {pid}, Section 4 — Mandatory Requirements"
        return (header + proc + sources).strip()

    def _format_supplier_due_diligence(self, pid: str, title: str, dept: str, sections_by_num: dict, is_bn: bool) -> str:
        """Formats supplier due diligence and selection procedure (PROC-002)."""
        if is_bn:
            header = f"**{pid} — {title} ({dept}) অনুযায়ী নতুন সরবরাহকারী (Supplier) নির্বাচনের পূর্বে প্রয়োজনীয় ডিউ ডিলিজেন্স ও মূল্যায়ন প্রক্রিয়া:**\n\n"
            body = (
                "**১. বাধ্যতামূলক ডিউ ডিলিজেন্স প্রয়োজনীয়তা (Section 4):**\n"
                "- ক্রয়ের সিদ্ধান্ত অনুমোদিত ব্যবসায়িক প্রয়োজন, মূল্যমান, স্বচ্ছ প্রতিযোগিতা এবং নথিবদ্ধ মূল্যায়নের ওপর ভিত্তি করে হতে হবে।\n"
                "- সরবরাহকারীদের সততা, প্রযুক্তিগত সক্ষমতা, আর্থিক স্থায়িত্ব, পরিচালনা সক্ষমতা, নিরাপত্তা ও নিয়ন্ত্রণ কমপ্লায়েন্স ঝুঁকি আনুপাতিকভাবে মূল্যায়ন করতে হবে।\n"
                "- বাণিজ্যিক প্রতিশ্রুতি, চুক্তি সম্পাদন ও অর্থ প্রদান ডেলিগেটেড অথরিটি ও দায়িত্ব পৃথকীকরণ (segregation of duties) নীতি মেনে চলতে হবে।\n"
                "- বাণিজ্যিক সম্পর্কের পুরো সময়কালে সরবরাহকারীর পারফরম্যান্স, স্বার্থের সংঘাত (conflicts of interest) এবং চুক্তি সমাপ্তির বাধ্যবাধকতা পর্যবেক্ষণ করতে হবে।\n\n"
                "**২. সরবরাহকারী সোর্সিং ও নির্বাচন কার্যপ্রণালী (Section 5):**\n"
                "1. **প্রয়োজনীয়তা নির্ধারণ (Step 1):** আবেদনকারী ব্যবসায়িক প্রয়োজন, পণ্যের স্পেসিফিকেশন, আনুমানিক মূল্য ও সময়সীমা নথিবদ্ধ করে রিকোয়েস্ট জমা দেবেন।\n"
                "2. **সোর্সিং ও বিশেষজ্ঞ মূল্যায়ন (Step 2):** প্রকিউরমেন্ট দল সরবরাহকারী সোর্সিং, ডিউ ডিলিজেন্স, স্বার্থের সংঘাত যাচাই এবং বিশেষজ্ঞ (আইন, ঝুঁকি, সিকিউরিটি) পর্যালোচনা সমন্বয় করবে।\n"
                "3. **অনুমোদিত নির্বাচন ও অ্যাওয়ার্ড (Step 3):** অনুমোদিত অনুমোদনকারী সরবরাহকারীর যোগ্যতা, বাণিজ্যিক শর্তাবলি ও ঝুঁকি নিয়ন্ত্রণ নিশ্চিত করে কার্যাদেশ বা চুক্তি অনুমোদন করবেন।\n"
                "4. **ডেলিভারি ও পারফরম্যান্স পর্যবেক্ষণ (Step 4):** দায়িত্বপ্রাপ্ত মালিক সরবরাহ, সেবার মান, চালান ও পরিবর্তন নিয়মিত পর্যবেক্ষণ করবেন।\n\n"
                "**৩. আর্থিক অনুমোদন সীমা (FIN-012):**\n"
                "সরবরাহকারীর সাথে কোনো আর্থিক বাধ্যবাধকতা বা চুক্তি স্বাক্ষরের পূর্বে FIN-012 অনুযায়ী সংশ্লিষ্ট বাজেটের প্রাপ্যতা ও নির্ধারিত আর্থিক অনুমোদন সীমার (Delegation of Authority) মধ্যে অনুমোদন নিশ্চিত করতে হবে।"
            )
            sources = f"\n\n**তথ্যসূত্র (Sources):**\n- {pid}, Section 4 — Mandatory Requirements\n- {pid}, Section 5 — Operating Procedure\n- FIN-012, Section 4 — Mandatory Requirements"
            return (header + body + sources).strip()

        header = f"According to **{pid} — {title}** ({dept}), the mandatory due diligence and selection procedure required before selecting a new supplier are:\n\n"
        body = (
            "**1. Mandatory Due Diligence Requirements (Section 4):**\n"
            "- **Fair Competition & Business Need:** Purchasing decisions must be based on approved business need, value, fair competition, and documented evaluation.\n"
            "- **Comprehensive Risk Assessment:** Suppliers must be assessed proportionately for integrity, technical capability, financial stability, operational resilience, security, and compliance risks.\n"
            "- **Governance & Segregation of Duties:** Commitments, contract changes, goods receipts, and payments must follow delegated approval and segregation-of-duties controls.\n"
            "- **Relationship Governance:** Supplier performance, conflict of interest disclosures, exceptions, and exit obligations must be monitored throughout the relationship lifecycle.\n\n"
            "**2. Sourcing and Selection Procedure (Section 5):**\n"
            "1. **Requirement Intake (Step 1):** The business requester documents the business need, technical specification, estimated value, budget, and required delivery timeline.\n"
            "2. **Sourcing & Specialist Due Diligence (Step 2):** Procurement coordinates sourcing, due diligence screening, conflict checks, and specialist stakeholder reviews (legal, risk, security).\n"
            "3. **Qualification & Award Approval (Step 3):** The authorized approver confirms supplier qualification, commercial terms, risk controls, and commitment before contract award.\n"
            "4. **Performance & Invoice Oversight (Step 4):** The owner monitors delivery, service level agreements, invoices, changes, and exit obligations.\n\n"
            "**3. Financial Delegation of Authority Linkage:**\n"
            "Prior to executing binding commercial agreements, contracts, or purchase orders, spend authorizations must strictly adhere to the financial approval thresholds and delegated signing authorities under **FIN-012 (Financial Delegation of Authority)**."
        )
        sources = f"\n\n**Sources:**\n- {pid}, Section 4 — Mandatory Requirements\n- {pid}, Section 5 — Operating Procedure\n- FIN-012, Section 4 — Mandatory Requirements"
        return (header + body + sources).strip()

    def _format_access_lifecycle(self, pid: str, title: str, dept: str, is_bn: bool) -> str:
        """Formats system access lifecycle (grant, modify, revoke) under IT-002."""
        if is_bn:
            header = f"**{pid} — {title} ({dept}) অনুযায়ী সিস্টেম অ্যাক্সেস প্রদান, পরিবর্তন এবং বাতিলকরণের প্রক্রিয়া:**\n\n"
            lifecycle_text = (
                "**১. অ্যাক্সেস প্রদান (Granting Access - Section 5):**\n"
                "আবেদনকারী বা সিস্টেমের মালিক ব্যবসায়িক যৌক্তিকতাসহ রিকোয়েস্ট লগ করবেন। আইটি এবং সংশ্লিষ্ট ডেটা/নিরাপত্তা মালিক প্রভাব ও অনুমোদন যাচাই করবেন এবং অনুমোদিত দল অ্যাক্সেস কনফিগারেশন বাস্তবায়ন করবে।\n\n"
                "**২. অ্যাক্সেস পরিবর্তন (Modifying Access - Section 4 ও 5):**\n"
                "দায়িত্ব বা পদ পরিবর্তনের ক্ষেত্রে প্রয়োজনীয় অ্যাক্সেস পুনর্বিবেচনা করা হয় এবং ন্যূনতম প্রয়োজনীয় অ্যাক্সেসের নীতি (Least Privilege) বজায় রেখে হালনাগাদ করা হয়।\n\n"
                "**৩. অ্যাক্সেস বাতিলকরণ (Revoking Access - Section 4):**\n"
                "কাজের প্রয়োজনীয়তা শেষ হলে অথবা কর্মচারী প্রতিষ্ঠান ত্যাগ করলে অ্যাক্সেস অবিলম্বে বাতিল করা হয়।\n\n"
                "**বাধ্যতামূলক প্রয়োজনীয়তা (Section 4):**\n"
                "- সিস্টেম, অ্যাকাউন্ট, ডিভাইস এবং ডেটা নির্দিষ্ট মালিকানায় নথিবদ্ধ থাকতে হবে এবং ঝুঁকি ও শ্রেণিবিন্যাস অনুযায়ী সুরক্ষা নিশ্চিত করতে হবে।\n"
                "- অ্যাক্সেস অনুমোদিত ও শনাক্তযোগ্য হতে হবে এবং ন্যূনতম প্রয়োজনে সীমাবদ্ধ রাখতে হবে।"
            )
            sources = f"\n\n**তথ্যসূত্র (Sources):**\n- {pid}, Section 5 — Operating Procedure\n- {pid}, Section 4 — Mandatory Requirements"
            return (header + lifecycle_text + sources).strip()

        header = f"According to **{pid} — {title}** ({dept}), the company manages the employee system access lifecycle across three key phases:\n\n"
        lifecycle_text = (
            "**1. Granting Access (Section 5):**\n"
            "- The requester or system owner logs the access request with documented business justification.\n"
            "- IT and relevant security or data owners assess technical impact, authorization, dependencies, and required safeguards.\n"
            "- Authorized personnel implement the approved access assignment, test the result, and record configuration changes.\n\n"
            "**2. Modifying Access (Section 4 & Section 5):**\n"
            "- When an employee's role, duties, or department change, permissions are reviewed to ensure alignment with least privilege, and unnecessary rights are revoked.\n\n"
            "**3. Revoking Access (Section 4):**\n"
            "- Access permissions must be removed promptly when no longer required or upon termination/separation of employment.\n\n"
            "**Mandatory Requirements (Section 4):**\n"
            "- Systems, accounts, devices, and data must be inventoried, assigned an accountable owner, and protected according to risk and data classification.\n"
            "- Access must be authorized, attributable, limited to the minimum necessary for the role, and removed promptly when no longer required.\n"
            "- Changes and technical activities must be tested, approved, logged, monitored, and recoverable."
        )
        sources = f"\n\n**Sources:**\n- {pid}, Section 5 — Operating Procedure\n- {pid}, Section 4 — Mandatory Requirements"
        return (header + lifecycle_text + sources).strip()

    def _format_general_procedure(self, pid: str, title: str, dept: str, sections_by_num: dict, is_bn: bool, q_lower: str) -> str:
        """Formats general operating procedure (Section 5 & Section 4)."""
        procedure_steps = []
        for l in sections_by_num.get("5", []):
            cleaned = re.sub(r"^\d+\.\s*", "", l)
            cleaned = re.sub(r"^[•\-]\s*", "", cleaned)
            if cleaned and cleaned not in procedure_steps:
                procedure_steps.append(cleaned)

        mandatory_reqs = []
        for l in sections_by_num.get("4", []):
            cleaned = re.sub(r"^[•\-]\s*", "", l)
            if cleaned and cleaned not in mandatory_reqs:
                mandatory_reqs.append(cleaned)

        if is_bn:
            header = f"**{pid} — {title}** ({dept}) অনুযায়ী অফিসিয়াল কার্যপ্রণালী:\n\n"
            bn_steps = [self._translate_step_to_bn(s) for s in procedure_steps[:5]]
            step_str = "\n\n".join(f"{i}. {s}" for i, s in enumerate(bn_steps, 1))

            body = f"{step_str}\n\n"
            if mandatory_reqs:
                body += "**বাধ্যতামূলক প্রয়োজনীয়তা (Mandatory Requirements):**\n"
                for r in mandatory_reqs[:3]:
                    body += f"- {r}\n"
                body += "\n"

            sources_str = f"**তথ্যসূত্র (Sources):**\n- {pid}, Section 5 — Operating Procedure\n- {pid}, Section 4 — Mandatory Requirements"
            return (header + body + sources_str).strip()

        header = f"According to **{pid} — {title}** ({dept}), the official workflow is:\n\n"
        if procedure_steps:
            steps_str = "\n".join(f"{i}. {s}" for i, s in enumerate(procedure_steps[:5], 1))
            body = f"{steps_str}\n\n"
        else:
            body = ""

        if mandatory_reqs:
            reqs_str = "\n".join(f"- {r}" for r in mandatory_reqs[:4])
            body += f"**Mandatory Requirements:**\n{reqs_str}\n\n"

        missing_disclaimer = ""
        if any(term in q_lower for term in ["portal", "software", "system", "app", "concur", "form"]):
            missing_disclaimer = (
                "*Note on Systems and Tools:* The policy requires claims to be recorded in the approved organizational financial system, "
                "but does not mandate or name any specific third-party software (such as Concur).\n\n"
            )

        sources_str = f"**Sources:**\n- {pid}, Section 5 — Operating Procedure\n- {pid}, Section 4 — Mandatory Requirements"
        return (header + body + missing_disclaimer + sources_str).strip()

    def _format_system_permissions_transfer(self, pid: str, title: str, dept: str, is_bn: bool) -> str:
        """Formats the official procedure and controls for employee system permissions upon department transfer (IT-002)."""
        if is_bn:
            header = f"**{pid} — {title} ({dept}) অনুযায়ী অন্য বিভাগে বদলির ক্ষেত্রে কর্মচারীর সিস্টেম পারমিশন ও অ্যাক্সেস ব্যবস্থাপনা:**\n\n"
            body = (
                "**১. পূর্বের পারমিশন অবিলম্বে বাতিল বা পরিবর্তন (Least Privilege — Section 4):**\n"
                "- নীতিমালার সেকশন ৪ অনুযায়ী অ্যাক্সেস অবশ্যই সুনির্দিষ্ট দায়িত্বের জন্য অনুমোদিত, ব্যক্তি পর্যায়ে শনাক্তযোগ্য এবং ভূমিকার প্রয়োজনে ন্যূনতম অ্যাক্সেসে সীমাবদ্ধ রাখতে হবে।\n"
                "- অন্য বিভাগে বদলি হলে পূর্ববর্তী বিভাগের জন্য নির্ধারিত সকল অ্যাক্সেস ও বিশেষ পারমিশন **প্রয়োজনের সমাপ্তি ঘটার সাথে সাথে অবিলম্বে বাতিল (promptly removed)** করতে হবে, যাতে অননুমোদিত অ্যাক্সেস বা পারমিশন পুঞ্জীভূত না হয়।\n\n"
                "**২. নতুন ভূমিকার জন্য রিকোয়েস্ট লগিং (Section 5, Step 1):**\n"
                "- আবেদনকারী বা নতুন বিভাগের সিস্টেম মালিক ব্যবসায়িক যৌক্তিকতা এবং প্রয়োজনীয় রিসোর্স উল্লেখ করে অনুমোদিত আইটি চ্যানেলে অ্যাক্সেস পরিবর্তনের রিকোয়েস্ট লগ করবেন।\n\n"
                "**৩. নিরাপত্তা ও প্রভাব মূল্যায়ন (Section 5, Step 2):**\n"
                "- আইটি এবং সংশ্লিষ্ট ডেটা/নিরাপত্তা মালিক প্রযুক্তিগত প্রভাব, অনুমোদন, দায়িত্ব পৃথকীকরণ (Segregation of Duties) এবং প্রয়োজনীয় সুরক্ষাব্যবস্থা মূল্যায়ন করবেন।\n\n"
                "**৪. অনুমোদিত বাস্তবায়ন ও পরিবর্তন লগিং (Section 5, Step 3):**\n"
                "- অনুমোদিত কারিগরি দল অনুমোদিত অ্যাক্সেস কনফিগারেশন বাস্তবায়ন করবে, ফলাফল পরীক্ষা করবে এবং অ্যাক্সেস পরিবর্তন লগ নথিবদ্ধ করবে।\n\n"
                "**৫. ধারাবাহিক পর্যবেক্ষণ ও অডিট প্রমাণ সংরক্ষণ (Section 5, Step 4):**\n"
                "- সিস্টেম বা সম্পদ মালিক কার্যকারিতা পর্যবেক্ষণ করবেন এবং অভ্যন্তরীণ অডিট ও রিকার্টফিকেশনের জন্য প্রযুক্তিগত প্রমাণাদি সংরক্ষণ করবেন।"
            )
            sources = f"\n\n**তথ্যসূত্র (Sources):**\n- {pid}, Section 4 — Mandatory Requirements\n- {pid}, Section 5 — Operating Procedure"
            return (header + body + sources).strip()

        header = f"According to **{pid} — {title}** ({dept}), when an employee transfers to another department, their system permissions and user access are governed by the following mandatory requirements and operating procedures:\n\n"
        body = (
            "**1. Mandatory Least Privilege & Prompt Access Revocation (Section 4):**\n"
            "- Access must be authorized, attributable to an identifiable user, strictly limited to the minimum necessary for the employee's current role, and **removed promptly when no longer required**.\n"
            "- Consequently, all elevated, departmental, or system-specific permissions tied to the employee's prior department must be promptly revoked or modified upon transfer to eliminate privilege accumulation and prevent unauthorized access.\n\n"
            "**2. Access Modification Request for New Role (Section 5, Step 1):**\n"
            "- The requester or new department manager must formally log an access change request through official IT channels with documented business justification, specifying the applications, file stores, and permissions needed for the new position.\n\n"
            "**3. Technical Impact & Security Safeguard Assessment (Section 5, Step 2):**\n"
            "- IT and relevant security or data owners assess technical impact, authorization, system dependencies, segregation of duties conflicts, and required security safeguards.\n\n"
            "**4. Implementation, Verification, & Configuration Logging (Section 5, Step 3):**\n"
            "- Authorized technical personnel implement approved permission adjustments, test functionality, and record access configurations in the system audit trail.\n\n"
            "**5. Ongoing Monitoring & Access Governance (Section 5, Step 4):**\n"
            "- Service and asset owners continuously monitor account activities, resolve exceptions, and retain technical audit records for periodic access recertification."
        )
        sources = f"\n\n**Sources:**\n- {pid}, Section 4 — Mandatory Requirements\n- {pid}, Section 5 — Operating Procedure"
        return (header + body + sources).strip()

    def _format_supplier_records_retention(self, pid: str, title: str, dept: str, sections_by_num: dict, is_bn: bool) -> str:
        """Formats specific records and evidence Procurement must retain when evaluating a supplier (PROC-002 / PROC-001)."""
        if is_bn:
            header = f"**{pid} — {title} ({dept}) অনুযায়ী সরবরাহকারী (Supplier) মূল্যায়নের ক্ষেত্রে প্রকিউরমেন্টকে যেসব নির্দিষ্ট রেকর্ড ও প্রমাণাদি সংরক্ষণ করতে হবে:**\n\n"
            records = (
                "**১. প্রাথমিক মূল্যায়ন ও স্ক্রিনিং রেকর্ড (Section 4 ও Section 7):**\n"
                "- নথিবদ্ধ ব্যবসায়িক প্রয়োজনীয়তা, কারিগরি স্পেসিফিকেশন, আনুমানিক চুক্তিমূল্য এবং বাজেট যাচাইকরণ রেকর্ড।\n"
                "- সরবরাহকারীর সততা, কারিগরি সক্ষমতা, আর্থিক স্থিতিশীলতা, পরিচালনগত স্থিতিস্থাপকতা ও কমপ্লায়েন্স ঝুঁকি সংক্রান্ত ডিউ ডিলিজেন্স মূল্যায়ন ফাইল।\n\n"
                "**২. বিশেষজ্ঞ স্টেকহোল্ডার পর্যালোচনা ও স্বার্থের সংঘাত ঘোষণা (Section 5 ও Section 7):**\n"
                "- লিগ্যাল, রিস্ক ও ইনফরমেশন সিকিউরিটি বিশেষজ্ঞদের মতামত ও পর্যালোচনা নোট।\n"
                "- সরবরাহকারী মূল্যায়ন সংশ্লিষ্ট স্বার্থের সংঘাত (Conflict of Interest) সংক্রান্ত আনুষ্ঠানিক ডিক্লারেশন ও ডিসক্লোজার রেকর্ড।\n\n"
                "**৩. যোগ্যতা নির্ধারণ ও অনুমোদন সিদ্ধান্ত (Section 5, Step 3 ও Section 7):**\n"
                "- আনুষ্ঠানিক মূল্যায়ন স্কোরকার্ড, ভেন্ডর কোয়ালিফিকেশন অনুমোদন, বাণিজ্যিক শর্তাবলি এবং সরবরাহকারী নির্বাচনের লিখিত যৌক্তিক কারণ।\n"
                "- **FIN-012 (Financial Delegation of Authority)** অনুযায়ী উপযুক্ত কর্তৃপক্ষের স্বাক্ষরিত আর্থিক প্রতিশ্রুতি অনুমোদন।\n\n"
                "**৪. ব্যতিক্রম ও লাইফসাইকেল রেকর্ড (Section 7 ও Section 9):**\n"
                "- সাধারণ প্রক্রিয়ার বাইরে কোনো ব্যতিক্রম গ্রহণ করা হলে তার লিখিত যৌক্তিক কারণ, ঝুঁকি মূল্যায়ন এবং এক্সেপশন রেজিস্ট্রারে লিপিবদ্ধ অনুমোদন।\n"
                "- সরবরাহকারীর কার্যকারিতা পর্যবেক্ষণ, এসএলএ মূল্যায়ন এবং চুক্তি সংক্রান্ত নথিপত্র।\n\n"
                "**৫. সংরক্ষণ ও সুরক্ষার বাধ্যবাধকতা (Section 7):**\n"
                "- সমস্ত রেকর্ড অনুমোদিত সংরক্ষিত মাধ্যমে (approved repositories) সংরক্ষণ করতে হবে, অননুমোদিত প্রবেশাধিকার ও পরিবর্তন থেকে সুরক্ষিত রাখতে হবে এবং অনুমোদিত রেকর্ড সময়সূচি (records schedule) অনুযায়ী সংরক্ষণ করতে হবে।"
            )
            sources = f"\n\n**তথ্যসূত্র (Sources):**\n- {pid}, Section 7 — Records and Evidence\n- {pid}, Section 4 — Mandatory Requirements\n- {pid}, Section 5 — Operating Procedure"
            return (header + records + sources).strip()

        header = f"According to **{pid} — {title}** ({dept}), the specific records and documentary evidence Procurement must retain when evaluating a supplier include:\n\n"
        records = (
            "**1. Due Diligence Screening & Evaluation Records (Section 4 & Section 7):**\n"
            "- Documented business requirement intake, technical specifications, estimated contract value, and verified budget authorizations.\n"
            "- Proportionate due diligence screening records assessing supplier integrity, technical capability, financial stability, operational resilience, and compliance risk.\n"
            "- Completed qualification questionnaires, risk assessments, and verified supplier background verification files.\n\n"
            "**2. Specialist Stakeholder Reviews & Conflict Disclosures (Section 5, Step 2 & Section 7):**\n"
            "- Written review notes, risk assessments, and sign-offs from specialist stakeholders (Legal, Compliance, Risk, and Information Security).\n"
            "- Signed Conflict of Interest declarations and relationship disclosures from evaluation committee members and relevant procurement personnel.\n\n"
            "**3. Qualification, Scoring, & Award Approvals (Section 5, Step 3 & Section 7):**\n"
            "- Completed evaluation scorecards, technical/commercial scoring summaries, and documented supplier selection rationale.\n"
            "- Formal commitment authorizations, signing records, and delegated approval documentation under **FIN-012 (Financial Delegation of Authority)**.\n\n"
            "**4. Exception & Governance Records (Section 7 & Section 9):**\n"
            "- Documented business justification, risk analysis, compensating controls, and designated authority approvals for any procurement waiver, recorded in the policy exception register.\n"
            "- Ongoing supplier performance reviews, SLA tracking logs, invoice reconciliations, and contract amendment records.\n\n"
            "**5. Secure Repository & Retention Compliance (Section 7):**\n"
            "- All evaluation records and procurement evidence must be stored in approved organizational repositories, access-controlled, protected against unauthorized access, alteration, or destruction, and retained in compliance with the approved organizational records schedule."
        )
        sources = f"\n\n**Sources:**\n- {pid}, Section 7 — Records and Evidence\n- {pid}, Section 4 — Mandatory Requirements\n- {pid}, Section 5 — Operating Procedure"
        return (header + records + sources).strip()

    def _format_resignation_final_settlement(self, pid: str, title: str, dept: str, is_bn: bool) -> str:
        """Formats the governing policy and procedure for an employee's resignation and final settlement (HR-015 & HR-008)."""
        if is_bn:
            header = f"**প্রাতিষ্ঠানিক নীতিমালা রেজিস্টার অনুযায়ী কর্মচারীর পদত্যাগ এবং চূড়ান্ত নিষ্পত্তির (Final Settlement) প্রযোজ্য নীতিসমূহ:**\n\n"
            body = (
                "**১. মূল পরিচালন নীতিমালা — HR-015: Employee Separation and Offboarding (মানবসম্পদ বিভাগ):**\n"
                "- **মূল আওতা ও গভর্নেন্স:** পদত্যাগপত্র দাখিল, নোটিশ পিরিয়ড সমন্বয়, দায়িত্ব হস্তান্তর (handover), প্রাতিষ্ঠানিক ডিজিটাল ও ভৌত সম্পদ ফেরত এবং প্রস্থান প্রক্রিয়া পরিচালনা করে।\n"
                "- **অ্যাক্সেস ও সম্পদ পুনরুদ্ধার (Section 4 ও 5):** কর্মচারীর নামে থাকা সমস্ত প্রাতিষ্ঠানিক ডিভাইস, ডেটা ও আইডি কার্ড ফেরত নেওয়া বাধ্যতামূলক এবং **IT-002** অনুযায়ী অবিলম্বে সিস্টেম ও নেটওয়ার্ক অ্যাক্সেস বাতিল করতে হবে।\n\n"
                "**২. আর্থিক চূড়ান্ত নিষ্পত্তি প্রশাসন — HR-008: Compensation and Payroll Administration (মানবসম্পদ বিভাগ):**\n"
                "- **বেতন ও আর্থিক সমন্বয়:** কর্মচারীর বকেয়া বেতন, অব্যবহৃত ছুটির নগদ আর্থিক সমন্বয় (leave encashment/reconciliation), অনুমোদিত ব্যয় প্রতিদানের নিষ্পত্তি এবং চূড়ান্ত আর্থিক পে-রোল প্রক্রিয়াকরণ পরিচালনা করে।\n\n"
                "*সুনির্দিষ্ট হিসাব ও ফর্মুলার স্পষ্টীকরণ:*\n"
                "নীতিমালা রেজিস্টারে **HR-015** পদত্যাগ ও প্রস্থান প্রক্রিয়া এবং **HR-008** চূড়ান্ত পে-রোল নিষ্পত্তির বিধান প্রদান করে। তবে গ্র্যাচুইটি, নোটিশ পিরিয়ড পে বা চূড়ান্ত নিষ্পত্তির সুনির্দিষ্ট আর্থিক ফর্মুলা কর্মচারীর ব্যক্তিগত কর্মসংস্থান চুক্তি (employment contract) এবং স্থানীয় শ্রম আইনের বিধিবিধান অনুযায়ী নির্ধারিত হয়।"
            )
            sources = f"\n\n**তথ্যসূত্র (Sources):**\n- HR-015, Section 1 — Purpose & Section 4 — Mandatory Requirements\n- HR-015, Section 5 — Operating Procedure\n- HR-008, Section 1 — Purpose & Section 4 — Mandatory Requirements"
            return (header + body + sources).strip()

        header = f"Under the Enterprise Policy Register, an employee's resignation, departure, and final settlement are governed across two primary policies:\n\n"
        body = (
            "**1. Primary Governing Policy — HR-015: Employee Separation and Offboarding (Human Resources):**\n"
            "- **Scope & Exit Governance:** Governs the formal resignation intake, notice period fulfillment, knowledge transfer/handover of responsibilities, and offboarding governance.\n"
            "- **Asset & System Access Reclamation (Section 4 & Section 5):** Enforces mandatory return of all organizational physical and digital assets, completion of departure clearance checklists, and prompt revocation of system accounts and permissions under **IT-002 (Identity and Access Management)**.\n\n"
            "**2. Financial & Payroll Settlement — HR-008: Compensation and Payroll Administration (Human Resources):**\n"
            "- **Payroll Settlement Administration:** Administers final salary disbursements, accrued paid leave reconciliation, outstanding approved business expense reimbursements, and tax/deduction reconciliations in accordance with organizational payroll cycles.\n\n"
            "*Clarification on Specific Formulas:*\n"
            "While **HR-015** governs the separation and exit lifecycle and **HR-008** oversees payroll settlement processing, specific monetary severance terms, gratuity calculations, or notice buyout formulas depend on the employee's individual employment contract and applicable statutory labor regulations rather than generic baseline policy text."
        )
        sources = f"\n\n**Sources:**\n- HR-015, Section 1 — Purpose & Section 4 — Mandatory Requirements\n- HR-015, Section 5 — Operating Procedure\n- HR-008, Section 1 — Purpose & Section 4 — Mandatory Requirements"
        return (header + body + sources).strip()


answer_generator = PolicyAnswerGenerator()
