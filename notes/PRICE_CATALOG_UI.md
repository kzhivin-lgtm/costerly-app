# Price Catalog UI

Task: 3.10.1
Status: active

## Product boundary

Price Lists is a continuously enriched company catalog. Its primary row is an
active supplier offer for one normalized material, not an uploaded document and
not a supplier summary. Source documents remain private provenance and are kept
in a source library.

User-facing departments are `Wood`, `Metal`, and `Finishing`. Their stable codes
are `wood`, `metal`, and `finishing`. `Finishing` is intentionally broader than
paint because it also covers coatings and surface treatments.

## Catalog contract

- Rows are grouped by department and then material type. Both levels can be
  collapsed.
- A row shows canonical material name, original source description, supplier,
  truncated supplier/source URL when available, normalized price and unit,
  last price date, and an opaque source reference.
- ILS prices use the shekel sign and grouped thousands. A non-ILS source must
  retain its actual currency until a verified conversion exists. The UI must
  never relabel an unconverted foreign price as ILS.
- The same normalized material from another supplier creates another row.
- A later ready price for the same material and supplier supersedes the active
  offer while preserving history.
- Ambiguous matches, missing prices, or missing units stay unresolved and never
  enter the active catalog.
- Source names and URLs are visually truncated without changing their stored
  values.

## Scenario matrix

| Scenario | Expected behavior |
| --- | --- |
| No sources or prices | Show a compact empty state and `Add price source` |
| One supported file or public URL | Process it and retain the original source |
| Several photos form one document | Treat the photos as one ordered source, not independent invoices |
| Source is processing | Keep it visible in the source library with `Processing` state |
| New ready material | Add an active catalog row |
| Same material and same supplier | Replace the active price and preserve the prior offer in history |
| Same material and different supplier | Add a separate supplier row |
| Duplicate source bytes | Do not silently create duplicate catalog rows |
| Match is uncertain | Keep it in `Needs review`; do not activate its price |
| Processing fails or times out | Preserve an actionable failed source with retry support |
| Long source name or URL | Truncate visually and expose the complete value accessibly |
| Many prices | Allow search and department, type, and supplier filtering |
| Mobile | Preserve readable cards/rows without clipped values or page overflow |

## Source formats

Target formats are PDF, XLSX, XLS, CSV, JPEG, PNG, HEIC, HEIF, and public URL.
The first UI revision must not claim a format is accepted until its complete
upload and extraction path is implemented. Multi-photo upload belongs to one
source operation and is verified separately from the extraction-agent prompt.

## Deferred UI follow-up

- Machinery production checkboxes still render red despite the attempted blue
  override. Do not continue patching that issue without fresh DOM evidence.
- Move `Available in-house?` slightly right so its first letter aligns with the
  availability buttons.
