---
template_code: information_security
template_version: "1.0.0"
title: Information Security Policy
description: >
  Top-level statement of the company's commitment to security, scope of the
  ISMS, roles and responsibilities, and policy hierarchy. Foundational for
  SOC 2 CC1.1 and NDPA §24.
framework_codes:
  - soc2
  - ndpa
  - iso27001
  - cbn_cyber
control_refs:
  - {framework: soc2, code: CC1.1}
  - {framework: ndpa, code: SEC_24}
  - {framework: iso27001, code: A.5.1}
variables:
  - name: company_name
    label: Company name
    required: true
  - name: company_country
    label: Country code
    required: true
  - name: effective_date
    label: Effective date
    required: true
  - name: owner
    label: Policy owner
    required: true
    default: Chief Executive Officer
  - name: review_cadence
    label: Review cadence
    required: false
    default: annually
  - name: contact_email
    label: Security contact email
    required: true
---
# Information Security Policy

**Company:** {{ company_name }}
**Effective date:** {{ effective_date }}
**Owner:** {{ owner }}
**Review cadence:** {{ review_cadence }}
**Contact:** {{ contact_email }}

## 1. Purpose

This policy establishes {{ company_name }}'s commitment to protecting the
confidentiality, integrity, and availability of information assets entrusted
to us by our customers, employees, and partners. It defines the scope of our
information security programme and the responsibilities of every person in
the company.

## 2. Scope

This policy applies to:

- All employees, contractors, and third parties acting on behalf of {{ company_name }}.
- All systems, applications, and data owned or operated by {{ company_name }},
  whether hosted on our infrastructure, in cloud services, or on personal
  devices used for work.
- All customer data, employee data, financial data, and intellectual property
  in our custody.

## 3. Principles

{{ company_name }} commits to:

1. **Confidentiality.** Personal and proprietary data is accessed only by
   those who need it to do their jobs.
2. **Integrity.** Information is protected from unauthorised modification.
3. **Availability.** Systems and data are available to authorised users when
   needed.
4. **Accountability.** Actions on critical systems are logged and attributable.
5. **Continuous improvement.** We measure our security posture and improve it
   based on findings, incidents, and emerging threats.

## 4. Roles and responsibilities

- **Board / Executive leadership** approves this policy, sets the security
  strategy, and ensures resources are available.
- **The {{ owner }}** owns this policy and is accountable for its enforcement.
- **All staff** are responsible for following this policy and the supporting
  policies it references. Staff must complete security awareness training and
  report suspected incidents to {{ contact_email }}.
- **The Data Protection Officer** (where designated under {{ company_country }}
  data protection law) advises on data protection compliance and acts as
  liaison with the supervisory authority.

## 5. Policy hierarchy

This policy is the top of the policy hierarchy. The following policies operate
underneath it and provide specific controls:

- Access Control Policy
- Data Protection Policy
- Data Retention Policy
- Incident Response Plan
- Acceptable Use Policy
- Vendor Management Policy
- Change Management Policy
- Backup and Recovery Policy

Where policies conflict, this policy and applicable law prevail.

## 6. Compliance and exceptions

Violations of this policy may result in disciplinary action up to and
including termination, and where appropriate, legal action. Exceptions to
this policy must be documented, risk-assessed, time-bound, and approved by
the {{ owner }}.

## 7. Review

This policy is reviewed {{ review_cadence }} and after any material change to
the business, regulatory environment, or threat landscape. The {{ owner }} is
accountable for the review.

## 8. Acknowledgment

All staff are required to read and acknowledge this policy at onboarding and
on each annual review.
