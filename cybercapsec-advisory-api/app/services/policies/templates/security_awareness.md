---
template_code: security_awareness
template_version: "1.0.0"
title: Security Awareness Training Policy
description: >
  Cadence and content of security awareness training for all staff.
  Maps to SOC 2 CC1.4.
framework_codes:
  - soc2
  - ndpa
  - iso27001
control_refs:
  - {framework: soc2, code: CC1.4}
variables:
  - name: company_name
    required: true
  - name: effective_date
    required: true
  - name: owner
    required: true
    default: Head of People
  - name: review_cadence
    required: false
    default: annually
  - name: training_cadence
    label: Training cadence for all staff
    required: false
    default: annually
  - name: phishing_simulation_cadence
    label: Phishing simulation cadence
    required: false
    default: quarterly
---
# Security Awareness Training Policy

**Company:** {{ company_name }}
**Effective date:** {{ effective_date }}
**Owner:** {{ owner }}
**Review cadence:** {{ review_cadence }}

## 1. Purpose

People are the most-targeted and most-trained line of defence in cyber
security. This policy ensures every {{ company_name }} staff member receives
relevant, current security training.

## 2. Scope

All employees, contractors, and long-term consultants with access to
{{ company_name }} systems must complete the training programme.

## 3. Onboarding training

Within their first two weeks, every new joiner completes:

- Information security overview (key policies, what to do if you see
  something suspicious)
- Acceptable Use Policy walkthrough and acknowledgment
- Phishing recognition basics
- Data handling fundamentals (what is sensitive, where it must stay)
- Incident reporting (who to tell, how fast)

Completion is tracked. New hires cannot receive production access until
training is complete.

## 4. Annual refresh

Every staff member completes a refresh course {{ training_cadence }}. The
refresh covers:

- Updates to policies and processes
- Recent incident lessons (anonymised)
- New threat patterns relevant to {{ company_name }}'s sector

Completion is tracked and reported to the {{ owner }}. Non-completion is
followed up by people leaders.

## 5. Role-specific training

Additional training is required for roles with elevated risk:

- **Engineering**: secure coding fundamentals, common vulnerability
  patterns (OWASP Top 10), dependency hygiene.
- **Customer support**: social engineering recognition, secure handling of
  customer verification.
- **Finance / payments**: business email compromise (BEC) recognition,
  payment authorisation controls.

## 6. Phishing simulations

{{ company_name }} runs phishing simulations {{ phishing_simulation_cadence }}.
Results are reported as aggregate metrics. Individuals who click are
provided with brief targeted education; repeated clicks may trigger more
intensive training but are not, on their own, a basis for discipline.

## 7. Training content

Content is reviewed {{ review_cadence }} to remain current. Content is
short, scenario-based, and relevant to {{ company_name }}'s actual risk
profile — not generic checkbox training.

## 8. Records

The {{ owner }} maintains evidence of:

- Completion records per staff member, per training event.
- Phishing simulation results (aggregate metrics).
- Training content version history.

Records are retained for at least three years.

## 9. Review

This policy is reviewed {{ review_cadence }}.
