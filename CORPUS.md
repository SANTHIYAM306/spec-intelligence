# Corpus inventory — source files are not bundled

The assignment specifies seven source groups. The exact filenames/revisions below are copied from the assignment brief. The PDFs have not been downloaded, hashed, or parsed into the deliverable, so local hashes, download dates, and measured content counts remain pending.

| # | Source | Revision/date | Main file stated in assignment | Pages stated | Local file / SHA-256 / download date |
|---:|---|---|---|---:|---|
| 1 | USB Power Delivery Specification | R3.2 V1.2, 19 Aug 2026 | `USB_PD_R3.2_V1.2_2026_08_19.pdf` | 418 | Pending |
| 2 | USB Power Delivery Compliance Test Specification | Q3 2026, 31 May 2026 | `USB PD3 CTS Q3 2026 OR.pdf` plus 9 ECNs | 334 | Pending |
| 3 | USB Type-C Cable and Connector Specification | Release 2.5, March 2026 | `USB Type-C Spec R2.5 - March 2026.pdf` | 442 | Pending |
| 4 | USB Type-C Functional Test Specification | Rev 0.91, March 2024 | Single PDF | 140 | Pending |
| 5 | USB Type-C Shared Capacity Charger Interoperability CTS | v1.0, 21 Oct 2025 | Single PDF | 9 | Pending |
| 6 | USB4 Specification | Version 2.0, November 2025; posted 2 Apr 2026 | `USB4 Specification 2.0 November 2025 - CLEAN.pdf` | 839 | Pending |
| 7 | Tech 2 Specification | v2.2.1, 19 June 2025 | All 25 PDFs in the ZIP | ~2,812 | Pending |

## Required local inventory fields

For each actual source file, record exact title/revision/date, filename, SHA-256, page count, download date, approximate table/figure/state-diagram/test-procedure counts, and five difficult pages with a short explanation. Do not infer these values from the assignment's estimates.

## Known parsing traps from the assignment
- Clean specs, redlines and previous revisions overlap; namespace and filter by revision.
- PD/Type-C diagrams may be vector graphics whose text order is fragmented; Tech 2 figures may be raster.
- Table and figure numbering differs by source and some numbering restarts in each Tech 2 book.
- Test IDs vary in syntax, and test specs can cite older base-spec revisions.
- Repeated headers/footers and legal boilerplate pollute retrieval.
- USB4 entry spans PD, Type-C and USB4 documents; link the entities across specifications.

Keep licensed PDFs, extracted text and page images out of public repositories.
