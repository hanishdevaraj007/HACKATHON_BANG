# Zone & Policy Model

> **Audience:** Developers and AI agents working on policy evaluation, zone configuration, or access control logic.

## Zone Configuration

Configuration file: `config/zones.json`

### Meridian Research Campus Zones

| Zone ID | Name | Level | Level Label | Auth Required |
|---------|------|-------|-------------|---------------|
| Z0 | Lobby / Reception | 0 | Public | None |
| Z1 | Employee Offices | 1 | Internal | Badge |
| Z2 | Collaboration Area | 2 | Controlled | Badge |
| Z3-LAB | R&D Laboratory | 3 | Restricted | Badge + PIN |
| Z3-ARCHIVE | Restricted Data Archive | 3 | Restricted | Badge + PIN |
| Z4 | Core Server Room | 4 | Critical | Badge + Biometric |

### Zone Level Model

The Z0–Z4 system is our **configurable prototype model**. It is NOT a claim that a universal industry standard defines these exact levels.

```
Level 0 — Public      : Open areas, minimal access control
Level 1 — Internal    : Employee-only, badge required
Level 2 — Controlled  : Authorized employees, badge required
Level 3 — Restricted  : Need-to-know, badge + PIN, may require escort
Level 4 — Critical    : Highest security, badge + biometric, escort required
```

### Zone Configuration Fields

Every zone in `config/zones.json` has these fields:

| Field | Type | Description |
|-------|------|-------------|
| `zone_id` | string | Unique zone identifier |
| `name` | string | Human-readable zone name |
| `level` | integer (0-4) | Security level |
| `level_label` | string | Human-readable level name |
| `authorized_roles` | array of strings | Roles allowed in this zone |
| `authorized_persons` | array of strings | Specific person IDs with explicit access |
| `allowed_hours` | object {start, end} | Time window for allowed access (24h format, UTC) |
| `required_auth` | string | Authentication method required |
| `escort_required` | boolean | Whether an escort is needed |
| `cameras` | array of strings | Camera IDs monitoring this zone |
| `devices` | array of strings | Device IDs in this zone |
| `network_segment` | string | Network CIDR for this zone |
| `assets` | array of strings | Protected asset IDs in this zone |

## Policy Evaluation Logic

### Access Authorization Check

```
Given: actor, zone, timestamp

1. Look up actor's role from config/organization.json
2. Look up zone from config/zones.json
3. Check: Is actor's role in zone.authorized_roles?
   - OR is actor's person_id in zone.authorized_persons?
   - If neither → UNAUTHORIZED ACCESS signal (+25 points)
4. Check: Is timestamp within zone.allowed_hours?
   - If not → AFTER HOURS signal (+15 points)
5. Check: Does zone.escort_required == true?
   - If yes, is there a second authorized person in the zone?
   - If no escort detected → flag for investigation
```

### Asset Sensitivity Check

```
Given: event involving a file, device, or physical asset

1. Look up zone's assets list
2. If the asset is in a zone with level >= 3 → SENSITIVE ASSET (+20 points)
3. If the file has classification == "confidential" → SENSITIVE ASSET (+20 points)
```

### USB Policy Check

```
Given: usb_insert event

1. If zone.level >= 2 → USB ACTIVITY signal (+15 points)
2. If followed by file_access with destination = USB → elevate
```

### Network Transfer Check

```
Given: network_transfer event

1. If direction == "outbound" AND bytes_transferred > threshold → LARGE OUTBOUND (+15 points)
2. Default threshold: 100 MB (104857600 bytes)
3. Threshold should be configurable
```

### Multi-Signal Correlation

```
Given: multiple signals for the same actor within a time window

1. If signal_count >= 3 within 60 minutes → MULTI-SIGNAL (+10 points)
2. Time window should be configurable
```

## Organization Configuration

Configuration file: `config/organization.json`

### Roles

| Role ID | Name | Max Zone Level |
|---------|------|---------------|
| visitor | Visitor | 0 |
| employee | Employee | 2 |
| researcher | Researcher | 3 |
| security_admin | Security Administrator | 4 |
| executive | Executive | 3 |

### Sample Persons

| Person ID | Name | Role | Badge | Account |
|-----------|------|------|-------|---------|
| P001 | Alice Chen | researcher | B-1001 | achen |
| P002 | Bob Martinez | employee | B-1002 | bmartinez |
| P003 | Carol Okafor | security_admin | B-1003 | cokafor |
| P004 | David Kim | visitor | B-9001 | (none) |
| P005 | Eva Johansson | executive | B-1005 | ejohansson |

## Policy Violation Scenarios

### Scenario 1: Unauthorized Zone Access
Bob Martinez (employee, max level 2) badges into Z3-LAB (level 3).
→ Immediate `unauthorized_zone_access` signal (+25)

### Scenario 2: After-Hours + USB in Restricted Zone
Alice Chen (researcher, authorized for Z3-LAB) badges in at 21:00 UTC (after hours 08:00–18:00), inserts USB.
→ `after_hours_activity` (+15) + `usb_activity` (+15) = 30 points (MEDIUM)

### Scenario 3: Data Exfiltration Chain
Bob Martinez enters Z3-LAB (unauthorized +25), inserts USB (+15), copies confidential file (+20), large outbound transfer detected (+15).
→ 75 points (HIGH), plus if 3+ signals → (+10) = 85 (CRITICAL)
