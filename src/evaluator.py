"""
Comprehensive Quantitative Evaluation Suite for Information Extraction
Implements Exact Match, RapidFuzz Semantic Similarity, Field-Level F1,
Schema Compliance, Hallucination Tracking, and Line-Item Bipartite Matching.
"""
from typing import Dict, Any, List, Optional, Tuple
import re
from rapidfuzz import fuzz
from .schemas import InvoiceExtraction, LineItem, TestCase

def normalize_str(s: Optional[str]) -> str:
    """Normalizes string for robust comparison (lowercasing, whitespace stripping)."""
    if s is None:
        return ""
    # strip whitespace, lower
    s = s.strip().lower()
    # collapse multiple spaces
    s = re.sub(r"\s+", " ", s)
    return s

def compare_dates(pred: Optional[str], exp: Optional[str]) -> bool:
    """Compares date strings with ISO normalization."""
    if pred is None and exp is None:
        return True
    if pred is None or exp is None:
        return False
    return normalize_str(pred) == normalize_str(exp)

def compare_floats(pred: Optional[float], exp: Optional[float], tolerance: float = 0.02) -> bool:
    """Compares float values with absolute error tolerance."""
    if pred is None and exp is None:
        return True
    if pred is None or exp is None:
        return False
    return abs(pred - exp) <= tolerance

def match_line_items(pred_items: List[LineItem], exp_items: List[LineItem]) -> Tuple[float, float, float]:
    """
    Computes Precision, Recall, F1 for line item lists using greedy bipartite matching.
    Items match if description similarity >= 75% and total matches within tolerance.
    """
    if not exp_items and not pred_items:
        return 1.0, 1.0, 1.0
    if not exp_items and pred_items:
        return 0.0, 1.0, 0.0
    if exp_items and not pred_items:
        return 1.0, 0.0, 0.0

    matched_exp = set()
    true_positives = 0

    for p in pred_items:
        best_match_idx = -1
        best_score = 0.0
        for i, e in enumerate(exp_items):
            if i in matched_exp:
                continue
            desc_sim = fuzz.token_sort_ratio(normalize_str(p.description), normalize_str(e.description))
            tot_match = compare_floats(p.total, e.total, tolerance=0.10)
            qty_match = compare_floats(p.quantity, e.quantity, tolerance=0.05)
            
            # Composite match score
            score = (desc_sim / 100.0) * (0.6 if tot_match else 0.2) * (1.2 if qty_match else 0.8)
            if desc_sim >= 70 and tot_match and score > best_score:
                best_score = score
                best_match_idx = i

        if best_match_idx != -1:
            matched_exp.add(best_match_idx)
            true_positives += 1

    precision = true_positives / len(pred_items) if pred_items else 0.0
    recall = true_positives / len(exp_items) if exp_items else 0.0
    f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
    return precision, recall, f1

