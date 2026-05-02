---
template_code: acceptable_use
template_version: "1.0.0"
title: Acceptable Use Policy
description: >
  Rules for staff use of company systems, devices, and data. Required reading
  for all staff. Maps to SOC 2 CC1.4 and supports the Information Security
  Policy.
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
    default: Chief Operating Officer
  - name: review_cadence
    required: false
    default: annually
  - name: contact_email
    required: true
---
# Acceptable Use Policy

**Company:** {{ company_name }}
**Effective date:** {{ effective_date }}
**Owner:** {{ owner }}
**Review cadence:** {{ review_cadence }}

## 1. Purpose

This policy defines the acceptable use of {{ company_name }} systems, devices,
and data by employees, contractors, and anyone with authorised access. Every
person with access must read and acknowledge this policy.

## 2. General use

- Use {{ company_name }} systems and data only for legitimate business
  purposes. Limited personal use is permitted where it does not interfere
  with work or violate this policy.
- Do not share your credentials with anyone, including colleagues or
  managers, under any circumstances.
- Lock your screen when stepping away from your device.
- Report suspected security incidents to {{ contact_email }} immediately.

## 3. Devices

- Devices used for work must have full-disk encryption enabled.
- Devices must run a supported, patched operating system. Apply security
  updates within seven days of release.
- Personal devices used for work must be enrolled in our device management
  programme where applicable.
- Lost or stolen devices must be reported to {{ contact_email }} within
  one hour of discovery.

## 4. Software and applications

- Install software only from trusted sources. Do not install pirated or
  cracked software.
- Open-source dependencies pulled into our codebase must be reviewed per the
  Secure Development Policy.
- Do not disable security software (antivirus, EDR, MDM) on company devices.

## 5. Email, messaging, and the internet

- Treat unexpected attachments and links with suspicion. Verify the sender
  out-of-band before opening.
- Do not forward sensitive {{ company_name }} information to personal email.
- Do not transmit unencrypted personal data, financial data, or credentials
  over email.

## 6. Data handling

- Customer data must stay within sanctioned systems. Do not export it to
  personal devices, personal cloud storage, or unsanctioned tools.
- Production data is not to be used in development or testing environments
  without explicit approval and appropriate masking.
- Sensitive printouts must be securely shredded.

## 7. Generative AI tools

- Do not paste customer data, source code, or confidential information into
  external generative AI tools (ChatGPT, Claude, Gemini, etc.) unless the
  tool is explicitly approved for that data class with an appropriate data
  handling agreement in place.
- Output from AI tools used in work products must be reviewed for accuracy
  and licensing.

## 8. Travel and remote work

- Public Wi-Fi requires a company VPN or equivalent secure tunnel for work
  use.
- Maintain physical possession of work devices. Do not leave devices
  unattended in public spaces.

## 9. Departure

On the last day of employment or engagement:

- Return all {{ company_name }} property.
- Do not retain copies of {{ company_name }} data on personal devices,
  accounts, or storage.
- Confidentiality obligations survive the end of the relationship.

## 10. Enforcement

Violations of this policy may result in disciplinary action up to and
including termination, and where appropriate, legal action.

## 11. Acknowledgment

I have read and understood this Acceptable Use Policy and agree to comply
with it.
