# Israel Reference Material Routing

Task: 3.15.1
Market: Israel (`IL`)
Status: estimator-input contract, not yet connected to Estimation Agent v2

## Objective

Resolve each unique material description with the least possible model work.
The agent must never receive or scan the full material or alias catalog.

## Routing order

1. Normalize whitespace and deterministic units in application code.
2. Resolve a confirmed company alias.
3. Query the indexed Israel alias key with a hard maximum of five results.
4. If one exact compatible identity remains, return it without an agent call.
5. On an alias miss, extract only family and technical attributes once for the
   unique source phrase.
6. Query by market, category and hard compatibility attributes. Return no more
   than five candidates.
7. Call the material resolver only when two through five compatible candidates
   remain. Its prompt contains the source phrase, evidence, extracted attributes
   and that shortlist only.
8. Zero candidates means `new_identity_or_needs_review`. More than five before
   the database limit means routing is insufficient and must not be hidden by a
   larger prompt.

## Hard compatibility filters

These are applied before semantic ranking and cannot be overridden by the
agent when explicitly present:

- market;
- material family;
- thickness and dimensional tolerance;
- species, alloy or chemistry;
- grade or moisture/fire class;
- finish and face construction when cost-relevant;
- package form and unit;
- raw, cut-to-size or fabricated price scope.

An unknown attribute does not equal a conflicting attribute. It lowers
confidence and may require review, but it never authorizes a silent substitute.

## Alias layers

- `canonical`: stable English catalog name.
- `technical_code`: exact machine-readable identity.
- `market_name`: Israel-market display or source name.
- `supplier_listing`: exact sourced supplier wording, optionally supplier-bound.
- `synonym`: reviewed recurring wording that is safe across the stated market.

Unit spellings such as `10 mm`, `1 cm` and Hebrew equivalents are normalized by
one deterministic parser. They are not multiplied across every identity.

## Batching and cache

- Deduplicate identical normalized phrases within an estimate before routing.
- Resolve every unique phrase once, then reuse the identity for all occurrences.
- Cache the result by market, company, normalized phrase, supplier context,
  extracted hard attributes and alias-catalog version.
- A confirmed recurring phrase becomes an alias and bypasses the agent later.
- Company aliases remain company-scoped and never become global automatically.

## Price selection after identity resolution

1. Exact compatible company material identity.
2. Active Israel market baseline for the same identity and price scope.
3. Candidate market evidence for review only.

Supplier SKU remains source provenance only. It cannot select an identity,
rank candidates or choose a price.

The resolver selects identity only. It does not choose prices, calculate units,
average retailers or decide whether an incompatible substitute is acceptable.

## Performance acceptance

- Exact confirmed aliases require zero model calls.
- A repeated phrase within the same estimate requires zero additional calls.
- The resolver prompt contains at most five material candidates.
- Candidate retrieval never performs a prompt-time full-catalog scan.
- Every automatic match preserves the source phrase, normalized attributes,
  selected identity, match route and confidence for audit.
