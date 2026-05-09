#!/bin/bash
set -e

python3 << 'ORACLE'
import json
from pathlib import Path
from datetime import datetime, timedelta, timezone
from collections import defaultdict, deque

# Load all incidents
incident_dir = Path("/input_artifacts/incidents")
incidents = {}

for incident_file in sorted(incident_dir.glob("*.json")):
    with open(incident_file) as f:
        incident = json.load(f)
        incidents[incident["id"]] = incident

# Load hidden constraints
hidden = {}
hidden_path = Path("/solution/hidden_constraints.json")
if hidden_path.exists():
    with open(hidden_path) as f:
        hidden = json.load(f)

print(f"Loaded {len(incidents)} incidents, {len(hidden)} hidden constraints")

# --------------------------------------------------------------
# Extract hidden root causes and additional dependencies from context
# The oracle knows them directly from hidden_constraints.json
# --------------------------------------------------------------
all_dependencies = {}
for inc_id, incident in incidents.items():
    deps = set(incident.get("dependencies", []))
    # Add hidden dependencies
    if inc_id in hidden and hidden[inc_id].get("hidden_additional_dependency"):
        deps.add(hidden[inc_id]["hidden_additional_dependency"])
    all_dependencies[inc_id] = list(deps)

# --------------------------------------------------------------
# Build dependency graph and topological sort
# Uses ALL dependencies including hidden ones
# --------------------------------------------------------------
dep_graph = defaultdict(list)
rdep_graph = defaultdict(list)
in_degree = {inc_id: 0 for inc_id in incidents}

for inc_id in incidents:
    for dep in all_dependencies.get(inc_id, []):
        if dep in incidents:
            dep_graph[inc_id].append(dep)
            rdep_graph[dep].append(inc_id)
            in_degree[inc_id] += 1

# Kahn's algorithm topological sort
queue = deque(
    sorted(
        [inc_id for inc_id, deg in in_degree.items() if deg == 0],
        key=lambda x: (-incidents[x]["severity"], incidents[x]["sla_deadline"])
    )
)
topo_order = []
remaining_in_degree = dict(in_degree)

while queue:
    node = queue.popleft()
    topo_order.append(node)
    dependents = sorted(
        rdep_graph[node],
        key=lambda x: (-incidents[x]["severity"], incidents[x]["sla_deadline"])
    )
    for dependent in dependents:
        remaining_in_degree[dependent] -= 1
        if remaining_in_degree[dependent] == 0:
            queue.append(dependent)

for inc_id in incidents:
    if inc_id not in topo_order:
        topo_order.append(inc_id)

ordered_incidents = topo_order

# --------------------------------------------------------------
# Analysis phase - includes hidden root causes
# --------------------------------------------------------------
incident_analysis = {}
for priority, inc_id in enumerate(ordered_incidents, 1):
    incident = incidents[inc_id]
    root_cause = ""
    if inc_id in hidden:
        root_cause = hidden[inc_id].get("hidden_root_cause", "")

    incident_analysis[inc_id] = {
        "id": incident["id"],
        "title": incident["title"],
        "severity": incident["severity"],
        "affected_systems": incident["affected_systems"],
        "required_engineers": incident["required_engineers"],
        "required_expertise": incident["required_expertise"],
        "sla_deadline": incident["sla_deadline"],
        "estimated_resolution_minutes": incident["estimated_resolution_minutes"],
        "dependencies": all_dependencies.get(inc_id, []),
        "resource_conflicts": incident.get("resource_conflicts", []),
        "recommended_priority": priority,
        "root_cause": root_cause
    }

# --------------------------------------------------------------
# Resource allocation respecting ALL dependencies and no-overlap
# --------------------------------------------------------------
engineers = [
    "alice@company.com",
    "bob@company.com",
    "charlie@company.com",
    "diana@company.com",
    "eve@company.com"
]

BASE_TIME = datetime(2026, 5, 8, 0, 0, 0, tzinfo=timezone.utc)
engineer_free_at = {eng: BASE_TIME for eng in engineers}
incident_end_time = {}

allocation_plan = {}

for inc_id in ordered_incidents:
    incident = incidents[inc_id]
    required_count = incident["required_engineers"]
    duration = timedelta(minutes=incident["estimated_resolution_minutes"])
    sla = datetime.fromisoformat(incident["sla_deadline"].replace("Z", "+00:00"))

    # Earliest start: after ALL dependencies (explicit + hidden)
    earliest_start = BASE_TIME
    for dep in all_dependencies.get(inc_id, []):
        if dep in incident_end_time:
            if incident_end_time[dep] > earliest_start:
                earliest_start = incident_end_time[dep]

    sorted_engineers = sorted(engineers, key=lambda e: engineer_free_at[e])
    chosen = sorted_engineers[:required_count]
    start_time = max(engineer_free_at[eng] for eng in chosen)
    if start_time < earliest_start:
        start_time = earliest_start

    end_time = start_time + duration

    for eng in chosen:
        engineer_free_at[eng] = end_time

    incident_end_time[inc_id] = end_time

    allocation_plan[inc_id] = {
        "assigned_engineers": chosen,
        "start_time": start_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "end_time": end_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
        "will_meet_sla": end_time <= sla,
        "confidence_score": 0.95
    }

