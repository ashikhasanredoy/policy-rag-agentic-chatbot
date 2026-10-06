import os
import asyncio
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from backend.app.core.config import settings
from backend.app.core.logging import logger
from backend.app.core.security import get_password_hash
from backend.app.database.models import User
from backend.app.database.repository import UserRepository
from backend.app.services.ingestion_service import ingestion_service
from backend.app.database.connection import AsyncSessionLocal, init_db

POLICIES_MANIFEST = [
    {
        "file": "data/policies/hr/annual_leave_policy_v2.md",
        "name": "Comprehensive Annual Leave and Absence Management Policy",
        "category": "HR",
        "department": "Global People & Culture",
        "version": "2.0",
        "description": "20-day annual leave accrual (1.66 days/mo), 5-day carryover expiring March 31, parental leave (16 weeks maternity, 6 weeks paternity), sick leave, and bereavement."
    },
    {
        "file": "data/policies/hr/remote_work_policy_v2.1.md",
        "name": "Remote, Hybrid Workplace, and Telecommuting Policy",
        "category": "HR",
        "department": "Global People & Culture",
        "version": "2.1",
        "description": "Hybrid schedule up to 2 days/week, core hours (10 AM - 4 PM), $500 home office ergonomic stipend, $50/mo internet allowance, and international telecommuting limits."
    },
    {
        "file": "data/policies/hr/employee_benefits_and_compensation_v2.md",
        "name": "Employee Benefits, Compensation Structure, and Wellness Policy",
        "category": "HR",
        "department": "Global Total Rewards & Benefits",
        "version": "2.0",
        "description": "Medical/Dental/Vision plans, 401(k) 50% match up to 6% salary, $5,250 annual tuition assistance, 2x salary life insurance, STD/LTD, and $75/mo gym fitness subsidy."
    },
    {
        "file": "data/policies/finance/travel_expense_policy_v3.md",
        "name": "Business Travel, Expense Reimbursement, and Corporate Card Policy",
        "category": "Finance",
        "department": "Global Finance, Accounting & Procurement",
        "version": "3.0",
        "description": "Daily meal per diem ($75 max), hotel limits ($200 std / $280 Tier-1), flights under 5 hrs in economy, 30-day Concur submission deadline, and mileage ($0.67/mi)."
    },
    {
        "file": "data/policies/it/byod_and_security_policy_v1.5.md",
        "name": "Bring Your Own Device (BYOD) and IT Endpoint Security Policy",
        "category": "IT",
        "department": "Global Information Technology & Infrastructure",
        "version": "1.5",
        "description": "Mobile MDM enrollment, 6-digit PIN / biometric lock, 3-year laptop refresh cycles, 2-hour lost device reporting SLA, and remote wipe protocols."
    },
    {
        "file": "data/policies/security/information_security_policy_v2.md",
        "name": "Corporate Information Security and Access Control Policy",
        "category": "Security",
        "department": "Global Information Security & Compliance",
        "version": "2.0",
        "description": "SOC2/ISO27001 data classification (Tiers 1-4), 14-char password complexity, mandatory FIDO2 hardware MFA, AES-256 / TLS 1.3 encryption, and incident response matrix."
    },
    {
        "file": "data/policies/operations/code_of_conduct_v1.md",
        "name": "Code of Business Conduct, Corporate Ethics, and Whistleblower Policy",
        "category": "Operations",
        "department": "Legal, Compliance & Executive Ethics",
        "version": "1.0",
        "description": "FCPA anti-bribery standards, gift limits ($100 cap), outside activity disclosures, insider trading rules, and 24/7 confidential ethics reporting hotline."
    },
    {
        "file": "data/policies/customer/customer_data_privacy_v2.md",
        "name": "Customer Data Privacy and Global Compliance (GDPR/CCPA) Policy",
        "category": "Customer",
        "department": "Data Privacy, Legal & Security Office",
        "version": "2.0",
        "description": "GDPR/CCPA customer rights (Access, Erasure, Portability), 30-day DSAR response SLA, 7-year financial record retention, and Standard Contractual Clauses (SCCs)."
    }
]

async def seed_initial_data(db: AsyncSession):
    user_repo = UserRepository(db)

    # 1. Seed Default Admin and Employee Users
    admin_user = await user_repo.get_by_email("admin@company.com")
    if not admin_user:
        logger.info("Creating default Admin user (admin@company.com / admin123)")
        admin = User(
            email="admin@company.com",
            full_name="Sarah Connor (Compliance Admin)",
            hashed_password=get_password_hash("admin123"),
            role="ADMIN"
        )
        await user_repo.create(admin)

    employee_user = await user_repo.get_by_email("employee@company.com")
    if not employee_user:
        logger.info("Creating default Employee user (employee@company.com / user123)")
        emp = User(
            email="employee@company.com",
            full_name="Alex Rivera (Staff Engineer)",
            hashed_password=get_password_hash("user123"),
            role="EMPLOYEE"
        )
        await user_repo.create(emp)

    # 2. Ingest Sample Policies into DB, Qdrant, and BM25
    for item in POLICIES_MANIFEST:
        file_path = os.path.join(settings.BASE_DIR, item["file"])
        if os.path.exists(file_path):
            logger.info(f"Ingesting seed policy: {item['name']}")
            await ingestion_service.ingest_document(
                db=db,
                file_path=file_path,
                name=item["name"],
                category=item["category"],
                department=item["department"],
                version=item["version"],
                description=item["description"],
                status="active",
                effective_date="2026-01-01",
                created_by="System Seeder"
            )
        else:
            logger.warning(f"Seed file not found: {file_path}")

    logger.info("Database and vector store seeding completed successfully!")

if __name__ == "__main__":
    async def main():
        await init_db()
        async with AsyncSessionLocal() as session:
            await seed_initial_data(session)

    asyncio.run(main())
