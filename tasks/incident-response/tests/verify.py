#!/usr/bin/env python3
"""Verifier for incident response task with hidden constraint checking."""
import json
from pathlib import Path
from datetime import datetime

score = 0.0
checks = []

VALID_ENGINEERS = {
    "alice@company.com", "bob@company.com", "charlie@company.com",
    "diana@company.com", "eve@company.com"
}

REQUIRED_ANALYSIS_FIELDS = [
    "id", "title", "severity", "required_engineers",
    "sla_deadline", "estimated_resolution_minutes", "dependencies",
    "root_cause"
]

REQUIRED_ALLOCATION_FIELDS = [
    "assigned_engineers", "start_time", "end_time", "will_meet_sla"
]

def add_check(name, passed, weight):
    global score
    checks.append((name, passed, weight))
    if passed:
        score += weight
    print(f"{name}: {'PASS' if passed else 'FAIL'} ({weight})")

Path("/logs/verifier").mkdir(parents=True, exist_ok=True)
input_dir = Path("/input_artifacts/incidents")
hidden_path = Path("/tests/hidden_constraints.json")
analysis_path = Path("/logs/agent/incident_analysis.json")
allocation_path = Path("/logs/agent/resource_allocation_plan.json")
report_path = Path("/logs/agent/conflict_resolution_report.txt")

# Load ground truth input artifacts
ground_truth = {}
for p in sorted(input_dir.glob("*.json")):
    with open(p, "r", encoding="utf-8") as f:
        ground_truth[p.stem] = json.load(f)

# Load hidden constraints
hidden = {}
if hidden_path.exists():
    with open(hidden_path, "r", encoding="utf-8") as f:
        hidden = json.load(f)

NUM_INCIDENTS = len(ground_truth)
print(f"Ground truth loaded: {NUM_INCIDENTS} incidents")
print(f"Hidden constraints loaded: {len(hidden)} entries")

# ================================================================
# Check 1: Required files exist (0.03)
# ================================================================
files_exist = analysis_path.exists() and allocation_path.exists() and report_path.exists()
add_check("required_files_exist", files_exist, 0.03)

analysis = None
allocation = None

if files_exist:
    # ================================================================
    # Check 2: Incident analysis is valid JSON with all incidents (0.03)
    # ================================================================
    try:
        with open(analysis_path) as f:
            analysis = json.load(f)
        has_all = isinstance(analysis, dict) and len(analysis) >= NUM_INCIDENTS
        fields_complete = all(
            all(field in inc for field in REQUIRED_ANALYSIS_FIELDS)
            for inc in analysis.values()
        ) if has_all else False
    except Exception:
        has_all, fields_complete = False, False
    add_check("incident_analysis_valid", has_all and fields_complete, 0.03)

    # ================================================================
    # Check 3: Resource allocation is valid JSON with all incidents (0.03)
    # ================================================================
    try:
        with open(allocation_path) as f:
            allocation = json.load(f)
        alloc_has_all = isinstance(allocation, dict) and len(allocation) >= NUM_INCIDENTS
        alloc_fields_ok = all(
            all(field in alloc for field in REQUIRED_ALLOCATION_FIELDS)
            for alloc in allocation.values()
        ) if alloc_has_all else False
    except Exception:
        alloc_has_all, alloc_fields_ok = False, False
    add_check("resource_allocation_valid", alloc_has_all and alloc_fields_ok, 0.03)

    # ================================================================
    # Check 4: All incidents present (0.02)
    # ================================================================
    add_check("all_incidents_present", has_all and alloc_has_all, 0.02)
else:
    add_check("incident_analysis_valid", False, 0.03)
    add_check("resource_allocation_valid", False, 0.03)
    add_check("all_incidents_present", False, 0.02)

# ================================================================
# Check 5: Accurate structured data extraction (0.07)
# severity, required_engineers, estimated_resolution_minutes, deps
# ================================================================
if analysis and isinstance(analysis, dict) and ground_truth:
    accurate_analysis = True
    for inc_id, gt_data in ground_truth.items():
        if inc_id not in analysis:
            accurate_analysis = False
            break
        an_data = analysis[inc_id]
        if an_data.get("severity") != gt_data.get("severity") or \
           an_data.get("required_engineers") != gt_data.get("required_engineers") or \
           an_data.get("estimated_resolution_minutes") != gt_data.get("estimated_resolution_minutes"):
            accurate_analysis = False
            break
        # Build expected deps: explicit + hidden additional dependency
        expected_deps = set(gt_data.get("dependencies", []))
        if inc_id in hidden and hidden[inc_id].get("hidden_additional_dependency"):
            expected_deps.add(hidden[inc_id]["hidden_additional_dependency"])
        if set(an_data.get("dependencies", [])) != expected_deps:
            accurate_analysis = False
            break
    add_check("accurate_structured_data", accurate_analysis, 0.07)
