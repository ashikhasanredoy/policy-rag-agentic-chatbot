# Bring Your Own Device (BYOD), Hardware Asset, and Endpoint Security Policy

**Document ID:** POL-IT-004\
**Category:** IT\
**Policy Owner:** Global Information Technology & Infrastructure\
**Responsible Functions:** IT Operations, Information Security, HR,
Legal, Procurement, Asset Management\
**Proposed Version:** 1.6 (enhanced draft)\
**Source Version:** 1.5\
**Proposed Effective Date:** Upon formal approval\
**Review Cycle:** Semi-Annual and after material endpoint, threat, or
privacy changes\
**Status:** Draft --- proposed enhanced revision; approval required
before operational use\
**Applies To:** Employees, contractors, and third-party consultants who
access corporate resources using personal or company-owned endpoints\
**Systems Named in Source:** Microsoft Intune / Jamf Pro; Google
Workspace; GitHub; Slack; corporate VPN and SSO

> **Implementation notice:** Source requirements and named products are
> retained as examples. IT must confirm the actual MDM, EDR, hotline,
> email, supported OS versions, and hardware standards before
> publishing. MDM capabilities vary by platform and enrollment type;
> employee privacy statements must match the actual technical
> configuration and local law.

------------------------------------------------------------------------

## 1. Purpose, Scope, and Principles

1.1 This policy governs secure configuration, enrollment, monitoring,
access, maintenance, and disposal of personal and company-owned endpoint
devices that connect to corporate resources.

1.2 Covered devices include laptops, desktops, smartphones, tablets,
removable storage, and other endpoints used to access corporate email,
messaging, source code, staging systems, internal portals, databases,
VPN, or SSO.

1.3 The organization applies least privilege, device trust, data
minimization, secure configuration, timely patching, encryption, and
rapid incident reporting.

1.4 Access to corporate resources is conditional on meeting the required
security baseline. IT may restrict or block a non-compliant device.

## 2. Definitions

-   **BYOD:** An employee-owned device approved for limited business
    access.
-   **Corporate endpoint:** A device purchased, leased, or managed by
    the company.
-   **MDM:** Mobile Device Management platform used to enforce approved
    device settings and manage the corporate work environment.
-   **MAM:** Mobile Application Management used to protect selected work
    applications and data.
-   **Work Profile / container:** A separated corporate workspace on a
    personal device.
-   **EDR:** Endpoint Detection and Response security software.
-   **Rooted / jailbroken:** A device modified to bypass manufacturer
    security controls.
-   **Remote wipe:** A controlled action that removes corporate data or
    resets a company-owned device.
-   **Security incident:** A suspected compromise, loss, theft, malware
    event, unauthorized access, or data exposure.

## 3. Device Eligibility and MDM Enrollment

### 3.1 Mandatory Enrollment

Any personal smartphone or tablet used to access corporate email, Slack,
calendar, internal networks, or other protected resources must enroll in
the corporate MDM/MAM platform (source examples: **Microsoft Intune /
Jamf Pro**) and comply with the applicable enrollment profile.

### 3.2 Work Container and Privacy

Corporate management should use a separated work profile or managed
application container where technically supported. The source policy
states that the company does not monitor, access, or log personal
photos, text messages, browsing history, or personal apps. IT must
configure the platform accordingly and provide an accurate privacy
notice explaining: - Work data and corporate app activity that may be
managed. - Device compliance and security metadata collected. - Actions
IT may take, including removal of corporate data. - Any technical
limitations or exceptions.

The organization must not claim that personal information is
inaccessible if the selected enrollment method technically exposes it to
administrators.

### 3.3 Operating-System Requirements

-   **iOS / iPadOS:** Current major version or one prior major version,
    with security patches installed within **14 days of release**.
-   **Android:** Android **13 or newer**, with monthly security updates.
-   Unsupported, end-of-life, or materially vulnerable versions may be
    blocked earlier by IT.

### 3.4 Rooting and Jailbreaking

Rooted, jailbroken, bootloader-unlocked, or otherwise security-bypassed
devices are prohibited from MDM enrollment and corporate access. Network
admission controls should block detected non-compliant devices.

### 3.5 Enrollment and Revalidation

IT must verify ownership, OS version, encryption, screen lock, patch
status, and required management controls at enrollment and periodically
thereafter. Revalidation may also occur after a material OS or security
change.

## 4. Endpoint Security Baseline

### 4.1 Authentication and Screen Lock

