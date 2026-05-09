# Task: Agricultural Resource Redistribution Planning (Ethiopia)

## Objective

Optimize the redistribution of fertilizers and seeds across 50 regional centers in Ethiopia to maximize food security. The goal is to minimize the aggregate yield gap (target vs. actual) while strictly adhering to logistics, budget, and storage constraints.

## Task Setup

- **Working Directory**: `/workspace`
- **Input Data**:
  - **Regional Briefs**: 50 text files in `environment/input_artifacts/regional_briefs/` (named `region_001.txt` through `region_050.txt`).
  - **Resource Snapshot**: `environment/input_artifacts/agri_resource_snapshot.json` containing initial inventory levels and warehouse capacities.
- **Output Location**: Write your final result to `/workspace/output.json`.

## Constraints

1. **Budget**: Total redistribution cost must not exceed **$5,000,000**.
   - Transportation Cost: Fixed at **$1,000 per ton** moved between any two centers.
2. **Storage**: No regional center can exceed its storage capacity (default 500 tons, unless specified otherwise in regional briefs).
3. **Yield Optimization**: Shipments must prioritize regions with the largest yield gaps to maximize the Food Security Impact Score.
4. **Operational Constraints**: You must extract and respect buried constraints found in the regional briefs (e.g., road closures, warehouse integrity issues, local regulatory mandates).

## Output Schema

Your final output must be a single JSON object with the following structure:

```json
{
  "redistribution_plan": {
    "total_estimated_cost": number,
    "food_security_impact_score": number, 
    "strategy_summary": "string"
  },
  "target_inventory_by_region": [
    {
      "region_id": "string",
      "fertilizer_urea_final": number,
      "fertilizer_dap_final": number,
      "seeds_hybrid_final": number,
      "seeds_local_final": number
    }
  ],
  "shipment_schedule": [
    {
      "from_region": "string",
      "to_region": "string",
      "item": "string",
      "quantity_tons": number,
      "estimated_cost": number
    }
  ],
  "critical_constraints_identified": [
    {
      "type": "string",
      "location": "string",
      "description": "string"
    }
  ]
}
```

> [!NOTE]
> `food_security_impact_score` must be a value between 0.00 and 1.00, representing the percentage of the total yield gap addressed.

## Execution Steps

1. Analyze all 50 regional briefs to extract inventory shortages, yield gaps, and operational constraints.
2. Cross-reference findings with the `agri_resource_snapshot.json`.
3. Plan a redistribution strategy that maximizes impact while staying within budget and capacity limits.
4. Generate the final `output.json`.

## Verification Logic (Transparency)

To ensure fair evaluation, the following logic is applied by the verifier:
1. **Budget Compliance**: `Total Shipments (tons) * $1,000 / ton <= $5,000,000`.
2. **Impact Score Formula**: 
   - `Improvement = Max(0, Sum(Final_Inventory) - Sum(Initial_Inventory))`
   - `Addressed_Value = Min(Yield_Gap, Improvement)`
   - `Score = Sum(Addressed_Value across all regions) / Total_Yield_Gap`
3. **Tolerance**: The `food_security_impact_score` in your output must match the calculated score within a **±0.1 tolerance**.
4. **Non-Negative Constraint**: All final inventory values must be non-negative.
5. **Constraint Reporting**: The `critical_constraints_identified` block in the output JSON must contain at least 2 substantiated findings (type, location, description) extracted from the briefs.

---
**Note**: Any violation of hard constraints (budget, capacity, non-negative stock) results in a score of 0.0. Compliance with the JSON schema and correctly identifying constraints is rewarded through partial credit.
