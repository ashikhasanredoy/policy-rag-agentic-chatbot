# Corporate Information Security, Data Classification, and Access Control Policy

**Document ID:** POL-SEC-005\
**Category:** Security\
**Policy Owner:** Global Information Security & Compliance (InfoSec)\
**Responsible Functions:** CISO/Head of Security, IT, Engineering,
Privacy, Legal, Procurement, HR, System Owners, Internal Audit\
**Proposed Version:** 2.1 (enhanced draft)\
**Source Version:** 2.0\
**Proposed Effective Date:** Upon formal approval\
**Review Cycle:** Annual and after material threat, system, or
regulatory changes\
**Status:** Draft --- proposed enhanced revision; approval required
before operational use\
**Applies To:** All employees, contractors, officers, agents, systems,
applications, infrastructure, and third parties accessing or processing
organizational information\
**Standards Context:** ISO/IEC 27001:2022, SOC 2 Trust Services
Criteria, NIST Cybersecurity Framework, GDPR, HIPAA where applicable,
and relevant contractual requirements

> **Standards notice:** The source policy identifies SOC 2 Type II,
> ISO/IEC 27001:2022, GDPR, HIPAA, and NIST CSF as alignment references.
> This does not mean the organization is certified, audited, compliant,
> or legally subject to every framework. HIPAA applies only where the
> organization is a covered entity, business associate, or otherwise
> legally obligated. SOC 2 is an attestation report framework, not a
> certification. Legal, Compliance, and Security must validate
> applicability and any external claims.

------------------------------------------------------------------------

## 1. Purpose, Scope, and Security Principles

1.1 This policy establishes minimum requirements to protect the
confidentiality, integrity, and availability (CIA) of customer data,
employee information, proprietary intellectual property, software,
devices, cloud infrastructure, and enterprise systems.

1.2 It applies to information in electronic, physical, verbal, cloud,
backup, development, test, and production environments.

1.3 Security must be designed into systems and business processes. Every
user, device, service, and connection must be authenticated, authorized,
monitored proportionately, and reviewed.

1.4 Core principles: - **Least privilege:** Access is limited to what a
role needs. - **Need to know:** Information is available only to
authorized people for a legitimate purpose. - **Zero Trust:** No user,
device, or network is trusted solely because of its location. -
**Defense in depth:** Multiple preventive, detective, and recovery
controls are used. - **Secure by design:** Security requirements are
considered before development or procurement. - **Resilience:** Systems
must be recoverable within approved business objectives. -
**Accountability:** Security actions and exceptions must be documented.

## 2. Definitions

-   **Information asset:** Data, system, application, device, service,
    or infrastructure that has business value.
-   **Asset owner:** Person accountable for classification, access, and
    lifecycle decisions.
-   **CIA Triad:** Confidentiality, Integrity, and Availability.
-   **MFA:** Multi-Factor Authentication using two or more independent
    factors.
-   **Phishing-resistant MFA:** Authentication designed to resist
    credential phishing, such as FIDO2/WebAuthn security keys or
    passkeys.
-   **Privileged account:** An account capable of administering systems,
    changing security controls, or accessing sensitive data at scale.
-   **Restricted data:** The highest-sensitivity information category
    under this policy.
-   **Security incident:** An event that actually or potentially
    compromises information or systems.
-   **Vulnerability:** A weakness that could be exploited to affect
    confidentiality, integrity, or availability.
-   **RTO / RPO:** Recovery Time Objective and Recovery Point Objective,
    approved business continuity targets.
-   **ZTNA:** Zero Trust Network Access.

## 3. Security Governance and Responsibilities

### 3.1 CISO / Head of Information Security

Owns the security program, risk framework, technical baselines, incident
command, security reporting, and policy exceptions.

### 3.2 System and Data Owners

Classify assets, approve access, define business criticality, set
retention, confirm recovery requirements, and remediate identified
risks.

### 3.3 IT and Engineering

Implement secure configurations, identity controls, network
segmentation, encryption, patching, monitoring, backups, secure
development, and recovery procedures.

