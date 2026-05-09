# Oracle Derivation - Warehouse Fulfillment Plan

## Input Files

| File | Description |
|------|-------------|
| `/input_artifacts/fulfillment/orders_batch.json` | 86 customer orders including SKU quantities, urgency, deadlines, handling requirements |
| `/input_artifacts/fulfillment/warehouse_inventory.json` | On-hand stock per SKU per warehouse zone |
| `/input_artifacts/fulfillment/fulfillment_constraints.json` | Zone limits, priority order, SLA thresholds, cold-chain restrictions, overselling policy |

## Planning Methodology

The oracle represents an expert-curated fulfillment plan requiring operational judgment at each stage. Multiple valid plans exist for this dataset; the oracle captures one defensible interpretation where competing priorities, partial inventory, and SLA risk factors must be weighed contextually.

### Stage 1 - Priority Sorting and Order Triage

Orders are evaluated using the priority ladder in `fulfillment_constraints.json`:
`CRITICAL > HIGH > STANDARD > ECONOMY`

Within the same tier, earlier-deadline orders are favored - but this is a judgment call when deadlines are close, since colder-chain handling complexity may affect wave feasibility for a real supervisor.

### Stage 2 - SKU-Level Zone Allocation

For each order and each requested SKU:
- Cold-chain products (handling = `cold_chain`) must come from zones listed in `cold_chain_allowed_zones` (`D-COLD-CHAIN`, `H-CROSS-DOCK`). This is a hard operational constraint enforced by refrigeration infrastructure.
- For non-cold-chain SKUs, zone selection requires judgment: spreading picks across multiple zones to avoid overloading zone capacity, or consolidating picks to simplify the picking wave - trade-offs a warehouse operations expert weighs case by case.
- Where inventory is insufficient to fully serve an order, partial allocation requires a reasoned explanation connecting the shortfall to inventory position and the affected customer's SLA exposure.

### Stage 3 - Order Status Determination

- `fulfilled` - all requested units allocated
- `partial` - some units allocated; shortfall documented with business rationale
- `unfulfillable` - zero units available; requires escalation

Status assignment requires contextual judgment when inventory is borderline - a supervisor may reallocate from a lower-priority order to fully serve a critical one, accepting a partial for the lower-priority order instead.

### Stage 4 - Zone Picking List Aggregation

Picking lists aggregate all zone-level allocations into actionable pick sheets. Accuracy requires careful cross-order accounting to ensure no zone's `capacity_limit` (from `max_picks_per_zone_per_wave`) is exceeded.

### Stage 5 - Conflict and Risk Reporting

The fulfillment conflict report requires genuine operational judgment:

- **inventory_conflicts**: Identifying which SKUs are over-demanded vs. supply, and writing resolution narratives that explain rationing decisions in business terms
- **sla_risks**: Assessing which orders face SLA exposure based on `sla_hours_by_priority` thresholds - this involves interpreting both deadline proximity and order status together, requiring holistic reasoning about customer impact
- **partial_fulfillments**: Documenting the 14 orders with partial status and the operational reasoning behind each cut

The LLM judge scores explanation quality, conflict report accuracy, and picking list correctness as distinct dimensions - reflecting that a correct fulfillment plan is not sufficient; it must also be defensible and auditable.

## Oracle Value Traceability

| Oracle value | Traced to |
|---|---|
| 86 entries in `order_fulfillment_plan` | 86 records in `orders_batch.json` |
| Cold-chain SKUs only from D-COLD-CHAIN / H-CROSS-DOCK | `cold_chain_allowed_zones` in constraints |
| Zone `capacity_limit` values in picking lists | `max_picks_per_zone_per_wave` in constraints |
| SLA risk thresholds: CRITICAL=24h, HIGH=36h, STANDARD=72h, ECONOMY=120h | `sla_hours_by_priority` in constraints |
| 14 partial fulfillments | SKUs where total demand exceeds combined zone stock at time of allocation |
| 5 inventory conflict SKUs | Cross-order demand exceeds total available units across all eligible zones |

## solve.sh

The oracle script copies a pre-curated expert fulfillment plan:
```bash
cp /solution/oracle.json /logs/agent/output.json
```

`oracle.json` represents one valid, expert-reviewed solution to this planning problem.
The LLM judge accepts semantically equivalent plans that satisfy inventory, priority, SLA, and zone constraints.