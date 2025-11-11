# Agricultural Classification Keywords

This document lists all keywords and patterns used to classify bills as agricultural/farm worker related.

## Category: Farm Worker Rights

**Core Terms**:
- `farm worker`, `farmworker`, `agricultural worker`
- `agricultural labor`, `agricultural employee`, `agricultural employment`
- `campo`, `campesino` (Spanish terms)

**Context**:
- Bills establishing or modifying rights for agricultural workers
- Legal protections specific to farm labor
- Enforcement of labor laws in agriculture

**Example Bills**:
- AB 5 (2019): Gig worker classification (affects agricultural contractors)
- AB 1066: Farm worker overtime
- SB 295: Farm worker heat illness prevention

## Category: Safety

**Health Hazards**:
- `heat illness`, `heat stress`, `heat exposure`, `heat safety`
- `pesticide`, `chemical exposure`, `toxic substance`
- `respiratory illness`, `lung disease`
- `musculoskeletal injury`, `repetitive motion`

**Safety Equipment**:
- `personal protective equipment`, `PPE`, `safety equipment`
- `shade structure`, `cooling station`
- `emergency response`

**Regulations**:
- `Cal/OSHA`, `occupational safety`, `workplace safety`
- `safety standard`, `safety regulation`
- `injury prevention`, `illness prevention`

**Example Bills**:
- SB 1167: Heat illness prevention standards
- AB 2068: Pesticide notification requirements
- SB 616: Workplace safety enforcement

## Category: Union Organizing

**Organizing Rights**:
- `collective bargaining`, `union`, `labor union`
- `right to organize`, `organizing rights`
- `union election`, `union certification`
- `card check`, `majority signup`

**Labor Relations**:
- `ALRA` (Agricultural Labor Relations Act)
- `ALRB` (Agricultural Labor Relations Board)
- `unfair labor practice`, `labor dispute`
- `strike`, `boycott`, `picketing`

**Specific Unions**:
- `UFW` (United Farm Workers)
- `United Farm Workers`
- `Cesar Chavez` (historical context)

**Example Bills**:
- AB 616: ALRA modernization
- SB 104: Union election procedures
- AB 2183: Card check authorization

## Category: Wages

**Compensation**:
- `overtime`, `overtime pay`, `overtime exemption`
- `minimum wage`, `agricultural wage`, `farm wage`
- `piece rate`, `piece-rate`, `hourly wage`
- `wage theft`, `unpaid wages`

**Pay Practices**:
- `payroll deduction`, `wage statement`
- `payment method`, `direct deposit`
- `break time`, `meal period`, `rest period`

**Example Bills**:
- AB 1066: Overtime for agricultural workers
- SB 3: Minimum wage increase
- AB 673: Wage theft penalties

## Category: Immigration

**Visa Programs**:
- `H-2A`, `H2A`, `agricultural visa`
- `guest worker`, `temporary worker`
- `work visa`, `employment visa`

**Immigration Status**:
- `undocumented`, `unauthorized`, `immigration status`
- `IRCA` (Immigration Reform and Control Act)
- `E-Verify`, `I-9`

**Worker Protections**:
- `retaliation`, `immigration retaliation`
- `discrimination`, `national origin`
- `labor contractor`, `farm labor contractor`, `FLC`

**Example Bills**:
- AB 450: Immigration enforcement protections
- SB 1044: H-2A worker protections
- AB 263: Farm labor contractor licensing

## Category: Working Conditions

**Housing**:
- `agricultural housing`, `farm worker housing`, `labor camp`
- `employer-provided housing`, `grower housing`
- `housing code`, `housing standard`
- `dormitory`, `barracks`

**Sanitation**:
- `sanitation`, `bathroom`, `toilet`, `restroom`
- `hand washing`, `handwashing`, `washing station`
- `drinking water`, `potable water`, `water access`
- `field conditions`, `field sanitation`

**Transportation**:
- `agricultural transport`, `crew transport`, `worker transport`
- `vehicle safety`, `passenger safety`

