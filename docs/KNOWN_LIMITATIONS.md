# Known Limitations

> **Audience:** All team members, AI agents, and anyone evaluating this project.
> Honesty about limitations is a feature, not a weakness.

## Identity Resolution

### No Biometric Re-Identification
The system does NOT perform face recognition, gait analysis, or any biometric re-identification. Identity resolution uses a heuristic:

```
camera_track + zone + time_proximity + badge_activity = resolved_identity
```

**What this means:**
- We can say "a person entered Z0 at 09:15:00" (camera track)
- We can say "badge B-1001 was swiped at Z0 at 09:14:55" (badge reader)
- We can say "these are likely the same person because same zone, 5 seconds apart"
- We CANNOT say "this is definitely Alice Chen" from video alone
- We CANNOT re-identify a person across different cameras without a badge event nearby

**Why this matters:** Do not present track-to-identity links with certainty in the dashboard. Always show confidence levels. Document this in any demo narrative.

### No Cross-Camera Tracking
A camera track ID (e.g., `TRK-20250315-001`) is valid only within a single camera's field of view for a single session. When a person leaves one camera and enters another, they get a new track ID. The system can only link these if there is a badge swipe or other identity event between the transitions.

## Computer Vision

### Detection, Not Understanding
The CV pipeline detects objects (persons, bags, etc.) using YOLO. It does NOT:
- Detect suspicious behavior (loitering, running, fighting)
- Detect emotions or intent
- Read text from documents or screens
- Detect specific individuals without badge correlation
- Guarantee detection in all lighting/angle conditions

### Tracking Limitations
Object tracking (e.g., ByteTrack) can lose tracks due to:
- Occlusion (person walks behind a pillar)
- Camera angle changes
- Poor lighting
- Multiple people crossing paths

Track loss results in a new track ID, which looks like a new person. This is a known and expected limitation.

### YOLO Confidence
YOLO confidence scores vary by:
- Object size in frame
- Lighting conditions
- Occlusion
- Distance from camera

Do not treat confidence < 0.5 as reliable.

## Correlation

### Temporal Windows
The correlation engine uses configurable time windows. If events happen outside the window (e.g., USB insert 2 hours before badge swipe), they may not be correlated. This is by design — the alternative (correlating everything) produces too many false positives.

### False Positives
The deterministic scoring system can produce false positives:
- An authorized researcher working late triggers after_hours_activity
- A legitimate USB backup triggers usb_activity
- A large software download triggers large_outbound_transfer

**The system generates signals, not convictions.** Every incident requires human review.

### Correlation Completeness
The MVP correlation engine covers a limited set of patterns. Real SOC systems have hundreds of correlation rules. Ours has the patterns documented in `docs/INCIDENT_CONTRACT.md` and nothing more. Do not claim coverage beyond what is implemented.

## Data

### Synthetic vs Real Data Boundary
Cyber telemetry is synthetic/scripted. Computer-vision validation uses real recorded scenario video when the asset is available. Unit tests may use synthetic CV fixtures.

### Telemetry & Campus Context
Every event, person, zone, and asset definition in this repository represents the fictional Meridian Research Campus prototype. Do not present synthetic cyber telemetry as live enterprise SIEM logs.

### Video Processing in Foundation
The foundation phase does not include a running video pipeline. CV pipeline modules in `cv/` are initialized as contracts; real recorded scenario video is ingested during Component A integration checkpoints. Example events in `data/examples/` and test fixtures in `tests/fixtures/` provide deterministic contract ground truth.

## Scale

### Not Production Scale
This system is designed for hackathon demonstration:
- SQLite, not PostgreSQL
- In-memory correlation, not distributed processing
- Single server, not clustered
- Dozens of events per demo, not millions per day

### No Persistence Guarantees
SQLite provides basic persistence but not:
- Concurrent write safety under load
- Backup/recovery procedures
- Data retention policies

## Security

### The Security Platform Itself Is Not Hardened
Ironic but true — this is a security event correlation platform that does not implement:
- Authentication on its own API (for hackathon simplicity)
- Encryption at rest
- Audit logging of its own operations
- Input sanitization beyond JSON schema validation

For a production system, all of these would be required.

## LLM Integration

### Not Implemented Yet
The LLM narrative generation is documented as a future feature. If implemented:
- It must only receive structured incident JSON
- It must only return narrative text
- It must be completely optional
- The system must work identically without it
- It must not influence scoring, detection, or correlation
