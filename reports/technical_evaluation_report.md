# Comprehensive Technical Evaluation Report
## LLM Evaluation Framework for Business Document Information Extraction

**Executive Summary:**  
This technical report documents the design, methodology, execution, and findings of an automated LLM evaluation framework developed for enterprise **Document Information Extraction** (Option 4). The benchmark suite evaluates Large Language Models on 55 rigorously engineered real-world business documents spanning digital invoices, thermal receipts, messy OCR scans, cross-border multi-currency statements, missing optional fields, and adversarial prompt injections.

**Key Highlight:** The evaluation was executed using live API inference against **Google Gemini 2.5 Flash (`gemini-2.5-flash`)**, benchmarking its empirical performance against frontier reference and baseline models across all 55 ground-truth test cases.

---

## 1. Domain & Business Application Context
In automated Accounts Payable (AP), invoice processing, and ERP ingestion workflows, extracting structured key-value entities (Vendor, Invoice Number, Issue Date, Due Date, Currency, Line Items, Subtotal, Tax, and Grand Total) directly impacts downstream financial ledgers. Unlike chat or interview evaluation—which suffer from subjective evaluation ambiguity—Document Information Extraction demands **deterministic accuracy**, strict schema compliance, and zero tolerance for hallucination or numeric distortion.

### Evaluation Objectives:
1. **Schema Compliance & Extraction Fidelity**: Validate exact match (EM) and token-level fuzzy similarity against ground truth.
2. **Robustness to Visual / OCR Noise**: Measure degradation caused by OCR letter substitution, broken line wrapping, and punctuation jitter.
3. **Cross-Border Generalization**: Assess parsing of international date formats (ISO, DD/MM/YYYY, DD.MM.YYYY) and foreign currencies (EUR, GBP, JPY, LKR, INR, SGD, CAD, AUD).
4. **Hallucination Resistance**: Quantify LLM tendency to invent absent fields (e.g., fabricating Net-30 payment terms when no due date is stated).
5. **Adversarial Resilience**: Defend against prompt injections embedded inside document comments or decoy account balances.

---

## 2. Benchmark Dataset Architecture (55 Test Cases)
The benchmark comprises **55 hand-curated, ground-truth annotated test cases** divided across 7 functional categories:

| Category Code | Description | Count | Primary Evaluation Focus |
|---|---|---|---|
| `standard_clean` | Cloud SaaS, IT consulting, & enterprise bills | 10 | Baseline accuracy, tabular extraction |
| `ocr_noise` | Scanned, faded thermal receipts, & OCR artifacts | 8 | Character substitution ('O' vs '0'), noise immunity |
| `international_multicurrency` | EUR, GBP, JPY, LKR, INR, SGD, CAD invoices | 8 | Comma decimals, multi-currency, date parsing |
| `missing_optional_fields` | Invoices omitting due date, tax, or subtotal | 8 | Hallucination tracking, null safety |
| `complex_tables` | Multi-item catering, auto parts, raw materials | 8 | Hungarian bipartite matching of line items |
| `informal_receipts` | Coffee shops, gas pumps, rideshare slips | 6 | Terse layouts, implicit vendor structures |
| `adversarial_edge_cases` | Decoy balances, conflicting dates, prompt injections | 7 | Instruction injection resistance, balance isolation |

---

## 3. Quantitative Evaluation Metrics
The framework calculates multi-dimensional quantitative metrics:
- **Exact Match (EM)**: Binary string/numeric equivalence after whitespace trimming.
- **Normalized Semantic Similarity (RapidFuzz)**: Token-sort ratio for entity names and descriptions.
- **Float Tolerance Check**: Absolute error $\le \pm 0.01$ for monetary amounts.
- **Line Item Bipartite Matching**: Precision, Recall, and F1 matching line items via greedy bipartite assignment.
- **Schema Validity Rate**: Percentage of model responses successfully parsed by Pydantic.
- **Hallucination Rate**: Count of non-null extractions when ground truth is `None`.

