"""
Failure Pattern Identification and Root Cause Diagnostic Engine
Categorizes discrepancies into standard business and technical LLM failure modes.
"""
from typing import Dict, Any, List
from collections import defaultdict
from .schemas import TestCase

class FailureAnalyzer:
    """Analyzes extraction evaluations to classify failure patterns."""

    @staticmethod
    def classify_failures(test_cases: List[TestCase], results: List[Dict[str, Any]]) -> Dict[str, Any]:
        tc_dict = {tc.id: tc for tc in test_cases}
        
        failure_counts = defaultdict(int)
        case_diagnostics = []

        for res in results:
            tc_id = res["test_case_id"]
            tc = tc_dict.get(tc_id)
            if not tc:
                continue

            patterns_found = []

            # 1. Schema or parse failure
            if not res["parse_success"]:
                failure_counts["JSON_SYNTAX_OR_SCHEMA_VIOLATION"] += 1
                patterns_found.append({
                    "pattern": "JSON_SYNTAX_OR_SCHEMA_VIOLATION",
                    "severity": "CRITICAL",
                    "explanation": "LLM output could not be parsed as valid JSON or violated Pydantic schema."
                })

            # 2. Hallucinations
            if res.get("hallucinations"):
                for field in res["hallucinations"]:
                    pattern_name = f"HALLUCINATED_ABSENT_FIELD_{field.upper()}"
                    failure_counts[pattern_name] += 1
                    patterns_found.append({
                        "pattern": pattern_name,
                        "severity": "HIGH",
                        "explanation": f"LLM fabricated a non-null value for '{field}' when none existed in the source document."
                    })

            # 3. Mismatch classifications
            for field, exp_val, pred_val in res.get("mismatches", []):
                # Date normalization failure
                if field in ["invoice_date", "due_date"]:
                    failure_counts["DATE_NORMALIZATION_FAILURE"] += 1
                    patterns_found.append({
                        "pattern": "DATE_NORMALIZATION_FAILURE",
                        "severity": "MEDIUM",
                        "explanation": f"Date mismatch on {field}: expected '{exp_val}' (ISO), got '{pred_val}'."
                    })

                # Decoy confusion or calculation error
                elif field in ["total_amount", "subtotal"]:
                    if tc.category == "adversarial_edge_cases":
                        failure_counts["DECOY_VALUE_CONFUSION"] += 1
                        patterns_found.append({
                            "pattern": "DECOY_VALUE_CONFUSION",
                            "severity": "HIGH",
                            "explanation": f"Adversarial decoy: model extracted '{pred_val}' instead of ground truth '{exp_val}'."
                        })
                    elif tc.category == "international_multicurrency":
                        failure_counts["CURRENCY_COMMA_DECIMAL_ERROR"] += 1
                        patterns_found.append({
                            "pattern": "CURRENCY_COMMA_DECIMAL_ERROR",
                            "severity": "HIGH",
                            "explanation": f"Failed on international currency decimal separator or notation: expected {exp_val}, got {pred_val}."
                        })
                    else:
                        failure_counts["NUMERICAL_PRECISION_MISMATCH"] += 1
                        patterns_found.append({
                            "pattern": "NUMERICAL_PRECISION_MISMATCH",
                            "severity": "MEDIUM",
                            "explanation": f"Numerical error on {field}: expected {exp_val}, got {pred_val}."
                        })

                # Line item discrepancies
                elif field == "line_items":
                    failure_counts["LINE_ITEM_PARSING_ERROR"] += 1
                    patterns_found.append({
                        "pattern": "LINE_ITEM_PARSING_ERROR",
                        "severity": "MEDIUM",
                        "explanation": f"Mismatch in line item table extraction: expected count {exp_val}, got {pred_val}."
                    })

                # OCR noise errors
                elif tc.category == "ocr_noise":
                    failure_counts["OCR_NOISE_CORRUPTION"] += 1
                    patterns_found.append({
                        "pattern": "OCR_NOISE_CORRUPTION",
                        "severity": "MEDIUM",
                        "explanation": f"OCR text distortion caused field '{field}' extraction failure: expected '{exp_val}', got '{pred_val}'."
                    })

                # Vendor Name or Invoice number mismatch
                elif field == "vendor_name":
                    if tc.category == "adversarial_edge_cases":
                        failure_counts["MULTI_ENTITY_VENDOR_CONFUSION"] += 1
                        patterns_found.append({
                            "pattern": "MULTI_ENTITY_VENDOR_CONFUSION",
                            "severity": "HIGH",
                            "explanation": f"Confused between broker/remit-to/vendor entity name: expected '{exp_val}', got '{pred_val}'."
                        })
                    else:
                        failure_counts["ENTITY_NAME_INCOMPLETE_MATCH"] += 1
                        patterns_found.append({
                            "pattern": "ENTITY_NAME_INCOMPLETE_MATCH",
                            "severity": "LOW",
                            "explanation": f"Minor entity naming discrepancy: expected '{exp_val}', got '{pred_val}'."
                        })

            if patterns_found:
                case_diagnostics.append({
                    "test_case_id": tc_id,
                    "category": tc.category,
                    "difficulty": tc.difficulty,
                    "patterns": patterns_found
                })

        return {
            "total_flawed_cases": len(case_diagnostics),
            "failure_pattern_counts": dict(sorted(failure_counts.items(), key=lambda x: x[1], reverse=True)),
            "detailed_case_diagnostics": case_diagnostics
        }
