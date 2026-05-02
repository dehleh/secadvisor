---
template_code: incident_response
template_version: "1.0.0"
title: Incident Response Plan
description: >
  Steps to detect, contain, eradicate, recover from, and learn from security
  incidents. Maps to SOC 2 CC7.3, NDPA §40, CBN §4.8.
framework_codes:
  - soc2
  - ndpa
  - cbn_cyber
  - iso27001
control_refs:
  - {framework: soc2, code: CC7.3}
  - {framework: ndpa, code: SEC_40}
  - {framework: cbn_cyber, code: "4.8"}
variables:
  - name: company_name
    required: true
  - name: company_country
    required: true
  - name: effective_date
    required: true
  - name: owner
    required: true
    default: Head of Security
  - name: review_cadence
    required: false
    default: annually
  - name: contact_email
    required: true
  - name: dpo_email
    required: true
  - name: ndpc_notification_window
    label: NDPC notification window
    required: false
    default: 72 hours
  - name: cbn_notification_window
    label: CBN notification window
    required: false
    default: 24 hours
---
# Incident Response Plan

**Company:** {{ company_name }}
**Effective date:** {{ effective_date }}
**Owner:** {{ owner }}
**Review cadence:** {{ review_cadence }}

## 1. Purpose

This plan defines how {{ company_name }} detects, responds to, and recovers
from security incidents. The goal is to minimise impact, meet regulatory
notification obligations, and learn from each incident.

## 2. Scope

This plan applies to any event affecting the confidentiality, integrity, or
availability of {{ company_name }} systems or customer data. Examples
include unauthorised access, data exfiltration, ransomware, denial-of-service
attacks, lost or stolen devices, and confirmed successful phishing.

## 3. Incident severity

| Severity | Description | Response time |
|----------|-------------|---------------|
| **SEV-1** | Active breach with confirmed customer data exposure or production outage | Immediate |
| **SEV-2** | Confirmed unauthorised access without confirmed exfiltration; significant degradation | Within 1 hour |
| **SEV-3** | Suspected incident pending investigation | Within 4 hours |
| **SEV-4** | Minor security event, no customer impact | Within 1 business day |

## 4. Roles

- **Incident Commander** ({{ owner }}): leads the response, makes decisions
  on containment, communications, and escalation.
- **Technical lead**: drives investigation, containment, and recovery.
- **Communications lead**: coordinates internal and external messaging.
- **Legal / DPO**: assesses notification obligations under applicable laws.
- **Executive sponsor**: makes business and disclosure decisions for SEV-1
  and SEV-2 incidents.

## 5. Phases

### 5.1 Detect

Sources of detection include monitoring alerts, customer reports, employee
reports, and third-party notifications. Anyone discovering a suspected
incident must report it to {{ contact_email }} within one hour.

### 5.2 Triage

The Incident Commander assigns a severity and convenes the response team.
Document the incident in the incident log: time, source, observed indicators,
suspected scope.

### 5.3 Contain

Take immediate action to stop the incident from spreading. Examples: revoke
compromised credentials, isolate affected hosts, disable affected services,
block malicious IPs at the perimeter. Preserve forensic evidence where
practical.

### 5.4 Eradicate

Remove the root cause: malware, persistent access, vulnerable code or
configuration. Apply patches, rotate keys and credentials, rebuild affected
systems where containment confidence is low.

### 5.5 Recover

Restore systems to normal operation. Validate that the incident is resolved
and that recovered systems are clean. Heightened monitoring continues for at
least seven days.

### 5.6 Learn

Within 14 days of resolution, conduct a post-incident review covering: root
cause, timeline, what worked, what didn't, and concrete corrective actions.
Track corrective actions to closure.

## 6. Notification

### 6.1 Regulatory

Personal data breaches likely to result in risk to individuals' rights must
be notified to:

- The Nigeria Data Protection Commission (NDPC) within
  {{ ndpc_notification_window }} of becoming aware, where {{ company_country }}
  is Nigeria or NDPA applies.
- The Central Bank of Nigeria within {{ cbn_notification_window }} where
  {{ company_name }} is a regulated financial entity.
- The relevant supervisory authority of any other applicable jurisdiction
  within the legally required window.

The Legal / DPO lead coordinates notification, supported by drafts maintained
by the {{ owner }}.

### 6.2 Affected individuals

Where the breach is likely to result in high risk to data subjects' rights,
affected individuals are notified without undue delay through their primary
contact channel.

### 6.3 Customers and partners

Customer notification follows contractual obligations and is reviewed by the
executive sponsor before sending.

## 7. Communication

- Internal status updates are posted to the security channel every two hours
  during active SEV-1 / SEV-2 incidents.
- External communications go through the Communications lead. Staff do not
  speak to media or post publicly about live incidents.

## 8. Testing

This plan is tested at least {{ review_cadence }} via tabletop exercise.
Findings drive corrective actions tracked to closure.

## 9. Contacts

- **Report an incident**: {{ contact_email }}
- **Data protection enquiries**: {{ dpo_email }}