**General Conditions**:
- `working condition`, `work environment`
- `field labor`, `harvest work`

**Example Bills**:
- AB 2334: Field sanitation requirements
- SB 595: Agricultural housing standards
- AB 1783: Worker transportation safety

## Exclusion Patterns

Terms that might trigger false positives:

**Exclude if primary focus is**:
- Agricultural products/commodities (unless labor mentioned)
- Farm subsidies/grants (unless worker benefit)
- Environmental regulations (unless worker exposure)
- Food safety (unless worker safety)
- Agricultural land use (unless worker housing)

**Regex Exclusions**:
- `\bcrop insurance\b` (unless + labor terms)
- `\bwater rights\b` (unless + worker terms)
- `\bsoil conservation\b`
- `\bgmo\b`, `\bgenetically modified\b`

## Subject Tags (LegiScan)

**Include if LegiScan subjects contains**:
- "Agriculture"
- "Labor and Employment"
- "Labor Relations"
- "Occupational Safety and Health"
- "Immigration"
- "Housing"

**Combined subjects** (high confidence):
- "Agriculture" + "Labor and Employment"
- "Agriculture" + "Immigration"
- "Labor and Employment" + "Immigration"

## Keyword Weighting

**High confidence** (strong indicators):
- "farm worker" + "overtime"
- "agricultural" + "heat illness"
- "UFW", "United Farm Workers"
- "ALRA", "ALRB"

**Medium confidence** (need multiple matches):
- "agricultural" + "wage"
- "farm" + "safety"
- "pesticide" + "worker"

**Low confidence** (need context):
- "agriculture" alone
- "labor" alone
- "housing" alone

## Priority Assignment Rules

**High Priority** (landmark legislation):
- 3+ categories matched
- Contains "farm worker" or "agricultural employee"
- UFW or major union mentioned
- Modifies ALRA or major labor law
- Significant policy change (new rights, major enforcement)

**Medium Priority** (incremental improvements):
- 2 categories matched
- Enforcement mechanisms
- Technical improvements to existing law
- Modest benefit expansion

**Low Priority** (minor changes):
- 1 category matched
- Technical amendments
- Clarifications
- Narrow scope

## Testing & Validation

**Known True Positives** (bills that should be tagged):
- AB 5 (2019): Worker classification
- SB 1167 (2016): Heat illness prevention
- AB 1066 (2015): Overtime for ag workers
- AB 2183 (2022): Union card check

**Known False Positives** (bills that should NOT be tagged):
- Agricultural research grants (no labor component)
- Crop insurance programs
- Pesticide use regulations (without worker exposure focus)
- Water rights disputes

**Edge Cases** (requires manual review):
- Bills affecting agricultural contractors/intermediaries
- Immigration bills with agricultural provisions
- Housing bills with farm worker sections
- General labor bills that include agriculture

## Update Process

**Adding New Keywords**:
1. Document rationale in this file
2. Update `agricultural_classifier.py`
3. Test against known bills
4. Run bulk reclassification
5. Review sample of newly tagged bills

**Refining Weights**:
1. Identify false positives/negatives
2. Adjust pattern specificity
3. Update weighting rules
4. Validate against test set

## Historical Context

**Pre-2000s** (not in our dataset):
- ALRA passage (1975)
- UFW grape boycotts (1960s-70s)
- Bracero Program (1942-1964)

**2000s-2010s**:
- Heat illness regulations (2005+)
- Overtime push (multiple attempts)
- Immigration enforcement debates

**2020s**:
- COVID-19 protections
- Climate change (heat safety)
- AB 2183 (card check) - major victory
- Continued enforcement battles

## Sources

- **UFW Legislative Priorities**: https://ufw.org/legislation/
- **California ALRB**: https://www.alrb.ca.gov/
- **Cal/OSHA Standards**: https://www.dir.ca.gov/dosh/
- **California Rural Legal Assistance**: https://www.crla.org/
- **Farmworker Justice**: https://www.farmworkerjustice.org/