# --------------------------------------------------------------
# Generate conflict resolution report
# --------------------------------------------------------------
report = "INCIDENT RESPONSE COORDINATION REPORT\n"
report += "=" * 70 + "\n\n"
report += f"Total Incidents: {len(incidents)}\n"
report += f"Available Engineers: {', '.join(engineers)}\n\n"

report += "ROOT CAUSE ANALYSIS:\n"
for inc_id in ordered_incidents:
    incident = incidents[inc_id]
    rc = incident_analysis[inc_id].get("root_cause", "Unknown")
    report += f"\n  {incident['title']} ({inc_id})\n"
    report += f"    Root Cause: {rc}\n"

report += "\n\nRESOURCE CONFLICTS IDENTIFIED:\n"
conflict_found = False
for inc_id in ordered_incidents:
    incident = incidents[inc_id]
    conflicts = incident.get("resource_conflicts", [])
    if conflicts:
        conflict_found = True
        report += f"\n  {incident['title']} ({inc_id})\n"
        report += f"    Conflicts with: {', '.join(conflicts)}\n"
        report += "    Resolution: Sequential scheduling ensures no engineer overlap.\n"
if not conflict_found:
    report += "  No resource conflicts detected.\n"

report += "\n\nDEPENDENCY ANALYSIS (including hidden dependencies):\n"
dep_found = False
for inc_id in ordered_incidents:
    incident = incidents[inc_id]
    deps = all_dependencies.get(inc_id, [])
    if deps:
        dep_found = True
        dep_end = max(
            (incident_end_time[d].strftime("%Y-%m-%dT%H:%M:%SZ") for d in deps if d in incident_end_time),
            default="N/A"
        )
        report += f"\n  {incident['title']} ({inc_id})\n"
        report += f"    Depends on: {', '.join(deps)}\n"
        report += f"    Dependencies complete by: {dep_end}\n"
        report += f"    This incident starts: {allocation_plan[inc_id]['start_time']}\n"
if not dep_found:
    report += "  No dependencies detected.\n"

report += "\n\nSLA COMPLIANCE STATUS:\n"
for inc_id in ordered_incidents:
    incident = incidents[inc_id]
    plan = allocation_plan[inc_id]
    status = "MEETS SLA" if plan["will_meet_sla"] else "AT-RISK"
    report += f"  {incident['title']} ({inc_id}): {status}\n"
    report += f"    SLA deadline: {incident['sla_deadline']}\n"
    report += f"    Scheduled completion: {plan['end_time']}\n"

sla_count = sum(1 for p in allocation_plan.values() if p["will_meet_sla"])
report += f"\nSummary: {sla_count}/{len(incidents)} incidents will meet SLA.\n"

report += "\n\nENGINEER ALLOCATION SUMMARY:\n"
for eng in engineers:
    assigned = [
        inc_id for inc_id, plan in allocation_plan.items()
        if eng in plan["assigned_engineers"]
    ]
    report += f"  {eng}: {len(assigned)} incident(s) assigned\n"
    for inc_id in assigned:
        plan = allocation_plan[inc_id]
        report += f"    - {inc_id}: {plan['start_time']} -> {plan['end_time']}\n"

report += "\n\nESCALATION RECOMMENDATIONS:\n"
at_risk = [
    inc_id for inc_id, plan in allocation_plan.items()
    if not plan["will_meet_sla"]
]
if at_risk:
    for inc_id in at_risk:
        report += f"  ESCALATE: {incidents[inc_id]['title']} ({inc_id}) is at-risk.\n"
else:
    report += "  All incidents scheduled within SLA.\n"

# Write outputs
output_dir = Path("/logs/agent")
output_dir.mkdir(parents=True, exist_ok=True)

with open(output_dir / "incident_analysis.json", "w") as f:
    json.dump(incident_analysis, f, indent=2)

with open(output_dir / "resource_allocation_plan.json", "w") as f:
    json.dump(allocation_plan, f, indent=2)

with open(output_dir / "conflict_resolution_report.txt", "w") as f:
    f.write(report)

print(f"Oracle completed: {len(incidents)} incidents analyzed")
print(f"Output files written to /logs/agent/")

ORACLE
