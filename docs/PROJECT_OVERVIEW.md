# Project Overview — Meridian Security Platform

> **Audience:** Humans and AI coding agents with no prior context.
> Read this document FIRST before working on any component.

## What Is This?

The **Meridian Security Platform** is a multi-modal security event correlation system that detects and explains security incidents by correlating physical and cyber events across an organization.

## What Problem Does It Solve?

Security operations centers today deal with fragmented tools:
- CCTV systems show video but don't understand access control
- Badge systems log swipes but don't see what happened on camera
- Endpoint agents detect USB insertions but don't know who physically plugged it in
- Network monitors see data transfers but can't correlate them to physical movements

This platform bridges those gaps by:
1. **Normalizing** all events into a single schema
2. **Resolving** identities across modalities (camera track + badge + account)
3. **Enriching** events with zone policies and organizational context
4. **Correlating** events using deterministic finite state machines
5. **Scoring** incidents with an explainable, auditable point system
6. **Presenting** evidence timelines and graphs on a real-time dashboard

## What It Is NOT

- Not a production SOC tool — it's a hackathon prototype
- Not using biometric re-identification — identity resolution uses zone + time + badge correlation
- Not dependent on LLMs — LLMs are optional for narrative generation only
- Not using a graph database — evidence graphs are lightweight in-memory structures
- Not claiming computer vision capabilities beyond YOLO detection + supported tracking

## The Fictional Organization

**Meridian Research Campus** — a configurable fictional organization with:
- 6 zones (Z0 through Z4) with escalating security levels
- 5 roles (visitor, employee, researcher, security_admin, executive)
- 5 sample persons with badges and accounts
- Cameras, badge readers, workstations, and network devices per zone

The Z0–Z4 system is our configurable prototype model, NOT a universal industry standard.

## Architecture Summary

```
REAL WORLD
    ↓
SOURCE PROCESSORS (CV, badge, endpoint, network)
    ↓
NORMALIZED EVENT SCHEMA (schema/event.schema.json)
    ↓
ENTITY RESOLUTION (camera_track + zone + time + badge)
    ↓
ZONE / POLICY CONTEXT (config/zones.json)
    ↓
POLICY SIGNAL + CORRELATION (deterministic FSMs)
    ↓
INCIDENT ENGINE (scoring + evidence assembly)
    ↓
EVIDENCE (timeline + graph)
    ↓
API / WEBSOCKET (FastAPI)
    ↓
DASHBOARD (vanilla HTML/CSS/JS)
    ↓
OPTIONAL LLM NARRATIVE (never load-bearing)
```

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python, FastAPI, SQLite |
| CV | OpenCV, Ultralytics YOLO |
| Frontend | Vanilla HTML/CSS/JavaScript, WebSocket |
| Data | JSON schemas, JSON config |
| Testing | pytest, jsonschema |
| Validation | jsonschema |

## Current State

**Foundation phase complete.** The repository contains:
- ✅ Directory structure with component boundaries
- ✅ JSON schemas (event, incident, scoring)
- ✅ Configuration files (zones, organization, scoring)
- ✅ Example event data
- ✅ Shared contracts module
- ✅ Foundation test suite
- ✅ Full documentation

**Not yet implemented:**
- ❌ CV pipeline (Component A)
- ❌ Backend API and correlation engine (Component B)
- ❌ Dashboard UI (Component C)

## Data Sourcing & Validation Principle

Cyber telemetry is synthetic/scripted. Computer-vision validation uses real recorded scenario video when the asset is available. Unit tests may use synthetic CV fixtures.

## Key Documents

| Document | Purpose |
|----------|---------|
| `docs/ARCHITECTURE.md` | Detailed architecture and data flow |
| `docs/EVENT_CONTRACT.md` | Normalized event schema documentation |
| `docs/INCIDENT_CONTRACT.md` | Incident and scoring model |
| `docs/COMPONENT_BOUNDARIES.md` | Who owns what, what you can/cannot modify |
| `docs/AI_ENGINEERING_RULES.md` | Rules every developer and AI agent must follow |
| `docs/ZONE_POLICY.md` | Zone configuration and policy model |
| `docs/TESTING_STRATEGY.md` | How to write and run tests |
| `docs/PROMPT_TEMPLATE.md` | Master AI prompt template for each team member |
| `docs/TEAM_WORKFLOW.md` | Development workflow and integration process |
| `docs/INTEGRATION_CHECKPOINTS.md` | Integration milestones and verification |
| `docs/DECISION_LOG.md` | Architectural decisions and rationale |
| `docs/KNOWN_LIMITATIONS.md` | Honest limitations of the system |
