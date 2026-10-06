# Bring Your Own Device (BYOD), Hardware Asset, and Endpoint Security Policy

**Document ID:** POL-IT-004  
**Category:** IT  
**Department:** Global Information Technology & Infrastructure  
**Version:** 1.5  
**Effective Date:** 2026-01-01  
**Review Cycle:** Semi-Annual  
**Status:** Active  
**Applies To:** All Employees, Contractors, and Third-Party Consultants  

---

## Section 1: Objectives, Context, and Scope
1.1 **Purpose**: This policy governs the secure configuration, monitoring, access controls, and maintenance requirements when accessing corporate resources (email, messaging, source code, staging environments, and internal portals) from personal mobile devices (smartphones, tablets) or company-owned endpoint assets.  
1.2 **Scope**: Covers all endpoints connecting to corporate VPNs, Single Sign-On (SSO) identity portals, Google Workspace, GitHub, Slack, and internal database infrastructure.

---

## Section 2: Mobile Device Management (MDM) Enrollment
2.1 **Mandatory MDM Software**: Any personal smartphone or tablet utilized to access corporate email, Slack, calendar, or internal networks must enroll in the corporate Mobile Device Management (MDM) platform (e.g. Microsoft Intune / Jamf Pro).  
2.2 **Security Containerization**: Corporate MDM operates via a sandboxed "Work Profile" container. The company does **not** monitor, access, or log personal photos, text messages, browsing history, or personal apps.  
2.3 **Device OS Requirements**:
- **iOS / iPadOS**: Must be within the current major version or one prior version, with latest security patches installed within 14 days of release.
- **Android**: Must run Android 13 or newer with monthly security updates.  
2.4 **Prohibition on Rooting / Jailbreaking**: Devices that have been rooted, jailbroken, or bootloader-unlocked are strictly barred from MDM enrollment and will be blocked automatically by network admission controls.

---

## Section 3: Endpoint Security Baselines and Password Protocols
3.1 **Screen Lock and Encryption**:
- **Passcode Requirement**: All endpoints must require a minimum **six (6) digit PIN or alphanumeric passphrase**, or biometric authentication (Face ID, Touch ID, Fingerprint).
- **Inactivity Timeout**: Devices must automatically lock after a maximum of **five (5) minutes of inactivity**.
- **Storage Encryption**: Full device hardware encryption (FileVault for macOS, BitLocker for Windows, native hardware encryption for mobile) must remain permanently enabled.  
3.2 **Endpoint Detection and Response (EDR)**: Company-managed laptops are pre-installed with CrowdStrike Falcon / SentinelOne EDR. Tampering with, disabling, or modifying endpoint security agents is grounds for immediate disciplinary termination.

---

## Section 4: Hardware Lifecycle, Upgrades, and Refresh Cycles
4.1 **Standard Issue Laptop Specifications**:
- **Engineering / Product**: 16-inch or 14-inch Apple MacBook Pro (M3/M4 Pro, 36GB RAM, 1TB SSD) or Dell XPS Developer Edition (Linux/Windows).
- **General Corporate / Operations**: 13-inch MacBook Air or Lenovo ThinkPad X1 Carbon (16GB RAM, 512GB SSD).  
4.2 **Standard Refresh Cycle**: Corporate laptops are eligible for replacement and hardware refresh every **three (3) years** of active service.  
4.3 **Accessory and Peripheral Provisioning**: Employees may order standard IT accessories (chargers, mice, keyboards, monitor cables) directly through the internal IT ticketing service desk with manager approval.

---

## Section 5: Lost, Stolen, or Compromised Device Emergency Protocol
5.1 **Mandatory Reporting SLA**: If any personal or corporate device containing company data or active SSO credentials is lost, stolen, or suspected of being compromised, the employee must contact the **24/7 IT Security Incident Response Hotline (+1-800-555-SECU) or email security-alert@company.com within two (2) hours of discovery**.  
5.2 **Remote Enterprise Wipe**: Upon receiving a loss report, the IT Security team is authorized to initiate an immediate remote wipe of all corporate work profile data, revoke active OAuth tokens, and invalidate session cookies. Personal data outside the MDM container will not be affected on BYOD devices.

---

## Section 6: Prohibited Storage and Unauthorized Software
6.1 **External Storage Devices**: Unencrypted USB flash drives, external hard drives, and personal memory cards may not be connected to corporate laptops without IT Security authorization.  
6.2 **Shadow IT and Cloud Storage**: Employees must not sync corporate code, customer datasets, or internal documentation to personal cloud storage accounts (e.g. personal Dropbox, Google Drive, iCloud, or OneDrive).  
6.3 **AI Tools Policy**: Confidential code and internal customer documentation must not be pasted into unapproved public generative AI websites. Only enterprise-contracted, zero-retention AI tools authorized by IT are permitted.
