---
template_code: access_control
template_version: "1.0.0"
title: Access Control Policy
description: >
  Rules for provisioning, modifying, reviewing, and revoking access to
  systems and data. Maps to SOC 2 CC6.1, CC6.2, CC6.3 and NDPA §24, plus
  CBN §4.2 for fintechs.
framework_codes:
  - soc2
  - ndpa
  - cbn_cyber
  - iso27001
control_refs:
  - {framework: soc2, code: CC6.1}
  - {framework: soc2, code: CC6.2}
  - {framework: soc2, code: CC6.3}
  - {framework: ndpa, code: SEC_24}
  - {framework: cbn_cyber, code: "4.2"}
variables:
  - name: company_name
    required: true
  - name: effective_date
    required: true
  - name: owner
    required: true
    default: Head of Engineering
  - name: review_cadence
    required: false
    default: annually
  - name: access_review_cadence
    label: Access review cadence
    required: false
    default: quarterly
  - name: offboarding_sla
    label: Offboarding SLA
    required: false
    default: same business day
---
# Access Control Policy

**Company:** {{ company_name }}
**Effective date:** {{ effective_date }}
**Owner:** {{ owner }}
**Review cadence:** {{ review_cadence }}

## 1. Purpose

This policy ensures that access to {{ company_name }}'s systems and data is
granted on the principle of least privilege, reviewed regularly, and revoked
promptly when no longer required.

## 2. Scope

Applies to all systems holding {{ company_name }} or customer data, including
production infrastructure, code repositories, customer support tools, admin
consoles, and SaaS applications.

## 3. Identity

- Every individual user has a unique account. Shared accounts on production
  systems are prohibited.
- Service accounts are used only for system-to-system communication and are
  registered with a designated owner.

## 4. Authentication

- Multi-factor authentication (MFA) is mandatory for all users on systems
  that handle customer data, financial data, or production access.
- Where the service supports it, phishing-resistant MFA (security keys or
  device-bound passkeys) is preferred over SMS-based one-time codes.
- Passwords meet the requirements of the Password Policy.

## 5. Authorisation

- Access is granted based on documented role definitions and the principle of
  least privilege. New access requires approval by the requestor's manager and
  the system owner.
- Privileged access (admin, root, super-user) is restricted to a named list
  of users, time-bound where feasible, and logged in full.
- Data access is segmented by sensitivity. Production customer data access is
  read-restricted and write-audited.

## 6. Access review

- A review of all user access is performed {{ access_review_cadence }} by the
  {{ owner }} or delegate.
- Reviews check that current access matches current role, that dormant
  accounts are removed, and that privileged access is still warranted.
- Review evidence (who reviewed what, what changed) is retained for at least
  two years.

## 7. Onboarding and offboarding

- New hires receive access only after manager approval, signed acceptable use
  acknowledgment, and completion of initial security training.
- Departing employees and contractors lose access within {{ offboarding_sla }}
  of their last day. The {{ owner }} maintains an offboarding checklist
  covering: identity provider, code repositories, cloud accounts, customer
  support tools, communication tools, and physical access.
- Role changes within the company trigger an access reassessment within five
  business days.

## 8. Logging and monitoring

- Authentication events (success, failure, MFA challenge) are logged
  centrally and reviewed for anomalies.
- Privileged session activity is logged. Logs are tamper-resistant and
  retained per the Data Retention Policy.

## 9. Exceptions and enforcement

Exceptions require written approval by the {{ owner }} and a documented
compensating control. Violations may result in disciplinary action.

## 10. Review

This policy is reviewed {{ review_cadence }}.
