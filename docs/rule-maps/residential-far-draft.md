# Residential FAR decision map — draft 1

Status: review draft, not installed in the app's decision engine. This document
does not change deployed behavior and is not an exhaustive mapping of NYC FAR.

Source: user-supplied NYC Zoning Resolution export generated September 21, 2026.
All page references below are **Split 1 PDF page numbers**, not printed section
page numbers. Sections 23-20 through 23-24 and the mapped optional provisions
show last amended December 5, 2024. Definitions may have other amendment dates.
The R6–R12 table rows and footnotes were visually checked on PDF pages 438–439.
The R1–R5 rows were previously visually checked on page 437.

## 1. Scope and required evidence

Initial scope: residential floor area in Residence Districts R1–R12, using the
underlying Chapter 23 provisions. Residential components in Commercial or
Manufacturing Districts, mixed buildings, special districts and exceptional
approvals must be routed for additional rules; this draft does not resolve their
complete allowable FAR.

Every fact has a value, evidence reference and status: verified, user-stated,
conflicting or unknown. A model inference is not verified eligibility.

Required facts:

- Exact district, including suffix; mapped boundaries crossing the zoning lot.
- Residential use and other uses on the zoning lot; all buildings and retained
  existing floor area, not only the proposed addition.
- Verified zoning-lot boundaries and area; tax-lot identity alone is insufficient.
- Work type, relevant application/approval dates and existing lawful conditions.
- Floor-by-floor gross areas, claimed exclusions and the resulting zoning floor
  area schedule, with drawing sheet references.
- Special districts/subdistricts, overlays, applicable approvals and floor-area
  transfers or zoning-lot mergers.
- Facts supporting any claimed qualifying site, affordable/senior housing status,
  bonus, optional provision or geographic modification.

## 2. Decision sequence

| ID | Condition / question | Source to retrieve | Action |
|---|---|---|---|
| FAR-01 | Is the use residential, and is this an underlying Residence District review? | §23-20, p436; governing use/district applicability provisions | If not, route to the appropriate commercial/manufacturing/mixed-use rules. Unclear use or district → unresolved. |
| FAR-02 | What is the actual zoning lot and its area? | §12-10, definitions “lot area,” p169, and “zoning lot,” pp295–299 | Establish the denominator from zoning-lot evidence. Read the complete zoning-lot definition, including continuation pages. Do not equate it automatically to a tax lot. |
| FAR-03 | What counts as floor area? | §12-10, “floor area,” pp138–144 | Reconcile gross area with inclusions/exclusions. Retrieve and cite each claimed exclusion's actual paragraph and conditions. Unknown exclusion → unresolved amount, not zero. |
| FAR-04 | How is FAR calculated for all buildings on the lot? | §12-10, “floor area ratio,” p145 | Sum applicable zoning floor area across all buildings, then divide by zoning-lot area. |
| FAR-05 | Are there multiple uses or differing residential FAR regimes? | §23-20, p436 | Evaluate each component and shared floor-area allocation. Do not add independent maximum FARs. Route for other chapter/mixed-use rules where applicable. |
| FAR-06 | Is the district R1–R5? | §23-21, pp436–437 | Use the exact district row and verified standard/qualifying-site status; see branch A. |
| FAR-07 | Is the district R6–R12? | §23-22, pp438–439 | Select standard or qualifying affordable/senior housing row and apply table footnotes; see branch B. |
| FAR-08 | Is this a multiple-dwelling residence claiming special exemptions? | §23-23 and §§23-231–234, pp439–443 | Check building/work-date applicability before evaluating amenity, corridor, refuse and elevated-entry exemptions; see branch C. |
| FAR-09 | Does a mapped geographic/special provision apply? | §§23-24, 23-71, 23-72 and actual special-district provisions | Screen branch D. A district match alone is not eligibility. Unknown geography or approvals blocks a final allowance determination. |
| FAR-10 | Are all applicable constraints and exclusions reconciled? | All selected sources above | Calculate allowance and proposal; issue a finding with coverage and unresolved gates, not a general zoning-compliance conclusion. |

