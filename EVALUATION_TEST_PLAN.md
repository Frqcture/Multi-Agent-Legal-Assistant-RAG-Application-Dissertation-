# RAG Pipeline Evaluation Test Plan

## Overview

To rigorously evaluate whether the proposed system meets the safety and accuracy requirements of the legal domain, testing focused on the reliability of the Multi-Agent RAG pipeline. A proprietary evaluation dataset was constructed, comprising **5** synthetic, anonymised client case files and **20** corresponding test queries. These queries were split evenly between fact-retrieval questions and document drafting requests.

The system was evaluated across three primary metrics corresponding to the agent pipeline:

1. **Planner Accuracy**: The percentage of test queries correctly routed to either the Responder or Drafter agent.
2. **Retrieval Success Rate (Top-5)**: The percentage of queries where the critical supporting document chunk was successfully retrieved within the top 5 results by the ChromaDB retriever.
3. **Citation Precision**: A manual review of the generated outputs to determine the percentage of inline citations [document name, page number] that accurately pointed to the correct source text without hallucination.

---

## Evaluation Documents (5 Synthetic Case Files)

Located at: `Backend/TestDocuments/`

| # | Filename | Area of Law | Pages |
|---|----------|-------------|-------|
| 1 | `Thompson_v_Meridian_Construction.pdf` | Construction / Contract | 4 |
| 2 | `Williams_v_Ashford_Logistics_Employment.pdf` | Employment / Unfair Dismissal | 4 |
| 3 | `Chen_Estate_Probate.pdf` | Probate / Wills | 4 |
| 4 | `DataFlow_v_NexGen_IP_Dispute.pdf` | Intellectual Property | 4 |
| 5 | `Patel_Tenancy_Dispute.pdf` | Housing / Tenancy | 4 |

Each document contains precise, verifiable facts (dates, monetary figures, names, legal provisions) providing ground truth for every query.

---

## Test Queries

### Fact-Retrieval Queries (Q1–Q10) — Expected Route: Responder

| ID | Query | Target Document | Page(s) | Ground-Truth Answer |
|----|-------|----------------|---------|---------------------|
| Q1 | "What was the total contract price in the Thompson v Meridian Construction case?" | Thompson_v_Meridian_Construction.pdf | 1 | GBP 187,500 |
| Q2 | "On what date was Sarah Williams dismissed from her position?" | Williams_v_Ashford_Logistics_Employment.pdf | 2 | 17 December 2024, summary dismissal |
| Q3 | "Who are the named beneficiaries in Robert Chen's will?" | Chen_Estate_Probate.pdf | 1–2 | Emily Chen, Daniel Chen, Laura Chen-Morrison; charitable: Macmillan Cancer Support, Royal Orthopaedic Hospital Charitable Fund |
| Q4 | "What is the UK patent number at issue in the DataFlow v NexGen dispute?" | DataFlow_v_NexGen_IP_Dispute.pdf | 1 | GB2587412B, granted 22 September 2021 |
| Q5 | "What is the monthly rent in the Patel tenancy agreement?" | Patel_Tenancy_Dispute.pdf | 1 | GBP 1,150 (increased from GBP 1,050 on 1 August 2023 via s.13 notice) |
| Q6 | "What defects were identified in the Thompson construction project?" | Thompson_v_Meridian_Construction.pdf | 2 | Structural cracking (>5mm), roof defects (improper membrane/falls), drainage non-compliance (gradient 1:120 vs required 1:80), electrical non-compliance (BS 7671), window cavity tray defects |
| Q7 | "How long was Sarah Williams employed before her dismissal?" | Williams_v_Ashford_Logistics_Employment.pdf | 1 | 6 years and 3 months (2 September 2018 – 17 December 2024) |
| Q8 | "What is the total net value of the Chen estate?" | Chen_Estate_Probate.pdf | 2 | GBP 1,762,800 (Gross: GBP 1,835,900 less liabilities of GBP 73,100) |
| Q9 | "What specific trade secrets does DataFlow allege NexGen misappropriated?" | DataFlow_v_NexGen_IP_Dispute.pdf | 1–2 | The Osei-Kapoor Algorithm / StreamCore adaptive partitioning algorithm; Webb had direct access to source code; identical variable naming in 43 instances |
| Q10 | "What repairs were requested by the Patel family?" | Patel_Tenancy_Dispute.pdf | 2 | Damp/mould from defective roof, broken gas boiler (Vaillant ecoTEC Plus), unreliable hot water, rotten sash windows |

### Document Drafting Queries (Q11–Q20) — Expected Route: Drafter

| ID | Query | Target Document Context |
|----|-------|------------------------|
| Q11 | "Draft a letter before action for the Thompson v Meridian construction dispute" | Thompson_v_Meridian_Construction.pdf |
| Q12 | "Draft a witness statement for Sarah Williams' employment tribunal claim" | Williams_v_Ashford_Logistics_Employment.pdf |
| Q13 | "Draft a grant of probate application cover letter for the Chen estate" | Chen_Estate_Probate.pdf |
| Q14 | "Draft a cease and desist letter for the DataFlow v NexGen IP dispute" | DataFlow_v_NexGen_IP_Dispute.pdf |
| Q15 | "Draft a Section 11 disrepair claim letter for the Patel tenancy case" | Patel_Tenancy_Dispute.pdf |
| Q16 | "Draft a settlement proposal letter for the Thompson construction case" | Thompson_v_Meridian_Construction.pdf |
| Q17 | "Draft the grounds of complaint for Sarah Williams' unfair dismissal ET1 form" | Williams_v_Ashford_Logistics_Employment.pdf |
| Q18 | "Draft a beneficiary notification letter for the Chen estate" | Chen_Estate_Probate.pdf |
| Q19 | "Draft a licensing agreement proposal for the DataFlow IP matter" | DataFlow_v_NexGen_IP_Dispute.pdf |
| Q20 | "Draft a tenancy deposit return demand letter for the Patel case" | Patel_Tenancy_Dispute.pdf |

---

## Evaluation Procedure

1. Delete any existing uploaded documents from the system.
2. Upload all 5 PDFs from `Backend/TestDocuments/`.
3. Run each query (Q1–Q20) through the search interface one at a time.
4. For each query, record:
   - The **workflow steps** (planner classification, retriever results, responder/drafter output)
   - The **final answer** with any inline citations
5. Evaluate against the three metrics below.

---

## Metrics Definitions

### 1. Planner Accuracy

| Measure | Definition |
|---------|------------|
| Correct routing | Q1–Q10 routed to **Responder**; Q11–Q20 routed to **Drafter** |
| Formula | (Number of correctly routed queries / 20) × 100% |

### 2. Retrieval Success Rate (Top-5)

| Measure | Definition |
|---------|------------|
| Success | The target document (and ideally the target page) appears in the top 5 retrieved chunks |
| Formula | (Number of queries with target document in top-5 / 20) × 100% |

### 3. Citation Precision

| Measure | Definition |
|---------|------------|
| Correct citation | An inline citation [document_name, page_number] that accurately points to text present on that page of that document |
| Hallucinated citation | A citation referencing a document/page that does not contain the cited claim |
| Formula | (Number of correct citations / Total citations produced) × 100% |

---

## Results

*To be completed after test execution.*

| Metric | Result |
|--------|--------|
| Planner Accuracy | /20 (%) |
| Retrieval Success Rate (Top-5) | /20 (%) |
| Citation Precision | / total citations (%) |