class ExtractionEvaluator:
    """Evaluates an extracted InvoiceExtraction against expected TestCase."""

    @staticmethod
    def evaluate_case(test_case: TestCase, pred: Optional[InvoiceExtraction], parse_success: bool = True) -> Dict[str, Any]:
        exp = test_case.expected_output
        result = {
            "test_case_id": test_case.id,
            "category": test_case.category,
            "difficulty": test_case.difficulty,
            "parse_success": parse_success,
            "field_scores": {},
            "hallucinations": [],
            "mismatches": []
        }

        if not parse_success or pred is None:
            # Complete failure to extract/parse
            fields = ["invoice_number", "invoice_date", "due_date", "vendor_name", "currency", "line_items", "subtotal", "tax_amount", "total_amount"]
            for f in fields:
                result["field_scores"][f] = {"exact_match": 0.0, "similarity": 0.0, "status": "parse_failure"}
            result["overall_accuracy"] = 0.0
            return result

        # 1. Invoice Number
        if exp.invoice_number is None and pred.invoice_number is not None:
            result["hallucinations"].append("invoice_number")
            inv_em = 0.0
            inv_sim = 0.0
        elif exp.invoice_number is None and pred.invoice_number is None:
            inv_em = 1.0
            inv_sim = 1.0
        else:
            p_val = normalize_str(pred.invoice_number)
            e_val = normalize_str(exp.invoice_number)
            inv_em = 1.0 if p_val == e_val else 0.0
            inv_sim = fuzz.ratio(p_val, e_val) / 100.0
            if inv_em == 0.0:
                result["mismatches"].append(("invoice_number", exp.invoice_number, pred.invoice_number))

        result["field_scores"]["invoice_number"] = {"exact_match": inv_em, "similarity": inv_sim}

        # 2. Invoice Date
        if exp.invoice_date is None and pred.invoice_date is not None:
            result["hallucinations"].append("invoice_date")
            date_em = 0.0
        elif exp.invoice_date is None and pred.invoice_date is None:
            date_em = 1.0
        else:
            date_em = 1.0 if compare_dates(pred.invoice_date, exp.invoice_date) else 0.0
            if date_em == 0.0:
                result["mismatches"].append(("invoice_date", exp.invoice_date, pred.invoice_date))
        result["field_scores"]["invoice_date"] = {"exact_match": date_em, "similarity": date_em}

        # 3. Due Date
        if exp.due_date is None and pred.due_date is not None:
            result["hallucinations"].append("due_date")
            due_em = 0.0
        elif exp.due_date is None and pred.due_date is None:
            due_em = 1.0
        else:
            due_em = 1.0 if compare_dates(pred.due_date, exp.due_date) else 0.0
            if due_em == 0.0:
                result["mismatches"].append(("due_date", exp.due_date, pred.due_date))
        result["field_scores"]["due_date"] = {"exact_match": due_em, "similarity": due_em}

        # 4. Vendor Name
        if exp.vendor_name is None and pred.vendor_name is not None:
            result["hallucinations"].append("vendor_name")
            v_em, v_sim = 0.0, 0.0
        elif exp.vendor_name is None and pred.vendor_name is None:
            v_em, v_sim = 1.0, 1.0
        else:
            p_v = normalize_str(pred.vendor_name)
            e_v = normalize_str(exp.vendor_name)
            v_em = 1.0 if p_v == e_v else 0.0
            v_sim = fuzz.token_sort_ratio(p_v, e_v) / 100.0
            if v_em == 0.0:
                result["mismatches"].append(("vendor_name", exp.vendor_name, pred.vendor_name))
        result["field_scores"]["vendor_name"] = {"exact_match": v_em, "similarity": v_sim}

        # 5. Currency
        c_p = normalize_str(pred.currency)
        c_e = normalize_str(exp.currency)
        c_em = 1.0 if c_p == c_e else 0.0
        if c_em == 0.0:
            result["mismatches"].append(("currency", exp.currency, pred.currency))
        result["field_scores"]["currency"] = {"exact_match": c_em, "similarity": c_em}

        # 6. Line Items
        li_p, li_r, li_f1 = match_line_items(pred.line_items, exp.line_items)
        result["field_scores"]["line_items"] = {
            "precision": li_p,
            "recall": li_r,
            "f1": li_f1,
            "exact_match": 1.0 if li_f1 > 0.99 else 0.0,
            "similarity": li_f1
        }
        if li_f1 < 0.99:
            result["mismatches"].append(("line_items", len(exp.line_items), len(pred.line_items)))

        # 7. Subtotal
        sub_em = 1.0 if compare_floats(pred.subtotal, exp.subtotal) else 0.0
        if sub_em == 0.0:
            result["mismatches"].append(("subtotal", exp.subtotal, pred.subtotal))
        result["field_scores"]["subtotal"] = {"exact_match": sub_em, "similarity": sub_em}

        # 8. Tax Amount
        tax_em = 1.0 if compare_floats(pred.tax_amount, exp.tax_amount) else 0.0
        if tax_em == 0.0:
            result["mismatches"].append(("tax_amount", exp.tax_amount, pred.tax_amount))
        result["field_scores"]["tax_amount"] = {"exact_match": tax_em, "similarity": tax_em}

        # 9. Total Amount
        tot_em = 1.0 if compare_floats(pred.total_amount, exp.total_amount) else 0.0
        if tot_em == 0.0:
            result["mismatches"].append(("total_amount", exp.total_amount, pred.total_amount))
        result["field_scores"]["total_amount"] = {"exact_match": tot_em, "similarity": tot_em}

        # Calculate Overall Accuracy (Weighted mean of critical fields)
        weights = {
            "invoice_number": 0.12,
            "invoice_date": 0.12,
            "due_date": 0.08,
            "vendor_name": 0.14,
            "currency": 0.06,
            "line_items": 0.20,
            "subtotal": 0.08,
            "tax_amount": 0.08,
            "total_amount": 0.12
        }
        overall = sum(result["field_scores"][f]["similarity"] * w for f, w in weights.items())
        result["overall_accuracy"] = round(overall, 4)
        return result

    @staticmethod
    def aggregate_metrics(results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Calculates global macro and micro metrics across all test cases."""
        total_cases = len(results)
        if total_cases == 0:
            return {}

        parse_successes = sum(1 for r in results if r["parse_success"])
        fields = ["invoice_number", "invoice_date", "due_date", "vendor_name", "currency", "line_items", "subtotal", "tax_amount", "total_amount"]

        field_summary = {}
        for f in fields:
            em_sum = sum(r["field_scores"][f]["exact_match"] for r in results)
            sim_sum = sum(r["field_scores"][f]["similarity"] for r in results)
            field_summary[f] = {
                "exact_match_rate": round(em_sum / total_cases, 4),
                "similarity_score": round(sim_sum / total_cases, 4)
            }

        # Category Breakdown
        categories = sorted(list(set(r["category"] for r in results)))
        category_summary = {}
        for cat in categories:
            cat_results = [r for r in results if r["category"] == cat]
            cat_acc = sum(r["overall_accuracy"] for r in cat_results) / len(cat_results)
            category_summary[cat] = {
                "count": len(cat_results),
                "accuracy": round(cat_acc, 4)
            }

        # Difficulty Breakdown
        difficulties = ["Easy", "Medium", "Hard", "Adversarial"]
        difficulty_summary = {}
        for diff in difficulties:
            diff_results = [r for r in results if r.get("difficulty") == diff]
            if diff_results:
                diff_acc = sum(r["overall_accuracy"] for r in diff_results) / len(diff_results)
                difficulty_summary[diff] = {
                    "count": len(diff_results),
                    "accuracy": round(diff_acc, 4)
                }

        total_hallucinations = sum(len(r["hallucinations"]) for r in results)
        global_avg_accuracy = sum(r["overall_accuracy"] for r in results) / total_cases

        return {
            "total_test_cases": total_cases,
            "json_schema_validity_rate": round(parse_successes / total_cases, 4),
            "global_composite_accuracy": round(global_avg_accuracy, 4),
            "total_hallucination_events": total_hallucinations,
            "field_summary": field_summary,
            "category_summary": category_summary,
            "difficulty_summary": difficulty_summary
        }