else:
    add_check("accurate_structured_data", False, 0.07)

# ================================================================
# Check 6: Hidden root cause extraction (0.30) - GRADUATED SCORING
# Score is proportional to accuracy ratio, not binary pass/fail.
# This is the key differentiator for single vs multi agent gap.
# ================================================================
RC_WEIGHT = 0.30
if analysis and isinstance(analysis, dict) and hidden:
    root_cause_correct = 0
    root_cause_total = 0
    for inc_id, h_data in hidden.items():
        if not h_data.get("hidden_root_cause"):
            continue
        root_cause_total += 1
        if inc_id not in analysis:
            continue
        agent_rc = str(analysis[inc_id].get("root_cause", "")).lower()
        hidden_rc = h_data["hidden_root_cause"].lower()
        # Extract key technical terms from hidden root cause
        key_terms = []
        words = hidden_rc.split()
        for w in words:
            w_clean = w.strip(".,;:'\"()[]{}").lower()
            if len(w_clean) >= 3 and (
                any(c.isdigit() for c in w_clean) or
                '-' in w_clean or
                '_' in w_clean or
                '/' in w_clean or
                '.' in w_clean or
                '@' in w_clean or
                w_clean in ['redis', 'kafka', 'sentinel', 'quorum', 'pgbouncer',
                           'coredns', 'istio', 'minio', 'vault', 'harbor',
                           'alertmanager', 'prometheus', 'elasticsearch',
                           'spark', 'kubelet', 'containerd', 'jwks',
                           'dataloader', 'lua', 'terraform', 'gitlab',
                           'n+1', 'split-brain', 'rebalancing', 'failover']
            ):
                key_terms.append(w_clean)

        if not key_terms:
            hidden_words = set(hidden_rc.split())
            agent_words = set(agent_rc.split())
            overlap = len(hidden_words & agent_words)
            if overlap >= len(hidden_words) * 0.4:
                root_cause_correct += 1
        else:
            matched = sum(1 for term in key_terms if term in agent_rc)
            if matched >= max(1, len(key_terms) * 0.4):
                root_cause_correct += 1
            else:
                print(f"  {inc_id} root cause MISS: key_terms={key_terms[:5]}, matched={matched}")

    rc_ratio = root_cause_correct / root_cause_total if root_cause_total > 0 else 0
    rc_score = round(rc_ratio * RC_WEIGHT, 4)
    print(f"Root cause accuracy: {root_cause_correct}/{root_cause_total} = {rc_ratio:.2f}")
    print(f"Root cause graduated score: {rc_score} / {RC_WEIGHT}")
    score += rc_score
    checks.append(("hidden_root_causes_extracted", rc_ratio >= 0.95, RC_WEIGHT))
else:
    checks.append(("hidden_root_causes_extracted", False, RC_WEIGHT))

# ================================================================
# Check 7: Hidden dependency detection (0.20) - GRADUATED SCORING
# Score is proportional to accuracy ratio.
# ================================================================
HDEP_WEIGHT = 0.20
if analysis and isinstance(analysis, dict) and hidden:
    hidden_dep_correct = 0
    hidden_dep_total = 0
    for inc_id, h_data in hidden.items():
        hdep = h_data.get("hidden_additional_dependency")
        if not hdep:
            continue
        hidden_dep_total += 1
        if inc_id not in analysis:
            continue
        agent_deps = set(analysis[inc_id].get("dependencies", []))
        if hdep in agent_deps:
            hidden_dep_correct += 1
        else:
            print(f"  {inc_id} hidden dep MISS: expected {hdep} in deps, got {agent_deps}")

    hdep_ratio = hidden_dep_correct / hidden_dep_total if hidden_dep_total > 0 else 0
    hdep_score = round(hdep_ratio * HDEP_WEIGHT, 4)
    print(f"Hidden dependency accuracy: {hidden_dep_correct}/{hidden_dep_total} = {hdep_ratio:.2f}")
    print(f"Hidden dep graduated score: {hdep_score} / {HDEP_WEIGHT}")
    score += hdep_score
    checks.append(("hidden_dependencies_detected", hdep_ratio >= 0.8, HDEP_WEIGHT))
