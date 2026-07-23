# Vision-extract the scanned Appendix B, and flag it as a control weakness

Appendix B of the FY2023 Board Paper is a scanned image with no extractable text. It
carries material content: the permanent NZ GM appointment (Mr. James O'Connor, effective
1 Jan 2023, "no further changes anticipated") that the FY2024 paper later contradicts
("3 GM changes in 18 months"), and a customer-concentration figure (~one third of NZ
FY2022 channel revenue via a single reseller, Security Tech Inc.).

Decision — do both:

1. **Extract** the appendix at ingest by passing the image to **Claude vision**, then feed
   the resulting text into the same narrative pipeline as the other papers. This
   strengthens the leadership-contradiction finding and demonstrates multimodal ingestion,
   which is on-theme with the brief's "scale to more unstructured data."
2. **Flag** the process weakness as diligence output: material board content delivered as
   a non-searchable scan, and a concentration figure that the P&L cannot verify — request
   machine-readable source and customer-level revenue.

We extract via Claude vision rather than a local OCR engine (tesseract) to avoid an extra
system dependency and keep the stack to one provider; the enterprise-scaling slide notes a
dedicated document-AI/OCR service as the production path. Considered and rejected:
flag-only (throws away real signal sitting in the document).
