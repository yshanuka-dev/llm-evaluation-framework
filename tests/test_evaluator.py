"""
Unit tests for the Evaluation Suite
"""
import pytest
from src.schemas import TestCase, InvoiceExtraction, LineItem
from src.evaluator import (
    normalize_str,
    compare_dates,
    compare_floats,
    match_line_items,
    ExtractionEvaluator
)
from src.failure_analyzer import FailureAnalyzer

def test_normalize_str():
    assert normalize_str("  Hello   World  ") == "hello world"
    assert normalize_str(None) == ""

def test_compare_dates():
    assert compare_dates("2024-03-15", "2024-03-15") is True
    assert compare_dates("2024-03-15", "2024-04-15") is False
    assert compare_dates(None, None) is True
    assert compare_dates("2024-03-15", None) is False

def test_compare_floats():
    assert compare_floats(100.0, 100.0) is True
    assert compare_floats(100.001, 100.0) is True
    assert compare_floats(100.1, 100.0) is False
    assert compare_floats(None, None) is True
    assert compare_floats(100.0, None) is False

def test_match_line_items():
    exp = [
        LineItem(description="Widget A", quantity=2.0, unit_price=10.0, total=20.0),
        LineItem(description="Widget B", quantity=1.0, unit_price=50.0, total=50.0)
    ]
    pred = [
        LineItem(description="Widget A", quantity=2.0, unit_price=10.0, total=20.0),
        LineItem(description="Widget B", quantity=1.0, unit_price=50.0, total=50.0)
    ]
    p, r, f1 = match_line_items(pred, exp)
    assert p == 1.0
    assert r == 1.0
    assert f1 == 1.0

def test_evaluate_case_clean():
    exp = InvoiceExtraction(
        invoice_number="INV-001",
        invoice_date="2024-01-01",
        vendor_name="Test Corp",
        total_amount=100.0
    )
    tc = TestCase(
        id="TC_001",
        category="standard_clean",
        description="Clean test",
        raw_document="Test Corp invoice INV-001 on 2024-01-01 total $100.00",
        expected_output=exp,
        difficulty="Easy"
    )
    result = ExtractionEvaluator.evaluate_case(tc, exp, parse_success=True)
    assert result["overall_accuracy"] > 0.95
    assert len(result["hallucinations"]) == 0
    assert len(result["mismatches"]) == 0

def test_evaluate_case_hallucination():
    exp = InvoiceExtraction(
        invoice_number="INV-001",
        invoice_date="2024-01-01",
        due_date=None,
        total_amount=100.0
    )
    pred = InvoiceExtraction(
        invoice_number="INV-001",
        invoice_date="2024-01-01",
        due_date="2024-02-01",  # Fabricated due date
        total_amount=100.0
    )
    tc = TestCase(
        id="TC_002",
        category="missing_optional_fields",
        description="Hallucination test",
        raw_document="Test",
        expected_output=exp,
        difficulty="Medium"
    )
    result = ExtractionEvaluator.evaluate_case(tc, pred, parse_success=True)
    assert "due_date" in result["hallucinations"]

def test_failure_analyzer():
    tc = TestCase(
        id="TC_003",
        category="adversarial_edge_cases",
        description="Decoy test",
        raw_document="Adversarial document",
        expected_output=InvoiceExtraction(total_amount=100.0),
        difficulty="Adversarial"
    )
    eval_res = {
        "test_case_id": "TC_003",
        "category": "adversarial_edge_cases",
        "difficulty": "Adversarial",
        "parse_success": True,
        "hallucinations": [],
        "mismatches": [("total_amount", 100.0, 999.0)]
    }
    diag = FailureAnalyzer.classify_failures([tc], [eval_res])
    assert diag["total_flawed_cases"] == 1
    assert "DECOY_VALUE_CONFUSION" in diag["failure_pattern_counts"]
