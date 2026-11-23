"""
Submission Packager
Creates a clean, portable ZIP archive of the entire assignment project.
"""
import zipfile
import os

def package_submission(output_zip="Submission_LLM_Evaluation_Framework.zip"):
    included_files = [
        "README.md",
        "assignment.txt",
        "main.py",
        "generate_pdf_report.py",
        "pytest.ini",
        "data/test_cases.json",
        "data/evaluation_results.json",
        "reports/Technical_Evaluation_Report.pdf",
        "reports/technical_evaluation_report.md",
        "reports/accuracy_by_category.png",
        "reports/failure_patterns.png",
        "src/__init__.py",
        "src/schemas.py",
        "src/dataset.py",
        "src/extractor.py",
        "src/evaluator.py",
        "src/failure_analyzer.py",
        "src/visualizer.py",
        "tests/test_evaluator.py"
    ]

    with zipfile.ZipFile(output_zip, "w", zipfile.ZIP_DEFLATED) as zipf:
        for file_path in included_files:
            if os.path.exists(file_path):
                zipf.write(file_path, arcname=file_path)
                print(f"Added to archive: {file_path}")
            else:
                print(f"Warning: file not found: {file_path}")

    print(f"\nSuccessfully created submission archive: {output_zip} ({os.path.getsize(output_zip)} bytes)")

if __name__ == "__main__":
    package_submission()
