---
template_code: data_protection
template_version: "1.0.0"
title: Data Protection Policy
description: >
  How personal data is collected, processed, stored, and protected. Maps to
  NDPA §24, §25, §26, §29 and equivalents in POPIA, Kenya DPA. Foundational
  for any African company processing personal data.
framework_codes:
  - ndpa
  - popia
  - kenya_dpa
  - soc2
control_refs:
  - {framework: ndpa, code: SEC_24}
  - {framework: ndpa, code: SEC_25}
  - {framework: ndpa, code: SEC_26}
  - {framework: ndpa, code: SEC_29}
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
  - name: dpo_name
    label: Data Protection Officer name
    required: false
    default: TBD
  - name: dpo_email
    label: DPO contact email
    required: true
  - name: contact_email
    required: true
  - name: data_retention_years
    label: Default retention (years)
    required: false
    default: 7
---
# Data Protection Policy

**Company:** {{ company_name }}
**Effective date:** {{ effective_date }}
**Owner:** {{ owner }}
**Review cadence:** {{ review_cadence }}

## 1. Purpose

This policy describes how {{ company_name }} processes personal data in
compliance with the data protection laws of {{ company_country }} and any
other applicable jurisdiction. It implements the principles of lawfulness,
fairness, transparency, purpose limitation, data minimisation, accuracy,
storage limitation, integrity and confidentiality, and accountability.

## 2. Definitions

- **Personal data**: any information relating to an identified or identifiable
  natural person.
- **Sensitive personal data**: data revealing race, ethnic origin, political
  opinions, religious beliefs, trade union membership, genetic data, biometric
  data, health data, sex life, and sexual orientation. National identifiers
  (BVN, NIN, passport, etc.) are treated as sensitive in our context.
- **Processing**: any operation performed on personal data — collection,
  storage, transmission, use, deletion.
- **Controller**: the party that determines the purposes and means of processing.
- **Processor**: a party processing personal data on behalf of a controller.

## 3. Lawful basis

{{ company_name }} processes personal data only when it has a lawful basis:

- The data subject has given clear, specific, informed consent.
- Processing is necessary for the performance of a contract with the data subject.
- Processing is necessary for compliance with a legal obligation.
- Processing is necessary to protect vital interests.
- Processing is necessary for the legitimate interests of {{ company_name }},
  balanced against the rights of the data subject.

The lawful basis for each processing activity is recorded in the Record of
Processing Activities (ROPA) maintained by the {{ owner }}.

## 4. Data subject rights

Data subjects have the right to:

- Access their personal data.
- Rectify inaccurate data.
- Erase their data ("right to be forgotten") subject to legal exceptions.
- Restrict processing.
- Object to processing.
- Data portability.
- Lodge a complaint with the supervisory authority of {{ company_country }}.

Requests must be acknowledged within five business days and resolved within
30 days. Requests are handled by {{ dpo_email }}.

## 5. Security of processing

{{ company_name }} implements appropriate technical and organisational
measures including:

- Encryption of personal data at rest and in transit.
- Pseudonymisation where it serves the processing purpose.
- Access controls per the Access Control Policy.
- Logging and monitoring of access to personal data.
- Regular testing of restore procedures.
- Vendor due diligence per the Vendor Management Policy.

## 6. Data retention

Personal data is retained no longer than necessary for the purposes for which
it was collected. The default retention is {{ data_retention_years }} years
after the end of the relationship, unless a shorter period applies under law
or longer retention is required for legal claims. The Data Retention Policy
provides per-category retention schedules.

## 7. International transfers

Where personal data is transferred outside {{ company_country }}, the receiving
party must offer an adequate level of protection. We rely on:

- Adequacy decisions where they exist.
- Standard contractual clauses with non-adequate jurisdictions.
- Explicit consent where transfers are occasional and non-systematic.

## 8. Vendors and processors

Every processor handling personal data on our behalf signs a Data Processing
Agreement before processing begins. Sub-processors require advance written
authorisation.

## 9. Breach notification

Personal data breaches are handled per the Incident Response Plan.
{{ company_name }} notifies the supervisory authority within the legally
required window (72 hours under NDPA; shorter for regulated financial
institutions under CBN). Affected data subjects are notified where required.

## 10. Data Protection Officer

{{ dpo_name }} acts as Data Protection Officer for {{ company_name }} and
can be reached at {{ dpo_email }}.

## 11. Review

This policy is reviewed {{ review_cadence }} and after any material change
to processing activities or the regulatory landscape.

For any questions about this policy, contact {{ contact_email }}.
