"""Smoke tests for service/pdf_report_generator.py."""

from service.pdf_report_generator import generate_pdf, generate_pipeline_pdf


def _assert_pdf(path):
    assert path.exists()
    assert path.stat().st_size > 0
    assert path.read_bytes().startswith(b"%PDF")


def test_generate_pdf_writes_non_empty_file(tmp_path):
    data = {
        "execution_status": "FAILED",
        "summary": {"total": 2, "passed": 1, "failed": 1, "duration": 1.5},
        "all_tests": [
            {"name": "test_ok", "status": "PASSED"},
            {"name": "test_bad[<param>]", "status": "FAILED"},
        ],
        "failed_tests": [
            {
                "name": "test_bad[<param>]",
                "failing_step": "Then <Element 'div'> is displayed & visible",
                "crash_message": "AssertionError: <Page url='x'> not displayed\nline two",
                "execution_log": ["Opening <application> & waiting"],
                "screenshot": "output/screenshots/missing.png",
            }
        ],
    }

    out = generate_pdf(data, output_path=tmp_path / "nested" / "report.pdf", project_root=tmp_path)

    _assert_pdf(out)


def test_generate_pdf_handles_empty_data(tmp_path):
    _assert_pdf(generate_pdf({}, output_path=tmp_path / "empty.pdf", project_root=tmp_path))


def test_generate_pipeline_pdf_handles_markup_characters_in_llm_output(tmp_path):
    data = {
        "job_id": "job-1",
        "status": "complete",
        "bug_analysis": "SAUCE-1: <b>unclosed & <script> tags </i> in LLM output",
        "test_execution": "Step 1 — expected a < b && c > d",
        "jira_update": "",
    }

    _assert_pdf(generate_pipeline_pdf(data, output_path=tmp_path / "pipeline.pdf"))
