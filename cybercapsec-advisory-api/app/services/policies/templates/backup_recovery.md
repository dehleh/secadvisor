---
template_code: backup_recovery
template_version: "1.0.0"
title: Backup and Recovery Policy
description: >
  Backup frequency, retention, integrity testing, and restoration procedures.
  Maps to SOC 2 A1.2 and CBN §4.6.
framework_codes:
  - soc2
  - iso27001
  - cbn_cyber
control_refs:
  - {framework: soc2, code: A1.2}
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
  - name: rpo_hours
    label: Recovery Point Objective (hours)
    required: false
    default: 24
  - name: rto_hours
    label: Recovery Time Objective (hours)
    required: false
    default: 8
  - name: restore_test_cadence
    label: Restore test cadence
    required: false
    default: quarterly
---
# Backup and Recovery Policy

**Company:** {{ company_name }}
**Effective date:** {{ effective_date }}
**Owner:** {{ owner }}
**Review cadence:** {{ review_cadence }}

## 1. Purpose

This policy ensures that {{ company_name }} can recover its critical data
and services after a disruptive event, within agreed objectives.

## 2. Recovery objectives

- **Recovery Point Objective (RPO)**: {{ rpo_hours }} hours.
  We tolerate at most {{ rpo_hours }} hours of data loss for critical
  systems.
- **Recovery Time Objective (RTO)**: {{ rto_hours }} hours.
  Critical services are restored within {{ rto_hours }} hours of a
  declared disaster.

## 3. Scope

Applies to all production data stores, application configuration, source
code, and infrastructure-as-code repositories.

## 4. Backup strategy

- **Production databases**: automated point-in-time recovery (PITR) and
  daily snapshots, retained for at least 30 days.
- **File and object storage**: cross-region replication; versioning enabled
  on critical buckets; lifecycle policies move older versions to cold
  storage.
- **Source code and IaC**: source-of-truth in a managed Git provider with
  automated mirrors. Repository backups are exported weekly.
- **Application configuration and secrets**: managed via the secrets store;
  rotation and recovery procedures documented.

Backups are encrypted at rest. Access to backups follows the Access Control
Policy and is logged.

## 5. Restore testing

A formal restore test is performed {{ restore_test_cadence }} and after any
material change to the backup architecture. Each test:

1. Selects a critical system at random or per a rotation.
2. Restores from a recent backup into a non-production environment.
3. Validates data integrity against expected reference points.
4. Records the time taken (compared to RTO) and findings.

Findings are tracked to closure. An untested backup is not considered a
working backup.

## 6. Disaster recovery plan

The {{ owner }} maintains a runbook covering common disaster scenarios:

- Primary database loss
- Cloud region outage
- Ransomware affecting production data
- Source code repository compromise

Each scenario specifies: detection signal, escalation path, recovery steps,
validation checks, and communications.

The plan is tested annually via tabletop exercise alongside the Incident
Response Plan.

## 7. Roles

- **{{ owner }}** is accountable for backup operation, test execution, and
  the disaster recovery plan.
- **Engineering on-call** executes restores during incidents per the
  runbook.
- **Executive sponsor** declares disaster status when RTO is at risk and
  authorises customer-facing communications.

## 8. Review

This policy is reviewed {{ review_cadence }} and after any restore test
that fails to meet RTO or RPO.