### 3.4 Privacy and Legal

Advise on personal data, regulatory obligations, contracts, evidence
preservation, breach notification, and legal holds.

### 3.5 Procurement and Vendor Owners

Complete third-party risk assessment before purchase or data access and
monitor material vendor changes.

### 3.6 All Users

Protect credentials and devices, follow classification rules, complete
training, report incidents promptly, and use systems only for authorized
purposes.

## 4. Information Asset Inventory and Classification

### 4.1 Asset Inventory

Each system owner must maintain an inventory of critical systems, data
stores, cloud services, endpoints, applications, integrations, owners,
locations, dependencies, and recovery requirements.

### 4.2 Classification Tiers

  ------------------------------------------------------------------------
  Tier              Classification     Examples          Minimum handling
  ----------------- ------------------ ----------------- -----------------
  1                 **Public**         Approved          Approved for
                                       marketing         public
                                       brochures, public distribution;
                                       website content,  standard
                                       job postings,     brand/legal
                                       press releases    review

  2                 **Internal**       Internal          Do not share
                    (default)          communications,   externally
                                       employee          without business
                                       directory, wikis, justification and
                                       organizational    authorization
                                       charts, team      
                                       documentation     

  3                 **Confidential**   Non-public        Restrict to
                                       financial         approved teams;
                                       reports,          encrypt in
                                       roadmaps,         transit and at
                                       contracts,        rest; log
                                       supplier pricing, sensitive access
                                       proprietary       
                                       business data     

  4                 **Strictly         Customer PII,     Strict
                    Confidential /     payment-card      need-to-know;
                    Restricted**       data, PHI,        strong
                                       private           encryption;
                                       cryptographic     tightly
                                       keys, production  controlled
                                       credentials, core access; no local
                                       proprietary       download unless
                                       algorithms        explicitly
                                                         approved
  ------------------------------------------------------------------------

### 4.3 Classification Ownership

The creator or data owner must classify information at creation or
ingestion. If uncertain, use the higher reasonable classification until
the owner decides.

### 4.4 Reclassification

Information may be downgraded only by the asset owner with documented
justification. Public release requires authorized review.

## 5. Handling and Protection Requirements

### 5.1 Public

Public information may be distributed only after approval by the
responsible business owner and any required Brand, Legal, or
Communications review.

### 5.2 Internal

Internal information must remain in approved corporate systems. External
sharing requires business justification, recipient validation, and owner
approval.

### 5.3 Confidential

Confidential information must: - Be shared only with authorized
recipients. - Use approved encrypted channels. - Be stored in managed
repositories with access logging. - Be protected from public links and
uncontrolled downloads. - Be securely deleted when retention ends.

### 5.4 Restricted

Restricted information must: - Be encrypted in transit using **TLS 1.3**
and at rest using **AES-256**, or an approved equivalent where technical
compatibility requires a formally accepted exception. - Be stored only
in environments approved for the relevant data and risk. The source
policy specifies SOC 2 / ISO 27001-certified environments;
Security/Procurement must validate current reports and certification
scope rather than relying on a marketing claim. - Be accessible only to
named roles and approved service accounts. - Use MFA and enhanced
logging for access. - Not be downloaded to local drives under the source
baseline, unless the CISO and data owner approve a documented,
time-limited exception with encryption, endpoint controls, and deletion
evidence. - Never be sent through personal email, unapproved messaging,
public repositories, or unapproved AI tools.

### 5.5 Physical Information

Paper records, removable media, whiteboards, meeting-room displays, and
printed reports must receive protection consistent with their
classification. Sensitive documents must be locked away and destroyed
through approved secure disposal.

## 6. Identity and Access Management

### 6.1 Account Lifecycle

Access must be requested, approved, provisioned, modified, reviewed, and
removed through a controlled process. Every account must have an
accountable owner and a unique identity.

### 6.2 Least Privilege

Access is granted on a role-appropriate, need-to-know basis. Default
access is denied unless explicitly authorized.

