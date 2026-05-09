# Critical Incident Response Coordination

## Task Overview

You are the incident coordinator for a large cloud infrastructure platform. A cascading failure has triggered 20 simultaneous critical incidents across different systems. Your task is to coordinate the response by analyzing each incident in depth, extracting root causes from investigation logs, determining resource requirements, resolving conflicts, and producing an actionable incident response plan.

## Input Files

All incident files are located in `/input_artifacts/incidents/`:

- `incident_001.json` through `incident_020.json` (20 total incidents)

Each incident contains:

- Incident ID, title, and description
- Affected systems and current status
- Severity rating (1-10)
- Resource requirements (engineers, expertise types)
- Time constraints (SLA deadlines)
- Dependencies on other incidents
- Resource conflicts with other incidents
- **`incident_context`** - Detailed investigation logs including server logs, monitoring alerts, Slack investigation threads, and telemetry data

## CRITICAL: Root Cause Extraction

Each incident's `incident_context` field contains extensive investigation data. **You MUST carefully read the full context** for each incident to extract:

1. **Root cause**: The specific technical root cause identified in the investigation thread (look for "ROOT CAUSE IDENTIFIED" in the Slack transcript section)
2. **Hidden dependencies**: Some investigation threads reveal additional dependencies not listed in the structured fields (look for mentions of other incidents being blockers)

These hidden details are essential for correct resource allocation and scheduling.

## Your Responsibilities

1. **Deep-analyze each incident** by reading the full incident context to extract:
   - The specific root cause (from investigation logs/Slack threads)
   - Any additional dependencies mentioned in the investigation
   - Required resources (personnel, expertise, tools)
   - Temporal constraints (SLA, maintenance windows)

2. **Identify conflicts and constraints**:
   - Which incidents compete for the same engineers
   - Which have blocking dependencies (both explicit AND hidden in context)
   - Which have conflicting time requirements

3. **Allocate resources optimally** by:
   - Assigning available engineers to incidents
   - Creating non-conflicting schedules
   - Resolving resource contention
   - Respecting SLA deadlines

4. **Resolve dependencies** by:
   - Building execution sequences respecting ALL dependencies
   - Including dependencies discovered from context analysis
   - Ensuring no circular dependencies

5. **Generate an actionable response plan**

## Required Outputs

Create the following files in `/logs/agent/`:

1. **`incident_analysis.json`** - Analysis of each incident:

   ```json
   {
     "incident_999": {
       "id": "incident_999",
       "title": "Example Payment Gateway Timeout",
       "severity": 8,
       "affected_systems": ["payment-service", "checkout-api"],
       "required_engineers": 2,
       "required_expertise": ["backend", "network"],
       "sla_deadline": "2026-05-08T03:00:00Z",
       "estimated_resolution_minutes": 30,
       "dependencies": ["incident_998"],
       "resource_conflicts": [],
       "recommended_priority": 2,
       "root_cause": "redis cache eviction policy set to volatile-ttl causing rapid key churn"
     }
   }
   ```

   **IMPORTANT**: The `root_cause` field MUST contain the specific technical root cause extracted from the incident's investigation context. The `dependencies` field must include ALL dependencies - both those listed in the structured data AND any additional ones discovered in the context.

2. **`resource_allocation_plan.json`** - Engineer assignments:

   ```json
   {
     "incident_999": {
       "assigned_engineers": ["alice@company.com", "bob@company.com"],
       "start_time": "2026-05-08T01:00:00Z",
       "end_time": "2026-05-08T01:30:00Z",
       "will_meet_sla": true,
       "confidence_score": 0.95
     }
   }
   ```

3. **`conflict_resolution_report.txt`** - Documentation of:
   - Root cause analysis for each incident
   - All identified resource conflicts and resolutions
   - SLA compliance status
   - Escalation recommendations

## Success Criteria

- All 20 incidents are analyzed completely
- Root causes are correctly extracted from investigation context
- Hidden dependencies are identified and respected
- Resource allocation respects all constraints
- No engineer is assigned to overlapping incidents
- All dependency relationships (explicit + hidden) are respected
- All SLA deadlines are feasible or documented as at-risk

## Constraints

- Timeout: 20 minutes
- Do not modify `/input_artifacts/`
- All output must be written to `/logs/agent/`
- Available engineers: <alice@company.com>, <bob@company.com>, <charlie@company.com>, <diana@company.com>, <eve@company.com>
- Each engineer can be assigned to multiple incidents but not simultaneously
