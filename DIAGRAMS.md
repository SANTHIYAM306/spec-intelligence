# Diagrams

## Architecture

```mermaid
flowchart LR
  PDF[Authorised specification PDFs] --> Parse[Layout/text parser]
  PDF --> Render[Page image renderer]
  Parse --> Elements[Typed JSONL elements]
  Render --> Vision[Optional ColQwen/ColPali page index]
  Elements --> Chunk[Structure-aware chunks]
  Chunk --> BM25[Keyword/BM25 index]
  Chunk --> Dense[Sentence embedding index]
  BM25 --> Fuse[RRF fusion]
  Dense --> Fuse
  Elements --> KG[Candidate knowledge graph]
  Vision --> Fuse
  Fuse --> Agent[Bounded agent tools]
  KG --> Agent
  Agent --> Verify[Citation/evidence checks]
  Verify --> Answer[Cited answer or decline]
```

## Ingestion data-flow

```mermaid
flowchart TD
  A[PDF + SHA-256] --> B[Page and block extraction]
  B --> C[Heading/section heuristic]
  B --> D[Best-effort table extraction]
  B --> E{Selectable text?}
  E -- No --> F[Mark OCR needed]
  E -- Yes --> G[Typed paragraph elements]
  D --> H[JSONL with page and bbox]
  F --> H
  G --> H
```

## Knowledge graph construction

```mermaid
flowchart TD
  A[Typed elements] --> B[Deterministic identifier extraction]
  B --> C[Candidate entity resolution]
  C --> D[Relation candidates]
  D --> E[Schema and provenance validation]
  E --> F[Graph JSON + statistics]
  E --> G[Rejected-edge audit]
```

## Agent sequence

```mermaid
sequenceDiagram
  participant U as Engineer
  participant P as Planner
  participant R as Retrieval tool
  participant G as Graph tool
  participant V as Evidence verifier
  U->>P: Ask question
  P->>R: Search text/hybrid index
  R-->>P: Ranked elements + provenance
  P->>G: Resolve identifier / neighbors
  G-->>P: Candidate graph context
  P->>V: Check citations refer to retrieved elements
  alt evidence sufficient
    V-->>U: Evidence excerpts with citations
  else insufficient evidence
    V-->>U: Honest decline
  end
```

## Ontology ER view

```mermaid
classDiagram
  Document "1" --> "*" Section : contains
  Section "1" --> "*" Element : contains
  Element <|-- Table
  Element <|-- Figure
  Element <|-- Paragraph
  TestCase "*" --> "*" Requirement : verifies
  TestCase "*" --> "*" Timer : checks
  State "*" --> "*" State : transitions_to
  Message "*" --> "*" Timer : uses
  Entity --> Provenance : grounded_by
```

The graph and sequence diagrams describe the intended architecture; the current graph/agent stages are candidate extraction and deterministic workflow, not a complete LLM-based system.
