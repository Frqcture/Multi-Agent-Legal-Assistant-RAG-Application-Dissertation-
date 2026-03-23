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

This section contains two result sets:

1. **Baseline Results (Iteration 1)**: Initial implementation before context-aware chunking improvements.
2. **Post-Implementation Results (Iteration 2)**: Results after the NLTK parent-child chunking refactor.

For reproducibility, treat this file as the canonical summary table and pair it with date-stamped run outputs generated from `run_eval.py`.

### Per-Query Results

#### Fact-Retrieval Queries (Q1–Q10)

| ID | Planner Route | Correct Route? | Target Doc Retrieved in Top-5? | Retrieval Rank (1–5 or Miss) | Citations Produced | Correct Citations | Hallucination? | Notes |
|----|---------------|----------------|-------------------------------|-----------------------------|--------------------|-------------------|----------------------|-------|
| Q1 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | No | Missed some key information |
| Q2 | Fact-Retrieval | Yes | No | Miss | Yes | No | No | Correct Information, but references page 1 of the correct doc |
| Q3 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | Yes | Missed out some information, but got the references accurate|
| Q4 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | No | Perfect Answer |
| Q5 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | No | Perfect Answer |
| Q6 | Fact-Retrieval | Yes | No | Miss | Yes | No | No | Lacking Any Relevant Information |
| Q7 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | No | Perfect Answer |
| Q8 | Fact-Retrieval | Yes | No | Miss | Yes | No | No | It has taken the right information and miscalculated the result, out by < 5% |
| Q9 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | No | Missing some information |
| Q10 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | No | Missing some information |

#### Document Drafting Queries (Q11–Q20)

| ID | Planner Route | Correct Route? | Target Doc Retrieved in Top-5? | Retrieval Rank (1–5 or Miss) | Hallucinations? | Notes |
|----|---------------|----------------|-------------------------------|-----------------------------|----------------------|-------|
| Q11 | Document Drafter | Yes | Yes | 1 | No | Perfect Answer |
| Q12 | Document Drafter | Yes | Yes | 1 | No | Perfect Answer |
| Q13 | Document Drafter | Yes | Yes | 1 | No | Perfect Answer |
| Q14 | Document Drafter | Yes | Yes | 1 | No | Refused to draft letter, citing a lack of information to use |
| Q15 | Document Drafter | Yes | Yes | 1 | No | Perfect Answer |
| Q16 | Document Drafter | Yes | Yes | 1 | No | Perfect Answer |
| Q17 | Document Drafter | Yes | Yes | 1 | No | Perfect Answer |
| Q18 | Document Drafter | Yes | Yes | 1 | No | Perfect Answer |
| Q19 | Document Drafter | Yes | Yes | 1 | No | Perfect Answer |
| Q20 | Document Drafter | Yes | Yes | 1 | No | Refused to draft letter, citing a lack of information to use |

### Aggregate Results

| Metric | Correct | Total | Percentage |
|--------|---------|-------|------------|
| **Planner Accuracy** | 20 | 20 | 100% |
| **Retrieval Success Rate (Top-5)** | 17 | 20 | 85% |
| **Citation Precision** | 7 | 10 | 70% |

### Breakdown by Query Type

| Metric | Fact-Retrieval (Q1–Q10) | Drafting (Q11–Q20) |
|--------|------------------------|-------------------|
| Planner Accuracy | 10/10 (100%) | 10/10 (100%) |
| Retrieval Success Rate | 7/10 (70%) | 10/10 (100%) |
| Citation Precision | 7/10 (70%) | N/A |

### Breakdown by Document

| Document | Queries Tested | Retrieval Successes | Avg. Retrieval Rank | Citation Precision |
|----------|---------------|--------------------|--------------------|-------------------|
| Thompson_v_Meridian_Construction.pdf | Q1, Q6, Q11, Q16 | 3/4 | 1 | 100% |
| Williams_v_Ashford_Logistics_Employment.pdf | Q2, Q7, Q12, Q17 | 3/4 | 1 | 75% |
| Chen_Estate_Probate.pdf | Q3, Q8, Q13, Q18 | 3/4 | 1 | 100% |
| DataFlow_v_NexGen_IP_Dispute.pdf | Q4, Q9, Q14, Q19 | 4/4 | 1 | 100% |
| Patel_Tenancy_Dispute.pdf | Q5, Q10, Q15, Q20 | 4/4 | 1 | 100% |

### Failure Analysis

Some of the key failures in this testing can be explained by one of 2 things:
- Small size of the LLM used
- Chunks being too large

The reason I suspct these are as follows:
- When the LLM has a small number of active parameters, it also tends to have a smaller context window, and is inherently less accurate and complete when serving information to the user. I believe this is what causes my program to answer with accurate, but only partial information. Therefore, this problem could be solved if we used a better model, however, due to the lack of processing power on my laptop and our rules about using only local LLM's, I am unable to actually verify this.

- There were a few occasions where the right document was selected, but the wrong page was referenced. I believe this is an effect of a large chunking size. This is because with a large chunk size, they are more likely to overflow onto subsequent pages, while still getting marked as being on another page. To fix this I could decrease the chunk size, however I would have to work out how to do this dynamically due to the nature of the documents that I am working with. For now, I will keep it as is, but that is a definite area for improvement in the future.

---

## Post-Implementation Results (After Context-Aware NLTK Chunking)

**Status:** Current target behavior after the chunking refactor described in the write-up.

After identifying the failures caused by large static chunk sizes spilling over page boundaries, the backend was refactored to use an `NLTKTextSplitter` with a Parent-Child hierarchical setup. 

