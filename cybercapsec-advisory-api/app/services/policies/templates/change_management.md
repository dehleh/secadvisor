---
template_code: change_management
template_version: "1.0.0"
title: Change Management Policy
description: >
  Rules for proposing, reviewing, approving, and deploying changes to
  production systems. Maps to SOC 2 CC8.1.
framework_codes:
  - soc2
  - iso27001
  - cbn_cyber
control_refs:
  - {framework: soc2, code: CC8.1}
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
---
# Change Management Policy

**Company:** {{ company_name }}
**Effective date:** {{ effective_date }}
**Owner:** {{ owner }}
**Review cadence:** {{ review_cadence }}

## 1. Purpose

This policy ensures that changes to {{ company_name }} production systems are
authorised, tested, reviewed, and deployed in a controlled manner that
minimises risk to customers and the business.

## 2. Scope

Applies to changes affecting production infrastructure, application code,
configuration, data schemas, third-party integrations, and security controls.

## 3. Change classification

| Class | Examples | Approval required |
|-------|----------|-------------------|
| **Standard** | Routine, low-risk, frequently-performed (e.g. dependency bumps under SemVer minor) | Pre-approved |
| **Normal** | Day-to-day changes via the standard pipeline | Peer review |
| **Significant** | Schema migrations, auth changes, payment flow changes | Peer review + tech lead |
| **Emergency** | Hotfixes for SEV-1/SEV-2 incidents | Verbal sign-off + post-hoc review within 24h |

## 4. Process

### 4.1 Propose

Changes are proposed via pull request in the relevant repository. The PR
description states: what is changing, why, the user-facing impact, the
rollback plan, and any sensitive areas affected.

### 4.2 Review

- Every PR merged to a production branch requires at least one approving
  review from someone other than the author.
- Significant changes require an additional approval from a tech lead or the
  {{ owner }}.
- Automated checks (CI tests, linters, security scanners) must pass before
  merge.

### 4.3 Test

- Unit tests cover new logic; integration tests cover cross-component
  behaviour.
- Schema migrations are tested against a copy of production data shape in a
  staging environment.
- Significant changes go through a manual smoke test in staging before
  production deployment.

### 4.4 Deploy

- Production deployments are automated through the deployment pipeline.
  Direct manual deploys are prohibited except in emergency.
- Deployments include health checks; failed health checks roll back
  automatically where possible.
- Post-deployment monitoring period is at least one hour for significant
  changes.

### 4.5 Document

Every merged PR is the change record. The PR contains: author, reviewers,
deployment time, and (for significant changes) the rollback plan.

## 5. Emergency changes

Emergency changes follow an abbreviated process:

1. Verbal or chat sign-off from {{ owner }} or designated on-call.
2. Apply the fix.
3. Open a retroactive PR documenting what was done within 24 hours.
4. Conduct a post-incident review covering the change.

## 6. Production access

Direct production access (e.g. database write access, server SSH) is granted
only for diagnosis and incident response, and is logged. Routine changes
must go through the deployment pipeline, not manual production edits.

## 7. Review

This policy is reviewed {{ review_cadence }}. Process changes derived from
incident retros are tracked through the change management system itself.
