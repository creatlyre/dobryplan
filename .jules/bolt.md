
## 2024-05-23 - [Precompute Monthly Overview Variables]
**Learning:** In hot loops such as calculating monthly budget overviews, fetching repeated values from a dictionary using `get()` and constantly evaluating defaults within the loop creates measurable processing overhead (especially when multiplied by many users or years).
**Action:** When a loop iterates over fixed bounds (e.g., months 1-12), use a pre-allocated array of corresponding size and pre-compute repetitive math operations. In Python, list indexing combined with ahead-of-time calculations is substantially faster than inline dictionary lookups and conditional default evaluations.
