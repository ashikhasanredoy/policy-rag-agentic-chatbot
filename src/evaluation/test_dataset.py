"""
Comprehensive 50-Query Evaluation Dataset for Enterprise Policy RAG.
Covers all 10 departments, English, Bangla, Exact ID, Semantic, Cross-Department,
and Unanswerable/Out-of-Domain questions with verified ground truth.
"""

from typing import List, Dict, Any

EVALUATION_QUERIES: List[Dict[str, Any]] = [
    # --- Human Resources (HR) ---
    {
        "id": "Q01",
        "query": "What is the procedure for leave management under HR-003?",
        "expected_policies": ["HR-003"],
        "department": "Human Resources",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q02",
        "query": "How can an employee apply for annual leave?",
        "expected_policies": ["HR-003"],
        "department": "Human Resources",
        "category": "semantic",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q03",
        "query": "একজন কর্মচারী কীভাবে ছুটির আবেদন করতে পারে?",
        "expected_policies": ["HR-003"],
        "department": "Human Resources",
        "category": "bangla_semantic",
        "answerable": True,
        "language": "bn"
    },
    {
        "id": "Q04",
        "query": "What are the rules regarding employee attendance and punctuality?",
        "expected_policies": ["HR-002"],
        "department": "Human Resources",
        "category": "semantic",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q05",
        "query": "What constitutes a violation of HR-001 Employee Code of Conduct?",
        "expected_policies": ["HR-001"],
        "department": "Human Resources",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q06",
        "query": "কর্মচারী অসদাচরণ করলে কী ধরনের ব্যবস্থা নেওয়া যায়?",
        "expected_policies": ["HR-014", "HR-001"],
        "department": "Human Resources",
        "category": "bangla_semantic",
        "answerable": True,
        "language": "bn"
    },
    {
        "id": "Q07",
        "query": "What is the disciplinary action procedure for policy violations?",
        "expected_policies": ["HR-014"],
        "department": "Human Resources",
        "category": "semantic",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q08",
        "query": "What is the procedure for reporting workplace harassment and bullying?",
        "expected_policies": ["HR-012"],
        "department": "Human Resources",
        "category": "semantic",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q09",
        "query": "What are the guidelines for remote and hybrid work under HR-010?",
        "expected_policies": ["HR-010"],
        "department": "Human Resources",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q10",
        "query": "What steps are required during employee separation and offboarding?",
        "expected_policies": ["HR-015"],
        "department": "Human Resources",
        "category": "semantic",
        "answerable": True,
        "language": "en"
    },

    # --- Finance (FIN) ---
    {
        "id": "Q11",
        "query": "What is the expense reimbursement process under FIN-002?",
        "expected_policies": ["FIN-002"],
        "department": "Finance",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q12",
        "query": "কর্মচারী ভ্রমণের ব্যয় কীভাবে পরিশোধ করা হয়?",
        "expected_policies": ["FIN-002", "FIN-009"],
        "department": "Finance",
        "category": "bangla_semantic",
        "answerable": True,
        "language": "bn"
    },
    {
        "id": "Q13",
        "query": "What are the mandatory requirements for budget planning and control in FIN-001?",
        "expected_policies": ["FIN-001"],
        "department": "Finance",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q14",
        "query": "What controls govern corporate credit card use under FIN-010?",
        "expected_policies": ["FIN-010"],
        "department": "Finance",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q15",
        "query": "Who is responsible for petty cash management?",
        "expected_policies": ["FIN-003"],
        "department": "Finance",
        "category": "semantic",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q16",
        "query": "What is the invoice approval and accounts payable workflow?",
        "expected_policies": ["FIN-004"],
        "department": "Finance",
        "category": "semantic",
        "answerable": True,
        "language": "en"
    },

    # --- Information Technology (IT) ---
    {
        "id": "Q17",
        "query": "What are the password complexity requirements under IT-003?",
        "expected_policies": ["IT-003"],
        "department": "Information Technology",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q18",
        "query": "পাসওয়ার্ড এবং প্রমাণীকরণ নীতিমালার প্রধান নিয়ম কী?",
        "expected_policies": ["IT-003"],
        "department": "Information Technology",
        "category": "bangla_semantic",
        "answerable": True,
        "language": "bn"
    },
    {
        "id": "Q19",
        "query": "What are the employee responsibilities under the information security policy IT-001?",
        "expected_policies": ["IT-001"],
        "department": "Information Technology",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q20",
        "query": "What is the BYOD and mobile device management policy IT-004?",
        "expected_policies": ["IT-004"],
        "department": "Information Technology",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q21",
        "query": "How are security vulnerabilities and patches handled under IT-010?",
        "expected_policies": ["IT-010"],
        "department": "Information Technology",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q22",
        "query": "What is the IT incident response escalation procedure?",
        "expected_policies": ["IT-011"],
        "department": "Information Technology",
        "category": "semantic",
        "answerable": True,
        "language": "en"
    },

    # --- Legal & Compliance (LEG) ---
    {
        "id": "Q23",
        "query": "What is the anti-bribery and corruption policy under LEG-001?",
        "expected_policies": ["LEG-001"],
        "department": "Legal & Compliance",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q24",
        "query": "ঘুষ এবং দুর্নীতি প্রতিরোধে কোম্পানির নিয়ম কী?",
        "expected_policies": ["LEG-001"],
        "department": "Legal & Compliance",
        "category": "bangla_semantic",
        "answerable": True,
        "language": "bn"
    },
    {
        "id": "Q25",
        "query": "What protections are provided to whistleblowers under LEG-003?",
        "expected_policies": ["LEG-003"],
        "department": "Legal & Compliance",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q26",
        "query": "How are customer data privacy and GDPR compliance governed in LEG-005?",
        "expected_policies": ["LEG-005"],
        "department": "Legal & Compliance",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q27",
        "query": "What is the contract review and approval workflow under LEG-006?",
        "expected_policies": ["LEG-006"],
        "department": "Legal & Compliance",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },

    # --- Corporate Security (SEC) ---
    {
        "id": "Q28",
        "query": "What is the physical security policy for facility access under SEC-001?",
        "expected_policies": ["SEC-001"],
        "department": "Security",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q29",
        "query": "অফিসে দর্শক প্রবেশের নিয়মাবলী কী?",
        "expected_policies": ["SEC-003"],
        "department": "Security",
        "category": "bangla_semantic",
        "answerable": True,
        "language": "bn"
    },
    {
        "id": "Q30",
        "query": "What is the procedure for reporting security incidents in SEC-002?",
        "expected_policies": ["SEC-002"],
        "department": "Security",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q31",
        "query": "How are employee access badges and keycards managed under SEC-005?",
        "expected_policies": ["SEC-005"],
        "department": "Security",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },

    # --- Operations (OPS) ---
    {
        "id": "Q32",
        "query": "What is the business continuity and disaster recovery policy OPS-001?",
        "expected_policies": ["OPS-001"],
        "department": "Operations",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q33",
        "query": "ব্যবসায়িক ধারাবাহিকতা এবং দুর্যোগ পুনরুদ্ধারের নিয়ম কী?",
        "expected_policies": ["OPS-001"],
        "department": "Operations",
        "category": "bangla_semantic",
        "answerable": True,
        "language": "bn"
    },
    {
        "id": "Q34",
        "query": "What are the workplace health and safety requirements under OPS-008?",
        "expected_policies": ["OPS-008"],
        "department": "Operations",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q35",
        "query": "What are the environmental sustainability requirements under OPS-009?",
        "expected_policies": ["OPS-009"],
        "department": "Operations",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },

    # --- Procurement (PROC) ---
    {
        "id": "Q36",
        "query": "What are the vendor selection and supplier due diligence rules under PROC-003?",
        "expected_policies": ["PROC-003"],
        "department": "Procurement",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q37",
        "query": "সরবরাহকারী নির্বাচন এবং ক্রয়ের নিয়ম কী?",
        "expected_policies": ["PROC-001", "PROC-003"],
        "department": "Procurement",
        "category": "bangla_semantic",
        "answerable": True,
        "language": "bn"
    },
    {
        "id": "Q38",
        "query": "What is the purchase authorization threshold in procurement?",
        "expected_policies": ["PROC-004"],
        "department": "Procurement",
        "category": "semantic",
        "answerable": True,
        "language": "en"
    },

    # --- Sales (SALES) ---
    {
        "id": "Q39",
        "query": "What governs sales commission calculations under SALES-008?",
        "expected_policies": ["SALES-008"],
        "department": "Sales",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q40",
        "query": "What is the policy for customer discount approvals under SALES-002?",
        "expected_policies": ["SALES-002"],
        "department": "Sales",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },

    # --- Marketing (MKT) ---
    {
        "id": "Q41",
        "query": "What are the corporate branding and trademark guidelines under MKT-001?",
        "expected_policies": ["MKT-001"],
        "department": "Marketing",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q42",
        "query": "What approvals are required before publishing social media content under MKT-004?",
        "expected_policies": ["MKT-004"],
        "department": "Marketing",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },

    # --- Governance, Risk & Assurance (GOV) ---
    {
        "id": "Q43",
        "query": "What is the enterprise risk management policy GOV-002?",
        "expected_policies": ["GOV-002"],
        "department": "Governance, Risk & Assurance",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q44",
        "query": "What are the rules and principles for AI Use and Governance under GOV-009?",
        "expected_policies": ["GOV-009"],
        "department": "Governance, Risk & Assurance",
        "category": "exact_id",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q45",
        "query": "কৃত্রিম বুদ্ধিমত্তা (AI) ব্যবহারের নিয়মাবলী কী?",
        "expected_policies": ["GOV-009"],
        "department": "Governance, Risk & Assurance",
        "category": "bangla_semantic",
        "answerable": True,
        "language": "bn"
    },

    # --- Cross-Department Comparative Queries ---
    {
        "id": "Q46",
        "query": "Compare the employee grievance policy HR-013 with the whistleblower policy LEG-003.",
        "expected_policies": ["HR-013", "LEG-003"],
        "department": "Cross-Department",
        "category": "comparative",
        "answerable": True,
        "language": "en"
    },
    {
        "id": "Q47",
        "query": "How do information security IT-001 and physical access control SEC-001 coordinate?",
        "expected_policies": ["IT-001", "SEC-001"],
        "department": "Cross-Department",
        "category": "comparative",
        "answerable": True,
        "language": "en"
    },

    # --- Unanswerable / Out-of-Domain Queries (Safe Refusal Tests) ---
    {
        "id": "Q48",
        "query": "Can employees bring personal dogs or cats to work at headquarters?",
        "expected_policies": [],
        "department": "Out-of-Domain",
        "category": "unanswerable",
        "answerable": False,
        "language": "en"
    },
    {
        "id": "Q49",
        "query": "Does the company provide a monthly personal housing and mortgage allowance?",
        "expected_policies": [],
        "department": "Out-of-Domain",
        "category": "unanswerable",
        "answerable": False,
        "language": "en"
    },
    {
        "id": "Q50",
        "query": "কোম্পানি কি কর্মচারীদের ব্যক্তিগত ক্রিপ্টোকারেন্সি ট্রেডিংয়ে সহায়তা করে?",
        "expected_policies": [],
        "department": "Out-of-Domain",
        "category": "unanswerable",
        "language": "bn"
    }
]