## 3. Branch A — R1 through R5

§23-21 table, p437 (heading begins p436):

| Exact districts | Standard zoning lot FAR | Qualifying residential site FAR |
|---|---:|---:|
| R1-2A, R1-1, R1-2, R2A, R2, R3A, R3X, R3-1, R3-2 | 0.75¹ | 1.00 |
| R2X | 1.00 | 1.00 |
| R4A, R4B, R4, R4-1 | 1.00 | 1.50 |
| R5A, R5B, R5 | 1.50 | 2.00 |
| R5D | 2.00 | 2.00 |

¹ Only for the first table row's standard lots of **4,000 sf or more**: residential
floor area associated with any single dwelling unit must not exceed an equivalent
FAR of **0.60**. This is an additional per-dwelling limit, not a blanket change of
the whole lot's FAR to 0.60, and not an R4 footnote.

### Qualifying residential site eligibility

Retrieve §12-10, “qualifying residential site,” pp212–214. The branches are
alternatives; criteria within a branch must all be satisfied as written.

| Definition branch | Conditions to establish | Pages |
|---|---|---|
| (a)(1)(i)–(iv) | At least 5,000 sf; Greater Transit Zone; wide-street frontage or frontage along the short dimension of a block; not R1/R2. Observe the definition's December 5, 2024 station/geography limitation and §66-11 cross-reference. | 212 |
| (a)(2) | Greater Transit Zone and an existing building with community-facility floor space as of December 5, 2024. Do not add a 5,000 sf condition absent from this branch. | 212 |
| (a)(3) | Outside Greater Transit Zone, at least 5,000 sf, and the specified existing community-facility floor space as of December 5, 2024. | 213 |
| (a)(4) | R3-2, unsuffixed R4, R5 or R5B, and qualifying senior housing. Read the housing definition and dependencies. | 213 |
| (b)(1)(i)–(ii), (b)(2) | C1/C2/C4 mapped within or equivalent to R1–R5; detailed commercial-frontage/existing-residence conditions or the alternate paragraph (a) route. | 213–214 |
| (c) | M1 paired with R1–R5. Route to paired-district rules; do not use an R district table alone as a complete determination. | 214 |

The definition also imposes an affordability restriction where permitted
residential floor area exceeds **50,000 sf** when using §23-21 qualifying-site FAR.
Read the final paragraph on p214 and its §27-111/HPD dependencies; do not treat the
site definition as only a yes/no area test.

For a 2,000 sf ordinary R4 residential lot, (a)(1) fails its area condition.
That does not establish that every other route fails. The standard **1.00** is a
baseline candidate; any claimed higher allowance needs its own evidence.

## 4. Branch B — R6 through R12

§23-22, pp438–439. The enhanced column is for **qualifying affordable housing or
qualifying senior housing**, not the R1–R5 “qualifying residential site” test.
Retrieve §12-10 definitions: qualifying affordable housing, pp209–210, and
qualifying senior housing, p215; follow their referenced definitions/program rules.

| Exact districts / location condition | Standard residences | Qualifying affordable/senior housing |
|---|---:|---:|
| R6A, R6-1, R7B; R6 within the footnote 1 area | 3.00 | 3.90 |
| Other R6 | 2.20 | 3.90 |
| R6B | 2.00 | 2.40 |
| R6D, R6-2 | 2.50 | 3.00 |
| R7A; R7-1/R7-2 within the footnote 1 area | 4.00 | 5.01 |
| Other R7-1, R7-2 | 3.44 | 5.01 |
| R7D | 4.66 | 5.60 |
| R7X, R7-3 | 5.00 | 6.00 |
| R8A, R8X, R8 (base row) | 6.02 | 7.20 |
| R8 conditional row | 7.20¹ | 8.64² |
| R8B | 4.00 | 4.80 |
| R9A, R9 | 7.52 | 9.02 |
| R9D, R9X, R9-1 | 9.00 | 10.80 |
| R10A, R10X, R10 | 10.00 | 12.00 |
| R11 | 12.00 | 15.00 |
| R12 | 15.00 | 18.00 |