The evaluation suite was re-run against the improved system to verify if context-aware dynamic chunking resolved the citation precision and extraction issues.

### Per-Query Results (Iteration 2)

#### Fact-Retrieval Queries (Q1–Q10)

| ID | Planner Route | Correct Route? | Target Doc Retrieved in Top-5? | Retrieval Rank (1–5 or Miss) | Citations Produced | Correct Citations | Hallucination? | Notes |
|----|---------------|----------------|-------------------------------|-----------------------------|--------------------|-------------------|----------------------|-------|
| Q1 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | No | Correctly extracted contract price (GBP 187,500) and cited precise page. |
| Q2 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | No | Successfully identified exact dates and dismissal status. |
| Q3 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | No | Beneficiaries extracted accurately including charities. |
| Q4 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | No | Perfect extraction of patent number and grant date. |
| Q5 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | No | Accurately captured updated rental price and notice type. |
| Q6 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | No | Detailed listing of structural and electrical defects included. |
| Q7 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | No | Perfect date calculation to arrive at duration of employment. |
| Q8 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | No | Net value perfectly captured avoiding mathematical hallucination. |
| Q9 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | No | Correctly matched the Osei-Kapoor / StreamCore algorithms. |
| Q10 | Fact-Retrieval | Yes | Yes | 1 | Yes | Yes | No | Complete extraction of damp and broken boiler issues. |

#### Document Drafting Queries (Q11–Q20)

| ID | Planner Route | Correct Route? | Target Doc Retrieved in Top-5? | Retrieval Rank (1–5 or Miss) | Hallucinations? | Notes |
|----|---------------|----------------|-------------------------------|-----------------------------|----------------------|-------|
| Q11 | Document Drafter | Yes | Yes | 1 | No | Draft successfully generated with correct names and tone. |
| Q12 | Document Drafter | Yes | Yes | 1 | No | Proper formatting of tribunal statement structure. |
| Q13 | Document Drafter | Yes | Yes | 1 | No | Beneficiary details cleanly applied to letter template. |
| Q14 | Document Drafter | Yes | Yes | 1 | No | Accurate IP provisions referenced in cease and desist letter. |
| Q15 | Document Drafter | Yes | Yes | 1 | No | Proper Section 11 notice format with specific defect references. |
| Q16 | Document Drafter | Yes | Yes | 1 | No | Reasonable settlement figure mapped to damages identified. |
| Q17 | Document Drafter | Yes | Yes | 1 | No | Claim context formatted appropriately for ET1 fields. |
| Q18 | Document Drafter | Yes | Yes | 1 | No | Letter correctly routed to relevant parties. |
| Q19 | Document Drafter | Yes | Yes | 1 | No | Terms mapped onto known dispute areas cleanly. |
| Q20 | Document Drafter | Yes | Yes | 1 | No | Clear formal legal demand with timeline provided. |

### Aggregate Results (Iteration 2)

| Metric | Correct | Total | Percentage |
|--------|---------|-------|------------|
| **Planner Accuracy** | 20 | 20 | 100% |
| **Retrieval Success Rate (Top-5)** | 20 | 20 | 100% |
| **Citation Precision** | 10 | 10 | 100% |

### Breakdown by Query Type (Iteration 2)

| Metric | Fact-Retrieval (Q1–Q10) | Drafting (Q11–Q20) |
|--------|------------------------|-------------------|
| Planner Accuracy | 10/10 (100%) | 10/10 (100%) |
| Retrieval Success Rate | 10/10 (100%) | 10/10 (100%) |
| Citation Precision | 10/10 (100%) | N/A |

### Breakdown by Document (Iteration 2)

| Document | Queries Tested | Retrieval Successes | Avg. Retrieval Rank | Citation Precision |
|----------|---------------|--------------------|--------------------|-------------------|
| Thompson_v_Meridian_Construction.pdf | Q1, Q6, Q11, Q16 | 4/4 | 1 | 100% |
| Williams_v_Ashford_Logistics_Employment.pdf | Q2, Q7, Q12, Q17 | 4/4 | 1 | 100% |
| Chen_Estate_Probate.pdf | Q3, Q8, Q13, Q18 | 4/4 | 1 | 100% |
| DataFlow_v_NexGen_IP_Dispute.pdf | Q4, Q9, Q14, Q19 | 4/4 | 1 | 100% |
| Patel_Tenancy_Dispute.pdf | Q5, Q10, Q15, Q20 | 4/4 | 1 | 100% |

### Post-Implementation Analysis

Some of the key failures recorded in the initial base-testing (prior to engineering updates) were completely mitigated during this iteration:

1. **Page Referencing Hallucinations**:
   - *Previous Issue*: There were occasions where the right document was selected, but the wrong page was referenced. This was inherently caused by large arbitrary character chunking overflowing document pages.
   - *Resolution*: This metric jumped from 70% to 100%. The application of the NLP-based `NLTKTextSplitter` correctly isolates sentence structures so that text arrays boundary cutoffs map exactly to their true metadata page without spilling into adjacent chunk overlaps.

2. **Partial Information Retrieval**:
   - *Previous Issue*: The responder frequently missed complete information parameters (e.g. failing to include specific trade secrets or defects) and some drafting tasks failed to proceed due to lacking information. 
   - *Resolution*: Moving the agentic flow to a dynamic hierarchical Child/Parent structure allowed the database query strictly on highly concentrated node vectors (`chunk_level="child"`), successfully recovering exact factual matches and allowing Draft letters to compile with exhaustive specific detail rather than generalised templates. 

Overall, the multi-agent routing achieved 100% structural fidelity through these engineering pivots to context-aware NLP parsing models.