### Live Model Comparison Matrix (55 Test Cases)

| Performance Metric | Google Gemini 2.5 Flash (Live API) | Frontier Reference LLM | Baseline 7B LLM |
|---|---|---|---|
| **Composite Accuracy** | **99.35%** | **99.53%** | **88.80%** |
| **JSON Schema Validity** | **100.0%** | **100.0%** | **98.2%** |
| **Total Hallucination Events** | **0** | **0** | **13** |
| **Total Flawed Test Cases** | **2** | **3** | **40** |
| **Vendor Name EM** | 98.2% | 98.2% | 76.4% |
| **Invoice Date EM** | 100.0% | 98.2% | 90.9% |
| **Due Date EM** | 100.0% | 100.0% | 76.4% |
| **Total Amount EM** | 100.0% | 98.2% | 76.4% |
| **Line Items F1 Score** | 98.2% | 100.0% | 92.5% |

---

## 4. Category-Wise Accuracy Breakdown

```
Accuracy Comparison by Document Category:

- Adversarial Edge Cases           | Gemini 2.5: 100.0% | Frontier Ref:  98.0% | Baseline 7B:  72.2%
- Complex Tables                   | Gemini 2.5: 100.0% | Frontier Ref: 100.0% | Baseline 7B:  94.8%
- Informal Receipts                | Gemini 2.5:  99.4% | Frontier Ref: 100.0% | Baseline 7B:  90.7%
- International Multicurrency      | Gemini 2.5: 100.0% | Frontier Ref:  98.5% | Baseline 7B:  91.0%
- Missing Optional Fields          | Gemini 2.5:  96.0% | Frontier Ref: 100.0% | Baseline 7B:  92.5%
- Ocr Noise                        | Gemini 2.5: 100.0% | Frontier Ref: 100.0% | Baseline 7B:  77.6%
- Standard Clean                   | Gemini 2.5: 100.0% | Frontier Ref: 100.0% | Baseline 7B:  98.8%
```

---

## 5. Identified Failure Patterns & Empirical Findings

Our automated failure diagnostics categorized empirical errors into recurring failure modes:

### 1. Hallucination on Missing Optional Fields
- **Finding**: In cases where payment terms were absent (`TC_MISS_027` to `TC_MISS_034`), standard models exhibited an inductive bias to fabricate Net-30 dates. Gemini 2.5 demonstrated strong adherence to the negative prompt instructions, setting missing fields to `null`.

### 2. International Decimal Separator Handling
- **Finding**: In European formats (`271,00 €`), models without explicit numeric post-processing risk treating commas as digit groupings. Gemini correctly standardized European comma decimals into standard float types.

### 3. Decoy Amount & Cumulative Balance Isolation
- **Finding**: Adversarial case `TC_ADV_051` (unpaid previous balance of \$1,450 vs current \$428 invoice) tested whether models confuse historical accounts with current liabilities.

### 4. Prompt Injection Resilience
- **Finding**: In adversarial cases `TC_ADV_049` and `TC_ADV_053` (injections inside invoice notes), Gemini 2.5 successfully isolated the untrusted document text without hijacking the schema output.

---

## 6. Business Impact & Production Architecture Recommendations
1. **Tiered LLM Cascade**: Deploy a hybrid routing pipeline. Use Gemini 2.5 Flash for high-throughput, low-latency processing, backed by automated fallback triggers for documents with low OCR confidence.
2. **Deterministic Cross-Field Validation**: Implement post-extraction business rule engines verifying arithmetic consistency (`Subtotal + Tax == Total Amount`) before committing records to ERP general ledgers.
3. **Automated Continuous Regression Testing**: Integrate this 55-case benchmark into CI/CD pipelines to prevent model drift when updating prompts or fine-tuning.

---
*Report generated by the Automated LLM Evaluation Framework.*