Footnote 1 (p439): zoning lots, **or portions thereof**, within 100 feet of a
wide street. Do not apply the higher value across the entire lot automatically.

Footnote 2 (p439): **outside Mandatory Inclusionary Housing areas**, zoning lots
or portions within 100 feet of a wide street, containing UAP developments or
qualifying senior housing. Do not apply R8 8.64 merely because any affordable
housing is claimed. MIH/UAP eligibility and area boundaries must be established.
The general MIH-area definition is on p176 and refers to §27-111; maps/program
requirements need separate verification.

For portions with different applicable FARs, establish their areas and the
governing allocation rules before calculating an allowance. A single multiplier
for the whole lot is not automatically supported.

## 5. Branch C — floor-area accounting and multiple-dwelling exemptions

Base accounting is §12-10 “floor area,” pp138–144. Do not classify a room as
excluded solely from its label; test the actual definition paragraph, use,
dimensions and conditions. Existing retained floor area must remain accounted for.

§23-23, pp439–440, governs multiple-dwelling residences and the applicability of
these special exemptions. It allows the specified provisions for buildings
developed after December 5, 2024, and for qualifying newly created/altered floor
space in existing buildings after that date. Exempted space still counts for the
specified other ground-floor use regulations. Verify definitions and exact scope.

| Claimed space | Rule to retrieve | Conditions / evidence to check | Pages |
|---|---|---|---|
| Residential amenities | §23-231 | Eligible amenity use, resident access, cap of 5% of residential floor area; circulation is not amenity space. Verify calculation denominator. | 440–441 |
| Corridors: termination | §23-232(a)(1)–(3) | The stated outdoor-access, daylighting or three-bedroom-unit termination criterion; 50% exemption only where supported. | 441–442 |
| Corridors: length | §23-232(b) | Length from the defined vertical circulation core to furthest dwelling-unit door ≤100 linear feet; 50% exemption. Individual/combined application must not double-count the same space. | 442 |
| Refuse storage/disposal | §23-233 | Actual eligible space and cap of 3 sf per dwelling unit. | 442 |
| Elevated ground-floor entry | §23-234 | Curb-level entryway and qualifying ramps/stairs/lifts; 100 sf per foot of elevation difference, capped at 500 sf per building. Verify relevant levels. | 443 |

These are **accounting exemptions, not additional FAR bonuses**. A one-/two-family
project must not be treated as eligible solely because there are multiple units;
verify the defined multiple-dwelling category first.

## 6. Branch D — modification screens

| Trigger | Rule to retrieve | Required checks | Pages |
|---|---|---|---|
| R9/R10 tower under applicable tower regulations | §23-241; §23-435; §12-10 floor-area paragraphs (8) and (k) | Certain mechanical/unused/inaccessible space must be counted under the tower rule; verify all location, predominant-story and height conditions. | 443–444 for §23-241 |
| R1–R3 south of Avenue H in Brooklyn CDs 11, 14 or 15 | §23-242(a) | Verify exact geography; standard lot FAR increases to 1.0 under this provision. | 444–445 |
| Claimed predominantly built-up route in unsuffixed R4/R5 | §23-711(a), (b)(1)–(3), (c); then §23-712 | Lot ≤1.5 acres; block district/location and ≤4-acre area; building coverage ≥50% of block area; historical opposing-frontage test as of October 21, 1987; acceptable occupancy evidence. If established: R4 1.35 / R5 1.65. Do not select the highest number before qualification. | 541–542 |
| R5/R6 in the specified Brooklyn CD12 area | §23-721; §23-722 | Exact boundaries, unsuffixed district and exclusively single-/two-/three-family residences. §23-722 provides R5 1.65 for corner lots and 1.80 for interior/through lots; it does not state an R6 FAR modification. | 543–544 |
| Existing bonused public amenity being removed/changed | §23-243(a)–(c) and cross-references | Determine certification/authorization/special-permit obligations; no automatic fresh FAR bonus. | 445–446 |
| Special district/subdistrict, approved bonus/transfer, zoning lot split by district boundary, existing noncomplying building, variance or other approval | Actual controlling provisions/approval documents | Mandatory escalation gate. Exact section mapping remains project-specific and is not completed in this draft. Unknown → unresolved, never “no special rules.” | To be identified from mapped facts |