else:
    checks.append(("hidden_dependencies_detected", False, HDEP_WEIGHT))

# ================================================================
# Check 8: Accurate engineer count allocation (0.10)
# ================================================================
if allocation and isinstance(allocation, dict) and ground_truth:
    acc_count = True
    for inc_id, gt_data in ground_truth.items():
        if inc_id not in allocation:
            acc_count = False
            break
        req_eng = gt_data.get("required_engineers", 1)
        assigned = len(allocation[inc_id].get("assigned_engineers", []))
        if assigned != req_eng:
            print(f"Wrong engineer count for {inc_id}: expected {req_eng}, got {assigned}")
            acc_count = False
            break
    add_check("accurate_engineers_count", acc_count, 0.10)
else:
    add_check("accurate_engineers_count", False, 0.10)

# ================================================================
# Check 9: No engineer time overlaps (0.05)
# ================================================================
no_overlaps = False
if allocation and isinstance(allocation, dict):
    no_overlaps = True
    engineer_times = {}
    try:
        for inc_id, alloc in allocation.items():
            if "start_time" not in alloc or "end_time" not in alloc:
                continue
            start = datetime.fromisoformat(alloc["start_time"].replace("Z", "+00:00"))
            end = datetime.fromisoformat(alloc["end_time"].replace("Z", "+00:00"))
            for eng in alloc.get("assigned_engineers", []):
                if eng not in engineer_times:
                    engineer_times[eng] = []
                engineer_times[eng].append((inc_id, start, end))
        for eng, slots in engineer_times.items():
            for i, (id1, s1, e1) in enumerate(slots):
                for id2, s2, e2 in slots[i + 1:]:
                    if s1 < e2 and s2 < e1:
                        print(f"Overlap: {eng} assigned to {id1} and {id2}")
                        no_overlaps = False
                        break
    except Exception:
        no_overlaps = False
add_check("no_engineer_time_overlaps", no_overlaps, 0.05)

# ================================================================
# Check 10: Dependencies respected in scheduling (0.10)
# This includes BOTH explicit and hidden dependencies
# ================================================================
deps_respected = False
if allocation and isinstance(allocation, dict) and ground_truth:
    deps_respected = True
    try:
        end_times = {}
        for i, a in allocation.items():
            if "end_time" in a:
                end_times[i] = datetime.fromisoformat(a["end_time"].replace("Z", "+00:00"))

        for inc_id, inc_data in ground_truth.items():
            deps = inc_data.get("dependencies", [])
            if inc_id in allocation and "start_time" in allocation[inc_id]:
                start = datetime.fromisoformat(allocation[inc_id]["start_time"].replace("Z", "+00:00"))
                for dep in deps:
                    if dep in end_times and start < end_times[dep]:
                        print(f"Dependency violated: {inc_id} starts before {dep} ends")
                        deps_respected = False
    except Exception:
        deps_respected = False
add_check("dependencies_respected", deps_respected, 0.10)

# ================================================================
# Check 11: Valid engineers only (0.05)
# ================================================================
valid_engineers_only = False
if allocation and isinstance(allocation, dict):
    valid_engineers_only = True
    try:
        for inc_id, alloc in allocation.items():
            for eng in alloc.get("assigned_engineers", []):
                if eng not in VALID_ENGINEERS:
                    print(f"Invalid engineer: {eng}")
                    valid_engineers_only = False
    except Exception:
        valid_engineers_only = False
add_check("valid_engineers_only", valid_engineers_only, 0.05)

# ================================================================
# Check 12: Conflict resolution report quality (0.02)
# ================================================================
report_valid = False
if files_exist:
    try:
        with open(report_path) as f:
            content = f.read()
        if len(content) > 500 and sum(
            1 for kw in ["conflict", "sla", "dependency", "engineer",
                         "resolution", "root cause", "escalat", "priority"]
            if kw in content.lower()
        ) >= 4:
            report_valid = True
    except Exception:
        pass
add_check("conflict_report_complete", report_valid, 0.02)

# ================================================================
# Final score
# ================================================================
print("\n" + "=" * 60)
print(f"Final Score: {round(score, 4)}")
for name, passed, weight in checks:
    print(f"  {name}: {'PASS' if passed else 'FAIL'} (weight={weight})")
print("=" * 60)

Path("/logs/verifier/reward.txt").write_text(str(round(score, 4)))
exit(0 if score >= 0.99 else 1)
