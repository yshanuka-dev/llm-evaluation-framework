# LLM Evaluation Framework for Document Information Extraction

An end-to-end evaluation suite designed to benchmark Large Language Models on real-world business document extraction (invoices, receipts, billing statements, purchase orders).

Built to satisfy all requirements of the assignment:
- **Application**: Option 4: Document Information Extraction
- **Dataset**: 55 comprehensively designed benchmark test cases spanning 7 real-world categories
- **Expected Outputs**: Ground-truth annotated structured schemas (Pydantic models)
- **Quantitative Metrics**: Exact Match (EM), RapidFuzz token similarity, Hungarian bipartite line item F1, JSON schema validity rate, and hallucination tracking
- **Failure Analysis**: Automated diagnostic classification of empirical failure patterns (missing field hallucinations, comma decimal errors, OCR noise, decoy values, prompt injections)
- **Technical Report**: Comprehensive executive and engineering report with analytics charts

---

## Project Structure

```
├── data/
│   ├── test_cases.json             # 55 ground-truth annotated benchmark test cases
│   └── evaluation_results.json     # Detailed metric dumps across evaluated LLM tiers
├── reports/
│   ├── technical_evaluation_report.md  # Final comprehensive technical report
│   ├── accuracy_by_category.png        # Bar chart comparing accuracy across 7 categories
│   └── failure_patterns.png            # Horizontal bar chart of empirical failure patterns
├── src/
│   ├── __init__.py
│   ├── schemas.py                  # Pydantic schemas for extracted data and test cases
│   ├── dataset.py                  # 55 test cases across 7 categories & 4 difficulty levels
│   ├── extractor.py                # LLM extraction engine (Frontier, Mid-tier, Baseline, or Live API)
│   ├── evaluator.py                # Quantitative evaluation metrics suite
│   ├── failure_analyzer.py         # Failure pattern taxonomy and diagnostic engine
│   └── visualizer.py               # Plotting and markdown matrix generation
├── tests/
│   └── test_evaluator.py           # Pytest unit tests for evaluation logic
├── main.py                         # Single-command CLI runner for benchmark
├── pytest.ini                      # Pytest configuration
└── assignment.txt                  # Original task specification
```

---

## 55 Test Cases Across 7 Categories

| Category | Count | Focus Area |
|---|---|---|
| `standard_clean` | 10 | Clean digital SaaS, IT consulting, & cloud invoices |
| `ocr_noise` | 8 | Thermal receipts, letter substitutions ('O' for '0'), noisy scans |
| `international_multicurrency` | 8 | EUR (comma decimals), GBP, JPY, LKR, INR, SGD, CAD |
| `missing_optional_fields` | 8 | Testing hallucination resistance when due dates/tax are absent |
| `complex_tables` | 8 | Multi-item catering, auto parts, raw material unit rates |
| `informal_receipts` | 6 | Coffee shop receipts, fuel pumps, supermarket slips |
| `adversarial_edge_cases` | 7 | Conflicting dates, decoy balances, prompt injection attempts |

---

## Quickstart

### 1. Run Unit Tests
```bash
pytest tests/
```

### 2. Run the Full Evaluation Benchmark
```bash
python main.py
```

### 3. Run with a Specific Model or Live API
```bash
# Evaluate mid-tier model only
python main.py --models mid_tier_llm

# Evaluate with live Gemini API (if GEMINI_API_KEY is exported)
python main.py --models live_gemini
```
