# Warehouse Order Fulfillment Planning

## Task Overview

You are planning a same-day warehouse fulfillment wave. The warehouse has inventory spread across multiple zones, and customer orders have different urgency levels, deadlines, item handling constraints, and stock availability risks. Your job is to read the order, inventory, and constraint files and produce a defensible fulfillment plan that a warehouse supervisor could use for the next picking wave.

## Input Files

All input files are located in `/input_artifacts/fulfillment/`:

- `/input_artifacts/fulfillment/orders_batch.json` — customer orders, items, quantities, urgency levels, deadlines, destinations, and notes.
- `/input_artifacts/fulfillment/warehouse_inventory.json` — available on-hand units by warehouse zone and SKU.
- `/input_artifacts/fulfillment/fulfillment_constraints.json` — zone capacity limits, priority order, SLA rules, cold-chain restrictions, and overselling rules.

Your working directory is `/workspace`.

## Planning Requirements

Analyze every order in `orders_batch.json`. For each order, decide whether it can be fully fulfilled, partially fulfilled, or cannot be fulfilled from available inventory.

Your plan must:

1. Include every order exactly once in the order fulfillment plan.
2. Allocate item quantities only from warehouse zones where the SKU exists with available inventory.
3. Never oversell inventory. The total quantity allocated for a SKU from a zone must not exceed that zone's available quantity.
4. Prioritize orders using the priority order in `fulfillment_constraints.json`; if inventory is scarce, earlier-deadline high-priority orders should be favored over lower-priority orders.
5. Respect handling constraints, especially cold-chain SKUs, which may only be allocated from allowed cold-chain zones listed in the constraints file.
6. Build actionable warehouse picking lists by zone, aggregating all assigned units for each SKU.
7. Identify inventory conflicts, partial fulfillments, unfulfillable items, and SLA risks in the conflict report.
8. Explain allocation decisions clearly enough for a warehouse supervisor to audit the plan.

Do not modify any files under `/input_artifacts/`. Do not write outputs outside `/logs/agent/`.

---

## Output Instructions

Write your final answer to `/logs/agent/output.json` in this exact JSON format:

```json
{
  "order_fulfillment_plan": [
    {
      "order_id": "<str>",
      "customer": "<str>",
      "urgency": "<str>",
      "sla_deadline": "<str>",
      "status": "fulfilled | partial | unfulfillable",
      "requested_units": <int>,
      "allocated_units": <int>,
      "assigned_items": [
        {
          "sku": "<str>",
          "quantity_requested": <int>,
          "quantity_allocated": <int>,
          "allocations": [
            {
              "warehouse_zone": "<str>",
              "quantity": <int>
            }
          ]
        }
      ],
      "reasoning": "<str>"
    }
  ],
  "warehouse_picking_lists": [
    {
      "warehouse_zone": "<str>",
      "items_to_pick": [
        {
          "sku": "<str>",
          "total_quantity": <int>,
          "order_ids": ["<str>"]
        }
      ],
      "total_picks": <int>,
      "capacity_limit": <int>
    }
  ],
  "fulfillment_conflict_report": {
    "inventory_conflicts": [
      {
        "sku": "<str>",
        "requested_shortfall_total": <int>,
        "affected_order_ids": ["<str>"],
        "resolution": "<str>"
      }
    ],
    "sla_risks": [
      {
        "order_id": "<str>",
        "risk_reason": "<str>",
        "recommended_action": "<str>"
      }
    ],
    "partial_fulfillments": ["<str>"],
    "picking_wave_summary": "<str>",
    "summary": "<str>"
  }
}
```

Do not write anything else to `/logs/agent/output.json`.
