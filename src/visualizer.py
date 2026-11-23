"""
Visualization and Reporting Utilities for LLM Evaluation Results
Generates professional comparison plots, ASCII tables, and Markdown artifacts.
"""
import os
from typing import Dict, Any, List
import matplotlib
matplotlib.use("Agg")  # Non-interactive backend for headless execution
import matplotlib.pyplot as plt
import numpy as np

class EvaluationVisualizer:
    """Generates charts and formatted tables for LLM evaluation."""

    @staticmethod
    def generate_charts(
        multi_model_results: Dict[str, Dict[str, Any]],
        multi_model_failures: Dict[str, Dict[str, Any]],
        output_dir: str = "reports"
    ) -> List[str]:
        os.makedirs(output_dir, exist_ok=True)
        generated_files = []

        # 1. Category Accuracy Comparison Chart
        categories = list(next(iter(multi_model_results.values()))["category_summary"].keys())
        cat_labels = [c.replace("_", " ").title() for c in categories]
        
        models = list(multi_model_results.keys())
        model_display_names = {
            "frontier_llm": "Frontier LLM (GPT-4o / Claude 3.5)",
            "mid_tier_llm": "Mid-Tier LLM (Gemini Flash / Llama 70B)",
            "baseline_small_llm": "Baseline 7B LLM"
        }

        fig, ax = plt.subplots(figsize=(12, 6))
        x = np.arange(len(categories))
        width = 0.25

        colors = ["#2563eb", "#10b981", "#f59e0b"]
        for idx, m in enumerate(models):
            accs = [multi_model_results[m]["category_summary"][c]["accuracy"] * 100 for c in categories]
            offset = (idx - len(models)/2 + 0.5) * width
            rects = ax.bar(x + offset, accs, width, label=model_display_names.get(m, m), color=colors[idx % len(colors)], alpha=0.9)
            # Add value labels on top of bars
            for rect in rects:
                height = rect.get_height()
                ax.annotate(f"{height:.1f}%",
                            xy=(rect.get_x() + rect.get_width() / 2, height),
                            xytext=(0, 3),  # 3 points vertical offset
                            textcoords="offset points",
                            ha='center', va='bottom', fontsize=8, rotation=0)

        ax.set_ylabel("Extraction Accuracy (%)", fontsize=11, fontweight="bold")
        ax.set_title("LLM Information Extraction Benchmark - Accuracy by Document Category", fontsize=13, fontweight="bold", pad=15)
        ax.set_xticks(x)
        ax.set_xticklabels(cat_labels, rotation=15, ha="right", fontsize=9)
        ax.set_ylim(0, 115)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        ax.legend(loc="upper right", framealpha=0.9)

        plt.tight_layout()
        cat_chart_path = os.path.join(output_dir, "accuracy_by_category.png")
        plt.savefig(cat_chart_path, dpi=200)
        plt.close()
        generated_files.append(cat_chart_path)

        # 2. Failure Pattern Distribution Chart
        # Aggregate failures for the mid-tier model
        mid_tier_failures = multi_model_failures.get("mid_tier_llm", {}).get("failure_pattern_counts", {})
        if mid_tier_failures:
            top_patterns = list(mid_tier_failures.items())[:8]
            pattern_names = [p[0].replace("_", " ").title() for p in top_patterns]
            pattern_vals = [p[1] for p in top_patterns]

            fig, ax = plt.subplots(figsize=(10, 5))
            y_pos = np.arange(len(pattern_names))
            bars = ax.barh(y_pos, pattern_vals, color="#e11d48", alpha=0.85)
            ax.set_yticks(y_pos)
            ax.set_yticklabels(pattern_names, fontsize=9)
            ax.invert_yaxis()  # top-down
            ax.set_xlabel("Incident Occurrences across 55 Test Cases", fontsize=10, fontweight="bold")
            ax.set_title("Empirical Failure Pattern Distribution (Mid-Tier LLM)", fontsize=12, fontweight="bold", pad=15)
            ax.grid(axis='x', linestyle='--', alpha=0.3)

            for bar in bars:
                width = bar.get_width()
                ax.annotate(f"{int(width)}",
                            xy=(width, bar.get_y() + bar.get_height() / 2),
                            xytext=(5, 0),
                            textcoords="offset points",
                            ha='left', va='center', fontsize=9, fontweight="bold")

            plt.tight_layout()
            fail_chart_path = os.path.join(output_dir, "failure_patterns.png")
            plt.savefig(fail_chart_path, dpi=200)
            plt.close()
            generated_files.append(fail_chart_path)

        return generated_files

    @staticmethod
    def format_markdown_table(headers: List[str], rows: List[List[Any]]) -> str:
        """Helper to format clean markdown tables."""
        col_widths = [len(h) for h in headers]
        for row in rows:
            for i, val in enumerate(row):
                col_widths[i] = max(col_widths[i], len(str(val)))

        header_str = "| " + " | ".join(f"{h:<{col_widths[i]}}" for i, h in enumerate(headers)) + " |"
        sep_str = "| " + " | ".join("-" * col_widths[i] for i in range(len(headers))) + " |"
        row_strs = ["| " + " | ".join(f"{str(v):<{col_widths[i]}}" for i, v in enumerate(row)) + " |" for row in rows]

        return "\n".join([header_str, sep_str] + row_strs)
