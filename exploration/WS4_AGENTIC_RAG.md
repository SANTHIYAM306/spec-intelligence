# WS4 exploration — agentic RAG

## Question
How can the system answer multi-hop engineering questions while refusing unsupported claims?

## Candidates
- Single-pass retrieval-augmented answer: simpler, but can miss linked requirements.
- ReAct/tool loop: flexible, but may make unnecessary calls.
- Plan-and-execute with reflection: clearer budgets and trace; suitable for this local CLI.
- LangGraph is an optional future framework; plain Python is currently used to keep the baseline auditable.

## Current implementation
`agent.py` plans question categories, calls retrieval and graph helpers, records a trace and verifies that cited evidence elements came from retrieved results. `answer.py` returns evidence excerpts or declines.

## Limitations
The verifier checks citation membership, not semantic entailment. The current answer layer does not use a local LLM for synthesis. A stronger implementation must verify every claim against page/region evidence, support tool timeouts and token budgets, and re-plan when evidence is insufficient.
