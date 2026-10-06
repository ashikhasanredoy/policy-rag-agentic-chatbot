# Corporate Information Security, Data Classification, and Access Control Policy

**Document ID:** POL-SEC-005  
**Category:** Security  
**Department:** Global Information Security & Compliance (InfoSec)  
**Version:** 2.0  
**Effective Date:** 2026-01-01  
**Review Cycle:** Annual  
**Status:** Active  
**Standards Alignment:** SOC 2 Type II, ISO/IEC 27001:2022, GDPR, HIPAA, NIST CSF  

---

## Section 1: Information Security Governance and Principles
1.1 **Mission**: To protect the confidentiality, integrity, and availability (CIA Triad) of customer data, proprietary IP, software assets, and enterprise systems from cyber threats and unauthorized disclosure.  
1.2 **Principle of Least Privilege (PoLP)**: Access to systems, databases, source repositories, and cloud infrastructure is granted strictly on a need-to-know, role-appropriate basis.  
1.3 **Zero Trust Architecture**: No user or device is implicitly trusted inside or outside the corporate perimeter. Every transaction and access request requires continuous verification.

---

## Section 2: Data Classification Tiers and Handling Mandates
2.1 **Tier 1 - Public**: Information approved for public distribution (marketing brochures, public website content, open job postings, public press releases). Requires standard brand review.  
2.2 **Tier 2 - Internal (Default)**: General internal business communications, employee directory, internal wikis, organizational charts, and team documentation. Must not be shared externally without business justification.  
2.3 **Tier 3 - Confidential**: Proprietary business data, non-public financial reports, roadmap designs, contracts, supplier pricing, and unreleased product roadmaps. Access restricted to specific project teams.  
2.4 **Tier 4 - Strictly Confidential / Restricted**:
- **Scope**: Customer Personally Identifiable Information (PII), Payment Card Data (PCI-DSS), Protected Health Information (PHI), corporate cryptographic private keys, database production credentials, and core proprietary algorithm source code.
- **Handling**: Mandatory encryption in transit (TLS 1.3) and at rest (AES-256). Stored only in SOC2/ISO27001-certified environments. Downloading to local drives is strictly prohibited.

---

## Section 3: Identity, Password Complexity, and Multi-Factor Authentication (MFA)
3.1 **Password Complexity Standards**:
- **Minimum Character Length**: Passwords must contain a minimum of **fourteen (14) characters**.
- **Character Diversity**: Must incorporate at least three (3) of the following four categories: uppercase letters (A-Z), lowercase letters (a-z), numeric digits (0-9), and special characters (!@#$%^&*).
- **Password History**: Systems prevent reuse of the previous ten (10) passwords.  
3.2 **Multi-Factor Authentication (MFA) Mandate**:
- Phishing-resistant MFA (FIDO2 WebAuthn hardware security keys such as YubiKeys, or biometric Passkeys) is **mandatory** for all corporate Single Sign-On (Okta / Google Identity) and VPN access.
- SMS-based OTP verification is depreciated and prohibited due to SIM-swapping vulnerabilities.  
3.3 **Password Managers**: Employees must utilize the corporate-licensed enterprise password manager (1Password) to generate and store random credentials. Storing credentials in plain text or browser auto-fill is prohibited.

---

## Section 4: Network Security, Remote Access, and Encryption
4.1 **Network Segmentation**: Production cloud environments (AWS, GCP) are strictly segmented from staging, development, and corporate office networks via Virtual Private Clouds (VPCs) and Zero Trust Network Access (ZTNA).  
4.2 **Cryptographic Baselines**:
- **In-Transit**: TLS 1.3 required; TLS 1.0, 1.1, and SSL are permanently disabled across all public endpoints.
- **At-Rest**: AES-256 encryption is mandatory across all databases, S3 storage buckets, and server volumes.  
4.3 **Clean Desk and Screen Policy**: Laptops must be locked whenever stepping away from the desk. Whiteboards containing system architectural diagrams or sensitive data must be erased after meetings.

---

## Section 5: Third-Party Vendor Risk Assessment
5.1 **Vendor Due Diligence**: Any SaaS vendor, cloud provider, or contractor processing company or customer data must complete an InfoSec Vendor Security Assessment and sign a Data Processing Agreement (DPA) prior to contract execution.  
5.2 **Minimum Security Certifications**: Key vendors must maintain SOC 2 Type II or ISO 27001 certification audited within the past twelve (12) months.

---

## Section 6: Security Incident Management and Escalation SLAs
6.1 **Incident Classification & Escalation Matrix**:
- **Severity 1 (Critical - Active Breach / PII Exfiltration)**: Escalation to CISO, CEO, and Legal within **fifteen (15) minutes**. Customer and regulatory notification within statutory deadlines (72 hours under GDPR).
- **Severity 2 (High - Targeted Malware / Unauthorized Credential Access)**: Escalation within **one (1) hour**; containment initiated within two (2) hours.
- **Severity 3 (Medium - Phishing attempt / Policy violation)**: Escalation within **four (4) hours**.  
6.2 **Incident Contact Channels**: Contact `security-ops@company.com` or post in the Slack channel `#sec-incident-urgent` 24/7/365.
