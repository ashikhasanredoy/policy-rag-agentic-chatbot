import os
import csv
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

PROJECT_ROOT = Path(__file__).resolve().parent.parent
REGISTER_CSV = PROJECT_ROOT / "metadata" / "Policy_Register.csv"
POLICIES_DIR = PROJECT_ROOT / "policies"


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

    # 2. Build Ingestion Manifest from canonical Policy_Register.csv
    all_manifest = []
    if REGISTER_CSV.exists():
        with open(REGISTER_CSV, mode="r", encoding="utf-8-sig") as f:
            reader = csv.DictReader(f)
            for row in reader:
                pid = row.get("Policy ID", "").strip()
                if not pid:
                    continue
                dept_code = pid.split("-")[0]
                pdf_rel = row.get("PDF File", "").strip()
                fname = Path(pdf_rel).name.replace(".pdf", ".md") if pdf_rel else f"{pid}.md"
                md_path = POLICIES_DIR / dept_code / fname
                if md_path.exists():
                    dept = row.get("Department", "General")
                    eff_date = row.get("Effective Date", "2026-11-08").replace(" (placeholder)", "")
                    all_manifest.append({
                        "file": str(md_path),
                        "name": row.get("Policy Title", pid),
                        "category": dept,
                        "department": dept,
                        "version": row.get("Version", "1.0"),
                        "description": f"{pid} - {row.get('Policy Title', '')}: owned by {row.get('Policy Owner', 'Corporate')}.",
                        "status": "active",
                        "effective_date": eff_date,
                    })

    logger.info(f"Preparing ingestion for {len(all_manifest)} enterprise policy documents...")
    for idx, item in enumerate(all_manifest, start=1):
        file_path = item["file"]
        if os.path.exists(file_path):
            if idx <= 5 or idx % 30 == 0 or idx == len(all_manifest):
                logger.info(f"[{idx}/{len(all_manifest)}] Ingesting policy: {item['name']}")
            await ingestion_service.ingest_document(
                db=db,
                file_path=file_path,
                name=item["name"],
                category=item["category"],
                department=item["department"],
                version=item["version"],
                description=item.get("description", ""),
                status="active",
                effective_date=item.get("effective_date", "2026-01-01"),
                created_by="System Seeder"
            )

    logger.info(f"Database and metadata seeding completed successfully! Total indexed: {len(all_manifest)} policies.")

if __name__ == "__main__":
    async def main():
        await init_db()
        async with AsyncSessionLocal() as session:
            await seed_initial_data(session)

    asyncio.run(main())
