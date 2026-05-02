---
template_code: vendor_management
template_version: "1.0.0"
title: Vendor Management Policy
description: >
  Process for onboarding, assessing, and offboarding third-party vendors.
  Maps to SOC 2 CC9.2 and NDPA §29.
framework_codes:
  - soc2
  - ndpa
  - iso27001
control_refs:
  - {framework: soc2, code: CC9.2}
  - {framework: ndpa, code: SEC_29}
variables:
  - name: company_name
    required: true
  - name: effective_date
    required: true
  - name: owner
    required: true
    default: Chief Operating Officer
  - name: review_cadence
    required: false
    default: annually
  - name: critical_vendor_review_cadence
    label: Critical vendor review cadence
    required: false
    default: annually
---
# Vendor Management Policy

**Company:** {{ company_name }}
**Effective date:** {{ effective_date }}
**Owner:** {{ owner }}
**Review cadence:** {{ review_cadence }}

## 1. Purpose

This policy ensures that third parties processing {{ company_name }} data or
operating in our supply chain do so under appropriate security, privacy, and
contractual controls.

## 2. Vendor classification

Each vendor is classified at onboarding:

- **Tier 1 — Critical**: handles customer personal data, financial data, or
  has access to production systems.
- **Tier 2 — Important**: handles internal business data or has user-level
  access to internal systems.
- **Tier 3 — Standard**: limited or no data access (e.g. office supplies).

Classification determines the depth of due diligence and review cadence.

## 3. Due diligence

Before a contract is signed:

- **Tier 1**: complete a security questionnaire; review the vendor's SOC 2
  Type II, ISO 27001 certificate, or equivalent; review breach history; sign
  a Data Processing Agreement; document the lawful basis for any
  international transfer.
- **Tier 2**: complete a short security questionnaire; sign a confidentiality
  agreement and DPA where personal data is involved.
- **Tier 3**: standard procurement process.

Findings from due diligence are documented in the vendor register.

## 4. Contracts

All vendors handling personal data sign a Data Processing Agreement covering
the requirements of NDPA §29 and any other applicable jurisdictions:

- Subject matter, duration, nature, and purpose of processing.
- Categories of data and data subjects.
- Obligations to protect data, notify breaches, support data subject
  requests, and delete or return data on termination.
- Sub-processor authorisation and notification.

## 5. Ongoing review

- Tier 1 vendors are reviewed {{ critical_vendor_review_cadence }}, including
  re-validation of certifications and review of any incidents.
- Tier 2 and 3 are reviewed at contract renewal.
- Any vendor incident affecting {{ company_name }} data triggers a re-review
  regardless of cadence.

## 6. Vendor incident handling

Vendor incidents potentially affecting {{ company_name }} data are managed
under the Incident Response Plan. The {{ owner }} is notified within four
hours of vendor disclosure.

## 7. Offboarding

When a vendor relationship ends, the {{ owner }} confirms:

- Access revoked for all {{ company_name }} systems.
- Data returned or deleted per the contract, with written confirmation.
- Vendor record updated.

## 8. Vendor register

The {{ owner }} maintains a register of all current vendors with:
classification, services provided, data categories handled, contract dates,
DPA status, and last review date. The register is reviewed
{{ review_cadence }}.
