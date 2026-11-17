# Data directory

- `synthetic_demo.jsonl` is invented fixture data used for tests and demos. It is not real USB/Type-C/USB4/Tech 2 content.
- `gold_questions_template.json` contains the 25 seed questions from Appendix A of the assignment. It intentionally has no gold answers or evidence IDs because those must be verified against the licensed source PDFs. Fill author, gold answer, evidence, verifier and status only after checking the source page.
- `gold_set_template.json` is a small schema example, not an evaluated gold set.
- Put processed licensed documents and extracted content under ignored local paths such as `data/processed/`; do not commit them.
