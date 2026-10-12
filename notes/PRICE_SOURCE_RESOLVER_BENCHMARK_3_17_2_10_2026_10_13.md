# Price Source Resolver production benchmark, 2026-10-13

Work: 3.17.2.10, Estimate Ready Material Resolver

Status: production baseline. This is a clean Catalog run after all prior
company-610 sources were removed. It is the comparison baseline for the next
resolver or Israel Reference change.

## Immutable input

- Company: `610`
- Source: `company_610_controlled_kitchen_price_source.xls`
- Source ID: `d1cf160d-2e36-4de3-ba2c-e27e239a076b`
- MIME type: `application/vnd.ms-excel`
- Source SHA-256:
  `20ce4b680a300ff3a4969c23411b92f4d552658f361413216f85d978023726af`
- Template SHA-256:
  `4ac789a55c7a4095059d1493a39fa512389fb9cd3ba2ad243860c36a402152b4`
- Prompt: `price_source_v10_material_unit_defaults`
- Resolver code checkpoint: `7d314c4`, with the XLS bucket correction at
  `026566b`

The source remains a private company-owned artifact. Its immutable Storage
copy and the hash above identify the benchmark. Do not copy it into the Global
catalogue or treat it as public reference evidence.

## Import result

- 44 total source rows
- 40 ready rows: 37 material offers and 3 supplier operations
- 4 excluded rows: 3 consumables and 1 non-candidate
- 0 Review rows
- Source status: `ready`
- Structured-table evidence, 7,514 text characters, no OCR pages

## Resolver baseline

The clean active Company Catalog contains exactly 37 material offers from this
source. Their statuses are:

| Status | Offers | Meaning |
| --- | ---: | --- |
| Green | 18 | Pricing Key, purchase format and Israel canonical link are complete |
| Blue | 19 | Pricing Key and purchase format are complete, Israel canonical link is absent |
| Yellow | 0 | No material is missing a required Pricing Key fact or purchase format |
| Red | 0 | No material lacks family identity |

All 37 offers are Estimate Ready because Blue and Green are eligible for the
deterministic resolver. Blue is a Global Israel Reference coverage gap, not a
reason to exclude the company price.

Green coverage includes MDF, plywood, metal tube, glass, PVC sheet, hinge,
drawer slide, handle, furniture leg, caster and lift mechanism. Blue coverage
includes veneer, edge banding, solid timber, metal sheet and flat bar, acrylic
and plastic sheet, stone and coating families, plus particleboard.

## Comparison rule

Do not compare this baseline against the older `17 Green / 10 Blue / 16
Yellow` snapshot. That snapshot covered 43 catalog offers, including six
pre-existing offers outside this controlled source. It is not a same-input
comparison.

For a later resolver or Israel Reference update, clear company-610 sources,
re-import this exact source hash, then compare the four status counts above.
Any count change must be attributed either to a source-normalization change or
to a documented Israel Reference addition. Green must never fall, Yellow or
Red must not appear, and Blue may become Green only through a proven Israel
canonical link.

## Protected boundaries

- SKU remains evidence only. It does not create a catalog identity, pricing
  key or Israel Reference link.
- Raw supplier wording remains immutable source evidence.
- The benchmark does not make a Blue item Green by assumption.
- Storage acceptance of this legacy XLS relies on
  `db/sql/2026_10_13_company_price_sources_legacy_xls.sql` being applied.

## Deferred acceptance

The Price Source Cancel flow remains an independent production acceptance test
under task 3.17.2.12. The next Material Resolver work should use this baseline
to close Israel Reference coverage deliberately, family by family.