### 6.3 Joiner, Mover, and Leaver Controls

-   **Joiner:** Access only after identity and employment/contract
    status are verified and manager/system-owner approval is recorded.
-   **Mover:** Access must be reviewed when role, department, or project
    changes; obsolete access must be removed.
-   **Leaver:** Access must be disabled promptly at the approved
    separation time; credentials, tokens, keys, devices, and badges must
    be recovered or revoked.

### 6.4 Access Reviews

System owners must review privileged and Restricted-data access at least
quarterly and other material access at least semi-annually, or more
frequently where risk or law requires. Review evidence and remediation
must be retained.

### 6.5 Privileged Access

Administrative accounts must be separate from standard user accounts
where practical, protected by phishing-resistant MFA, time-limited where
possible, monitored, and used only for approved administrative work.
Shared privileged credentials are prohibited unless technically
unavoidable and controlled through a privileged-access management
process.

## 7. Passwords, MFA, and Authentication

### 7.1 Password Baseline

The source policy requires: - Minimum password length of **fourteen (14)
characters**. - At least **three (3) of four (4)** character categories:
uppercase, lowercase, numbers, and special characters. - Prevention of
reuse of the previous **ten (10) passwords**.

Systems should also block known compromised and commonly used passwords,
protect against online guessing, and support long passphrases. Passwords
must never be stored in plaintext or shared.

### 7.2 Password Changes

Passwords must be changed immediately when compromise is suspected,
credentials are exposed, or an administrator/security control requires
it. Routine forced rotation should be governed by the approved identity
standard and applicable system capability; it must not be used as a
substitute for MFA, monitoring, and compromised-password detection.

### 7.3 Mandatory MFA

Phishing-resistant MFA using FIDO2/WebAuthn hardware security keys (such
as YubiKeys) or biometric passkeys is mandatory for corporate SSO
(source examples: Okta / Google Identity) and VPN access.

### 7.4 SMS OTP

SMS-based one-time passwords are deprecated and prohibited as the
standard authentication method because of SIM-swapping and interception
risks. Any temporary exception must be approved by the CISO,
time-limited, and supported by compensating controls.

### 7.5 Password Manager

Employees must use the corporate-licensed enterprise password manager
(source example: **1Password**) to generate and store credentials.
Plain-text files, shared spreadsheets, notes, and unapproved browser
storage are prohibited.

### 7.6 Recovery

Account recovery must verify identity and must not rely solely on easily
discoverable personal information. Recovery codes and hardware keys must
be protected.

## 8. Network Security, Remote Access, and Encryption

### 8.1 Segmentation

Production cloud environments (source examples: AWS and GCP) must be
segmented from staging, development, and corporate office networks using
VPCs, security groups, firewalls, and Zero Trust Network Access
controls.

### 8.2 Remote Access

Remote access must use approved VPN or ZTNA, managed endpoints where
required, MFA, device posture checks, and monitored sessions. Public or
unmanaged networks must not bypass approved access controls.

### 8.3 Encryption in Transit

The source baseline requires **TLS 1.3** and disables TLS 1.0, TLS 1.1,
and SSL on public endpoints. Any compatibility exception must be
documented, risk-assessed, approved by Security, and assigned an expiry
date.

### 8.4 Encryption at Rest

The source baseline requires **AES-256** across databases, object
storage (including S3 buckets), and server volumes. Keys must be managed
through approved key-management services, access-restricted, rotated
according to the cryptographic standard, and protected from the data
they encrypt.

### 8.5 Key Management

Cryptographic keys, secrets, certificates, and production credentials
must be stored in approved secrets/key-management systems. Private keys
must never be committed to source repositories or shared through
chat/email.

### 8.6 Clean Desk and Screen

Laptops must be locked whenever unattended. Whiteboards containing
system architecture, credentials, customer data, or sensitive
information must be erased after meetings. Confidential printouts must
not be left in shared spaces.

## 9. Secure System Development and Change Management

9.1 Security requirements must be included in design, procurement,
development, testing, deployment, and decommissioning.