All endpoints must require at least a **six (6) digit PIN or an
alphanumeric passphrase**, or supported biometric authentication such as
Face ID, Touch ID, or fingerprint. Biometrics must be backed by a secure
device credential.

### 4.2 Inactivity Timeout

Devices must automatically lock after no more than **five (5) minutes of
inactivity**. Users must manually lock the device whenever leaving it
unattended.

### 4.3 Encryption

Full-device or platform-supported hardware encryption must remain
enabled: - FileVault for supported macOS devices. - BitLocker for
supported Windows devices. - Native hardware-backed encryption for
supported mobile devices.

IT must verify encryption status and recovery-key protection. Recovery
keys must not be stored in personal notes or unapproved locations.

### 4.4 Endpoint Detection and Response

Company-managed laptops must have the approved EDR solution installed
and healthy. The source names **CrowdStrike Falcon / SentinelOne** as
examples; IT must designate the actual licensed product. Employees must
not disable, tamper with, uninstall, or bypass EDR, firewall, MDM, or
other required security agents.

### 4.5 Patching and Vulnerability Remediation

Users must install approved security updates promptly. The source OS
requirements above are minimum baselines; IT may set shorter remediation
windows for actively exploited vulnerabilities. Devices that remain
unpatched beyond the approved deadline may be quarantined or blocked.

### 4.6 Malware Protection

Only approved software may be installed on corporate endpoints. Users
must not disable anti-malware protection, execute suspicious
attachments, or bypass application controls.

## 5. Identity, Accounts, and Access

5.1 Corporate access must use individually assigned accounts and
approved SSO/MFA. Shared accounts are prohibited unless formally
approved and technically controlled.

5.2 Users must never share passwords, MFA prompts, recovery codes, or
device unlock credentials.

5.3 Access must be role-based and limited to the minimum resources
required. Privileged access requires additional approval and monitoring.

5.4 Users must sign out of corporate applications on shared or borrowed
devices. Access from public or unmanaged computers is prohibited unless
a specific secure exception is approved by IT Security.

5.5 Suspected credential compromise must be reported immediately. IT may
revoke tokens, reset credentials, invalidate sessions, and require
re-authentication.

## 6. Hardware Asset Lifecycle

### 6.1 Standard Laptop Specifications

The source policy lists these standard configurations:

**Engineering / Product** - 14-inch or 16-inch Apple MacBook Pro (M3/M4
Pro, 36 GB RAM, 1 TB SSD); or - Dell XPS Developer Edition
(Linux/Windows).

**General Corporate / Operations** - 13-inch MacBook Air; or - Lenovo
ThinkPad X1 Carbon (16 GB RAM, 512 GB SSD).

IT may approve equivalent or updated models based on current
procurement, security, accessibility, and support requirements. Model
specifications are procurement baselines, not a guarantee of a
particular brand.

### 6.2 Refresh Cycle

Corporate laptops are eligible for replacement and hardware refresh
every **three (3) years** of active service, subject to condition,
business need, budget, and security support.

### 6.3 Accessories

Employees may request standard IT accessories such as chargers, mice,
keyboards, and monitor cables through the internal IT service desk with
manager approval.

### 6.4 Asset Register

IT/Asset Management must record asset ID, serial number, assigned user,
issue date, warranty, condition, encryption status, repair history, and
return/disposal status.

### 6.5 Transfer and Disposal

Devices must be returned to IT before reassignment, resale, donation, or
disposal. IT must remove corporate data, revoke certificates, securely
erase storage, and retain sanitization evidence.

## 7. Lost, Stolen, or Compromised Device Procedure

### 7.1 Reporting Deadline

If a personal or corporate device containing company data or active SSO
credentials is lost, stolen, or suspected of compromise, the employee
must contact the **24/7 IT Security Incident Response Hotline
(+1-800-555-SECU)** or **security-alert@company.com** within **two (2)
hours of discovery**.

**Contact verification:** These contact details are retained from the
source file and appear to be operational placeholders. IT must verify
and replace them with working, monitored channels before the policy is
published or relied upon.

### 7.2 Information to Report

Provide, where known: - Employee name and callback method. - Device
type, asset tag, and operating system. - Approximate time and location
of loss. - Whether the device was unlocked or connected. - Corporate
applications, data, or credentials potentially exposed. - Any suspicious
activity observed.

Do not delay reporting because some details are unknown.

### 7.3 IT Response