Optional regimes may carry linked height, yard or other obligations. Selecting a
FAR modification does not establish those checks or allow automatic stacking with
another allowance. Read complete provisions and their interaction rules.

## 7. Calculation and finding contract

For a simple, verified single-regime residential lot:

1. Zoning floor area = counted floor areas across all relevant buildings, less
   individually justified exclusions; avoid duplicated exemptions.
2. Proposed FAR = proposed total zoning floor area / verified zoning-lot area.
3. Maximum residential floor area = applicable FAR × verified zoning-lot area.
4. Compare existing/proposed/retained totals with the allowance. Where portions,
   uses or regimes differ, use the governing allocation rules instead of the
   simple whole-lot formula.

Each finding must record the exact section/subparagraph, source part/pages,
eligibility facts/evidence, selected table row, amendments/date screen, arithmetic,
exclusion schedule, modification screens and remaining dependencies.

Outcomes: preliminary pass, potential issue, not applicable with reason, unresolved.
A base FAR can be identified while final allowable FAR remains unresolved. Do not
announce final compliance with unknown modifying rules or unexplained exclusions.

## 8. Acceptance examples for implementation

| Facts | Expected decision |
|---|---|
| Verified standard R4, 2,000 sf lot, 2,000 sf correctly accounted residential ZFA; all modification screens resolved | §23-21 base 1.00; allowance 2,000 sf; FAR 1.00. Never select 0.75. |
| Same R4 lot, qualifying-site status unknown | Show base candidate 1.00; do not use 1.50 or assert universal failure of all qualifying routes. Record unresolved claimed enhancements separately. |
| Standard first-row §23-21 district, lot 4,000 sf | Check overall 0.75 and additional per-dwelling 0.60 footnote; do not impose that footnote on R4. |
| R4 predominantly-built-up FAR requested without historical/block evidence | 1.35 route unresolved; no automatic enhancement. |
| Standard R6, wide-street proximity unknown | Distinguish 2.20 base and possible 3.00 portion allowance; final allowance unresolved. |
| R8 enhanced FAR requested, MIH/UAP/senior qualification or 100-foot area unverified | Do not select 8.64 automatically. Resolve footnote 2 and housing definitions. |
| Two-family project claims amenity exemption under §23-231 | Check §23-23/defined multiple-dwelling applicability before allowing exemption. |
| Claimed cellar, mechanical or other exclusion lacks definition evidence | Keep accounting unresolved; do not accept a printed ZFA total as proof. |
| Residential building plus community-facility use | Route through §23-20 and applicable component/mixed-building rules; do not sum separate maximum FARs. |

## 9. Coverage still to be mapped

- Every §12-10 floor-area inclusion/exclusion and its definitions/dependencies.
- Full affordable/senior housing, MIH/UAP and transit-geography eligibility trees.
- Commercial/manufacturing residential equivalents and mixed-building provisions.
- District-boundary allocation, special districts, floor-area transfers/bonuses,
  existing noncompliance, approval and transition provisions.

This draft identifies these as mandatory gates; it does not claim they are solved.