9.2 Code changes must use approved repositories, peer review, protected
branches, controlled build pipelines, and appropriate testing.

9.3 Secrets and credentials must not be embedded in code. Dependency and
container images must be scanned for known vulnerabilities.

9.4 Production changes must be authorized, tested, logged, and have a
rollback plan proportionate to risk.

9.5 Development and test environments must not use production Restricted
data unless approved and protected. Synthetic or de-identified data
should be preferred.

9.6 High-risk systems must undergo security testing before release and
after material architecture changes.

## 10. Vulnerability, Patch, and Configuration Management

10.1 Assets must be scanned and assessed for vulnerabilities using
approved tools and risk-based schedules.

10.2 Security must define remediation deadlines based on severity,
exploitability, exposure, and business criticality. Actively exploited
vulnerabilities require urgent mitigation.

10.3 Unsupported software, default credentials, unnecessary services,
and insecure configurations must be removed or formally risk-accepted.

10.4 Configuration baselines must be version-controlled. Changes to
production security settings require approval, logging, and validation.

10.5 Exceptions must identify compensating controls, owner, residual
risk, and expiry date.

## 11. Logging, Monitoring, and Detection

11.1 Critical systems must generate logs sufficient to investigate
authentication, authorization, administrative changes, data access,
configuration changes, and security events.

11.2 Logs must be time-synchronized, access-restricted, tamper-resistant
where feasible, and retained according to the approved logging schedule
and legal requirements.

11.3 Security monitoring must detect suspicious sign-ins, privilege
escalation, malware, unusual data transfers, disabled controls, and
anomalous system behavior.

11.4 Monitoring must be proportionate and comply with privacy and
employment laws. Access to monitoring data must itself be restricted and
logged.

## 12. Backup, Business Continuity, and Disaster Recovery

12.1 System owners must define business impact, RTO, and RPO for
critical services.

12.2 Backups must be protected from unauthorized alteration and
ransomware, encrypted, access-restricted, and periodically tested.

12.3 At least periodically, restore tests must verify that data and
services can be recovered---not merely that backup jobs completed.

12.4 Critical systems must have documented recovery procedures,
dependency maps, named owners, communication steps, and escalation
paths.

12.5 Recovery exercises must include realistic scenarios such as
cloud-region outage, identity-provider failure, ransomware, accidental
deletion, and loss of key personnel.

## 13. Third-Party Vendor Risk Assessment

### 13.1 Pre-Contract Due Diligence

Any SaaS vendor, cloud provider, contractor, or service provider
processing company or customer data must complete an InfoSec Vendor
Security Assessment and execute an appropriate DPA before contract
execution or data access.

### 13.2 Minimum Assurance

The source policy requires key vendors to maintain **SOC 2 Type II or
ISO 27001** assurance audited within the past **twelve (12) months**.
Security/Procurement must confirm report period, scope, exceptions,
certification validity, covered services, and any bridge letter. A
certificate or report must not be treated as proof that all risks are
eliminated.

### 13.3 Contractual Controls

Contracts should address confidentiality, security measures, breach
notification, access restrictions, sub-processors, data location, audit
rights, business continuity, vulnerability handling, data
return/deletion, and exit assistance.

### 13.4 Ongoing Monitoring

Vendor risk must be reviewed periodically and after material incidents,
ownership changes, new data categories, new locations, or service
changes. Critical vendors require a documented exit and continuity plan.

## 14. Security Incident Management and Escalation

### 14.1 Immediate Reporting

All users must report suspected phishing, malware, lost devices,
credential theft, data exposure, unauthorized access, service
compromise, or policy violations immediately through the approved 24/7
Security channel.

