# Knowledge graph schema

## Node types
`Document`, `Section`, `Table`, `Figure`, `Message`, `DataObject`, `Field`, `State`, `Timer`, `Counter`, `Parameter`, `Signal`, `Role`, `TestCase`, `Check`, `Assertion`, `Requirement`, `VIFField`, `PowerProfile`, `Tech2Phase`, `Tech2Packet`, `Router`, `Adapter`, `Tunnel`.

## Relations
`DEFINED_IN`, `REFERENCES`, `SENT_BY`, `RESPONDS_TO`, `CONTAINS`, `TRANSITIONS_TO`, `STARTS_TIMER`, `STOPS_TIMER`, `HAS_FIELD`, `HAS_VALUE`, `TESTS`, `VERIFIES`, `APPLIES_WHEN`, `TUNNELS`, `SUPERSEDES`, `USES_TIMER`.

Every edge must carry `doc_id`, `revision`, `section`, `page`, `element_id`, `extraction_method`, and `confidence`. The current regex extractor provides candidate triples only. It does not implement full LLM/VLM extraction, schema-constrained relation extraction, stale-reference resolution, or human precision auditing.

## Validation policy
1. Deterministically extract strict identifiers and retain character spans where possible.
2. Generate candidate relations only from local evidence.
3. Validate node types, relation domain/range, provenance and source span.
4. Keep rejected candidates in an audit log; never silently coerce a wrong relation.
5. Resolve aliases conservatively and record merge rationale.
6. Cross-link base-spec entities and test-spec checks by canonical names, but flag revision mismatches.
