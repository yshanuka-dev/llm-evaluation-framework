"""
Pydantic Schemas for Document Information Extraction Benchmark
"""
from typing import List, Optional, Dict, Any
from pydantic import BaseModel, Field

class LineItem(BaseModel):
    description: str = Field(description="Description or title of the item/service")
    quantity: float = Field(default=1.0, description="Quantity of items")
    unit_price: float = Field(description="Unit price per item")
    total: float = Field(description="Total price for the line item")

class InvoiceExtraction(BaseModel):
    invoice_number: Optional[str] = Field(default=None, description="Unique invoice or receipt number")
    invoice_date: Optional[str] = Field(default=None, description="Date of issuance in ISO YYYY-MM-DD format if possible")
    due_date: Optional[str] = Field(default=None, description="Payment due date in ISO YYYY-MM-DD format if possible")
    vendor_name: Optional[str] = Field(default=None, description="Name of vendor, supplier, or billing company")
    currency: Optional[str] = Field(default="USD", description="Currency symbol or code (e.g. USD, EUR, GBP, LKR)")
    line_items: List[LineItem] = Field(default_factory=list, description="List of invoiced line items")
    subtotal: Optional[float] = Field(default=None, description="Subtotal amount before tax/shipping")
    tax_amount: Optional[float] = Field(default=None, description="Tax or VAT amount")
    total_amount: Optional[float] = Field(default=None, description="Grand total final amount payable")

class TestCase(BaseModel):
    id: str
    category: str
    description: str
    raw_document: str
    expected_output: InvoiceExtraction
    difficulty: str  # Easy, Medium, Hard, Adversarial
    metadata: Dict[str, Any] = Field(default_factory=dict)