### 14.2 Severity Matrix

  -----------------------------------------------------------------------
  Severity          Example           Source escalation Required response
                                      target            
  ----------------- ----------------- ----------------- -----------------
  **Severity 1 ---  Active breach,    Escalate to CISO, Activate incident
  Critical**        Restricted-data   CEO, and Legal    command, contain,
                    exfiltration,     within **15       preserve
                    major production  minutes**         evidence, assess
                    compromise                          legal/customer
                                                        impact

  **Severity 2 ---  Targeted malware, Escalate within   Isolate affected
  High**            unauthorized      **1 hour**;       assets, revoke
                    credential access containment       access,
                                      initiated within  investigate scope
                                      **2 hours**       

  **Severity 3 ---  Phishing attempt, Escalate within   Triage, block
  Medium**          policy violation  **4 hours**       indicators,
                    without confirmed                   educate,
                    compromise                          document, monitor
  -----------------------------------------------------------------------

The source policy's targets are internal escalation targets. They do not
replace incident-specific response decisions or statutory notification
deadlines.

### 14.3 Response Lifecycle

1.  Detect and report.
2.  Triage severity and assign incident commander.
3.  Contain affected systems and identities.
4.  Preserve evidence and maintain chain of custody where needed.
5.  Eradicate the cause and remediate vulnerabilities.
6.  Recover services from known-good states.
7.  Validate integrity and monitor for recurrence.
8.  Complete a post-incident review and track corrective actions.

### 14.4 Regulatory and Customer Notification

Legal and Privacy must determine whether notification is required, to
whom, and by when. The GDPR's 72-hour supervisory-authority deadline
applies where the legal threshold is met; it is not a universal
notification rule for all incidents or all customers. Other
jurisdictions and contracts may impose different deadlines.

### 14.5 Source Contact Channels

-   Email: `security-ops@company.com`
-   Slack: `#sec-incident-urgent`
-   24/7/365 availability is stated in the source policy.

These channels must be tested, monitored, and confirmed before
operational use. A backup contact path must exist if email or Slack is
unavailable.

## 15. Security Awareness and Acceptable Use

15.1 All personnel must complete security awareness training at
onboarding and at least annually.

15.2 Role-based training is required for developers, administrators,
finance, HR, customer support, and personnel handling Restricted data.

15.3 Users must not bypass controls, install unauthorized software,
share credentials, access data without a business need, or use
unapproved AI and cloud services for confidential information.

15.4 Phishing simulations and awareness exercises may be conducted in a
proportionate manner. Results should be used for education and risk
reduction, not public shaming.

## 16. Exceptions, Risk Acceptance, and Enforcement

16.1 Exceptions require a documented business justification, affected
assets/data, risk assessment, compensating controls, accountable owner,
approval by the CISO or delegate, and an expiry date.

16.2 High or critical residual risk requires executive risk acceptance.
Exceptions must be reviewed before expiry.

16.3 Violations may result in access suspension, retraining,
disciplinary action up to termination, contract remedies, or legal
referral, subject to applicable law and due process.

## 17. Assurance, Metrics, and Review

Suggested metrics: - MFA coverage and privileged-account compliance. -
Endpoint encryption and EDR coverage. - Critical vulnerability
remediation time. - Access-review completion and overdue access
removal. - Backup restore-test success. - Incident detection,
containment, and recovery times. - Vendor assessment and DPA
completion. - Security training completion. - Policy exceptions by
severity and age.

Security should conduct periodic control testing, tabletop exercises,
internal audits, and independent assessments. This policy is reviewed
annually and after material changes.

## 18. Policy RAG and Interpretation Rules

-   State the exact classification tier and required handling controls.
-   Distinguish mandatory source baselines from formally approved
    exceptions.
-   Do not claim SOC 2 certification or HIPAA applicability without
    evidence.
-   Do not promise that every incident requires a 72-hour notification;
    Legal must assess the legal threshold and jurisdiction.
-   Do not expose secrets, credentials, or restricted operational
    details in answers.
-   If a control or deadline is not specified, say **"This policy does
    not specify the control; refer to InfoSec for the approved
    standard."**

**Related policies:** Customer Data Privacy Policy; BYOD and Endpoint
Security Policy; Remote Work Policy; Code of Business Conduct; Vendor
Risk Management Standard; Business Continuity and Disaster Recovery
Standard.