Upon receiving a report, IT Security may: - Revoke SSO sessions, OAuth
tokens, certificates, and refresh tokens. - Disable or reset affected
credentials. - Lock or isolate the device. - Initiate remote removal of
corporate work-profile data. - Initiate a full wipe of company-owned
devices where appropriate. - Preserve logs and investigate possible data
exposure. - Notify Privacy, Legal, HR, and affected system owners.

### 7.4 Personal Data Protection

For BYOD devices, remote wipe should target corporate work-profile or
managed application data. The source policy states that personal data
outside the MDM container will not be affected. IT must verify this
behavior for the actual platform and enrollment type before promising
it.

### 7.5 Follow-Up

IT must document incident timeline, actions, data potentially affected,
user communications, recovery, and corrective measures.

## 8. Removable Media, Cloud Storage, and Data Transfer

8.1 Unencrypted USB drives, external hard drives, and personal memory
cards may not be connected to corporate laptops without IT Security
authorization.

8.2 Approved removable media must be encrypted, inventoried where
required, malware-scanned, and used only for an approved business
purpose.

8.3 Corporate code, customer datasets, and internal documentation must
not be synchronized to personal Dropbox, Google Drive, iCloud, OneDrive,
personal email, or other unapproved cloud storage.

8.4 Transfers must use approved corporate repositories, managed
file-sharing tools, or secure transfer mechanisms with access expiry and
audit logs where available.

8.5 Sensitive data must not be copied to a local device unless an
approved business process explicitly permits it and the device meets the
required security controls.

## 9. Software, Applications, and Generative AI

9.1 Employees may install only licensed and approved software on company
devices. Software must come from trusted sources and must not bypass
security controls.

9.2 Confidential code and internal customer documentation must not be
pasted into unapproved public generative-AI websites or consumer AI
services.

9.3 Only enterprise-contracted, zero-retention AI tools authorized by IT
may be used for confidential code or customer documentation, and only
within the approved configuration and use case.

9.4 Employees must not assume that a tool is approved merely because it
is available online or through a personal account. Check the current
approved-tool list.

9.5 AI outputs must be reviewed by a qualified employee before use in
production, customer communication, legal decisions, or
security-sensitive work.

## 10. BYOD Privacy, Consent, and Employee Choice

10.1 Before enrollment, employees must receive clear notice of
management capabilities, collected device information, work-data access,
remote actions, and support limitations.

10.2 Personal devices remain employee property. Corporate data and
managed applications remain subject to company security controls.

10.3 If an employee withdraws BYOD consent or leaves employment, IT may
remove corporate data and revoke access. The employee may be required to
use a company-issued device for continued access.

10.4 Where an employee declines BYOD enrollment, HR/IT must identify an
alternative access arrangement where required by law or employment
agreement.

10.5 Monitoring must be proportionate, transparent, and limited to
security and legitimate business purposes. Local privacy law controls.

## 11. Exceptions and Non-Compliance

11.1 Exceptions require written approval from IT Security and the
relevant business owner, a documented reason, compensating controls, an
expiry date, and risk acceptance by the designated authority.

11.2 No exception may authorize illegal processing, deliberate disabling
of required protection, or use of a known compromised device.

11.3 Violations---including tampering with EDR/MDM, unauthorized data
transfer, credential sharing, or concealment of device loss---may result
in access suspension and disciplinary action up to termination, subject
to investigation and applicable law.

## 12. Monitoring, Evidence, and Review

IT should maintain: - Device inventory and ownership records. - MDM
enrollment and compliance status. - OS and patch compliance reports. -
Encryption and EDR health status. - Access and administrative action
logs. - Lost-device incident records. - Asset return and secure disposal
evidence. - Exception and risk-acceptance records.

Suggested metrics include endpoint compliance rate, patch SLA
compliance, MDM coverage, EDR health, lost-device reporting time, and
unresolved exceptions.

Review this policy every six months and after material platform, threat,
or privacy changes.

## 13. Policy RAG and Interpretation Rules

-   Distinguish personal BYOD requirements from company-owned endpoint
    requirements.
-   State the two-hour reporting deadline and the exact contact details
    only with a warning that they must be verified.
-   Do not claim MDM cannot see any personal information unless the
    actual platform configuration confirms it.
-   Do not recommend copying corporate data to personal cloud storage or
    unapproved AI tools.
-   If device OS, MDM platform, or approved EDR is not specified, say
    **"IT must confirm the current supported configuration."**

**Related policies:** Information Security Policy; Customer Data Privacy
Policy; Remote Work Policy; Code of Business Conduct; Asset Management
Standard.
