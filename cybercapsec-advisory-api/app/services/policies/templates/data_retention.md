---
template_code: data_retention
template_version: "1.0.0"
title: Data Retention Policy
description: >
  Per-category retention schedules and deletion procedures. Maps to NDPA §26
  storage limitation and SOC 2 C1.2.
framework_codes:
  - ndpa
  - popia
  - kenya_dpa
  - soc2
control_refs:
  - {framework: ndpa, code: SEC_26}
  - {framework: soc2, code: C1.2}
variables:
  - name: company_name
    required: true
  - name: company_country
    required: true
  - name: effective_date
    required: true
  - name: owner
    required: true
    default: Data Protection Officer
  - name: review_cadence
    required: false
    default: annually
  - name: data_retention_years
    required: false
    default: 7
  - name: marketing_retention_months
    label: Marketing data retention (months)
    required: false
    default: 24
---
# Data Retention Policy

**Company:** {{ company_name }}
**Effective date:** {{ effective_date }}
**Owner:** {{ owner }}
**Review cadence:** {{ review_cadence }}

## 1. Purpose

This policy defines how long {{ company_name }} retains different categories
of data and how data is deleted at the end of its retention period. It
implements the storage limitation principle of {{ company_country }} data
protection law.

## 2. Retention schedule

| Category | Default retention | Driver |
|----------|-------------------|--------|
| Customer account records | {{ data_retention_years }} years after account closure | Legal claims, tax/audit |
| Transaction records | {{ data_retention_years }} years | Financial regulation |
| KYC documents (where applicable) | {{ data_retention_years }} years | AML / financial regulation |
| Customer support correspondence | 3 years after last contact | Service quality, claims |
| Marketing contact data | {{ marketing_retention_months }} months from last engagement | Consent decay |
| Employee records | 7 years after departure | Labour law |
| Application logs | 90 days hot, 12 months archive | Operational, security |
| Security/audit logs | 12 months minimum | Forensics, compliance |
| Backups | 30 days operational | Recovery |
| Website analytics (with PII) | 14 months | Best practice |

Where a more specific legal or contractual requirement applies, the longer
period takes precedence and is documented in the Record of Processing
Activities.

## 3. Deletion

At the end of a retention period, data is:

- **Deleted** from primary systems and backups, where deletion is feasible.
- **Anonymised** so individuals are no longer identifiable, where retention
  of aggregated insights is needed for the business.
- **Archived** with restricted access where ongoing legal claims require it.

Automated deletion is implemented wherever possible. Manual deletion runs
on a {{ review_cadence }} cycle for categories that cannot be automated.

## 4. Litigation hold

Where {{ company_name }} reasonably anticipates litigation or regulatory
investigation, retention is suspended for relevant data. Holds are issued in
writing by the {{ owner }} and tracked to release.

## 5. Data subject deletion requests

A data subject's request to delete personal data is handled per the Data
Protection Policy, normally within 30 days. Where retention is legally
required, the request is partially fulfilled with a written explanation.

## 6. Vendors

Vendors processing personal data are required by their Data Processing
Agreements to delete or return data on contract termination. The {{ owner }}
verifies vendor deletion at offboarding.

## 7. Review

This policy is reviewed {{ review_cadence }} or when legal requirements
change. Retention schedules are adjusted as new data categories emerge.
