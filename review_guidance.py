"""Verified applicability and measurement guidance for preliminary reviews."""
import json

EXTRACTION_GUIDANCE = '''
Record exact labels and feet/inches without rewriting digits: 44'-1\" is not 44'-11\".
Distinguish a roof elevation above a datum from a building height above base plane.
Identify base-plane elevation explicitly; grade, curb and floor levels are not
automatically the base plane. For every yard/setback dimension record its start
and end reference: lot line, street line, final map line, building wall, or unknown.
Never equate final map line with lot line or street line without explicit evidence.
Prioritize labeled rear-yard dimensions on the plot plan. Do not replace a labeled
dimension by lot-depth minus building-depth arithmetic. Preserve conflicting
labels as conflicts. Extract dwelling count, building attachment type, lot type,
lot width and use; do not infer these facts from the zoning district alone.
Return the requested JSON. Unknown facts must be null/unknown, not assumptions.
'''

REVIEW_GUIDANCE = '''
Applicability first: classify actual use and building/lot type before choosing a
rule. Residential Use Group II bulk normally uses Article II Chapter 3. Chapter
24 governs community-facility portions, not a residential building merely because
it is in R4. See 24-01, Split 1 p564. A residential and community-facility mixed
building requires the corresponding rules for each portion. Do not apply 24-34's
15-foot front yard to a residential R4 building.
Front yard: 23-321, Split 1 pp452–454, has basic R4 front yard 10 feet (table p453).
Check modifications and verify which reference line legally governs before any
pass/fail. A dimension from final map line is not automatically from the lot line;
report its actual reference and leave compliance unverified if governing lines
cannot be established. Do not call a dimension a violation using the wrong line.
Side yards: 23-332, Split 1 pp455–457. (a) single/two-family detached requires two
yards (R4: 5 feet each). (b) single/two-family semi-detached/zero-lot-line requires
one 5-foot yard and applicable adjoining-building separation. (c), pp456–457,
applies to other residences outside (a)/(b), with no required side yard but
conditions for provided open areas (5 feet) and applicable adjoining separation
(8 feet). For attached residences examine (c), not assumed 23-333 eligibility.
Qualifying residential site is a distinct 12-10 definition, Split 1 pp212–214.
The ordinary R1–R5 route requires at least 5,000 sf plus other criteria. There are
alternative routes; do not reject them solely on area or assume any applies.
Only apply 23-333 (pp457–458) after qualification is demonstrated. A 2,000 sf
ordinary residential lot does not meet the 5,000 sf route. Read full conditions.
Rear yard: 23-342, pp464–465. Standard interior lots: (a)(1) detached/zero-lot-line
20 feet at/below 75 feet above base plane, 30 feet above. (a)(2)(i) semi-detached/
attached on lots LESS THAN 40 feet wide: 30 feet (p465). (a)(2)(ii) width 40 feet
or greater: 20 feet at/below 75 feet, 30 above. Confirm applicability and exceptions.
Use the labeled rear yard with its sheet reference and endpoints. Do not derive
a replacement from lot depth/building depth when the yard is already labeled.
If no label exists, a derived value requires verified compatible reference lines
and all intervening offsets; mark derived, never explicitly labeled.
Height: 23-42, Split 1 p498, measures height from base plane. Roof datum elevation
alone cannot support a height pass. Use labeled base-plane-to-roof height, or
subtract VERIFIED base-plane elevation from roof elevation on the SAME datum,
and apply the rule's required measurement point. Missing datum/base plane =>
insufficient information. Do not mix heights and elevations or silently resolve
conflicting roof labels. 23-421 pp498–504 covers applicable pitched-roof envelopes;
23-422 pp505–506 covers applicable flat-roof envelopes. Select by building type
and actual rule scope, not roof appearance alone. The 35/45 table on p508 is
23-424 (qualifying residential sites; begins p507), NOT 23-631 and NOT a universal
R4 allowance. Confirm qualification before using it. Other exceptions need evidence.
Every finding must identify: applicable section/subparagraph and PDF part/page,
why it applies, exact labeled measurement and its reference lines/datum, and
conditions still unverified. Do not give a preliminary pass based on an assumption
about building type, qualification, datum or governing measurement line.
'''

def extraction_format():
    nullable_text = {'type': ['string', 'null']}
    properties = {
        'notes': {'type': 'string'},
        'building_type': {'type': 'string', 'enum': ['detached', 'semi_detached', 'zero_lot_line', 'attached', 'other', 'unknown']},
        'dwelling_units': {'type': ['integer', 'null']},
        'lot_type': {'type': 'string', 'enum': ['interior', 'corner', 'through', 'unknown']},
        'lot_width_feet': {'type': ['number', 'null']},
        'use_as_drawn': nullable_text,
        'measurements': {'type': 'array', 'items': {'type': 'object',
            'properties': {'kind': {'type': 'string', 'enum': ['roof_elevation', 'base_plane_elevation', 'building_height', 'front_yard', 'rear_yard', 'side_yard', 'other']},
                'label_as_drawn': {'type': 'string'}, 'from_reference': nullable_text,
                'to_reference': nullable_text, 'datum': nullable_text,
                'sheet_page': {'type': 'string'}, 'uncertainty': nullable_text},
            'required': ['kind', 'label_as_drawn', 'from_reference', 'to_reference', 'datum', 'sheet_page', 'uncertainty'],
            'additionalProperties': False}}
    }
    return {'type': 'json_schema', 'name': 'drawing_evidence', 'strict': True,
            'schema': {'type': 'object', 'properties': properties,
                       'required': list(properties), 'additionalProperties': False}}


def validate_evidence(text):
    evidence = json.loads(text)
    if not isinstance(evidence, dict) or not isinstance(evidence.get('measurements'), list):
        raise ValueError('Missing measurement evidence')
    return evidence
