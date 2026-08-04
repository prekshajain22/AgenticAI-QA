from datetime import datetime
from pathlib import Path

from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.platypus import (
    HRFlowable,
    Image,
    Paragraph,
    SimpleDocTemplate,
    Spacer,
)

PASS_COLOR = colors.HexColor("#2e7d32")
FAIL_COLOR = colors.HexColor("#c62828")
GREY_COLOR = colors.HexColor("#555555")


def generate_pdf(data, output_path=None, project_root=None):

    if output_path is None:
        output_path = Path("reports/QA_Execution_Report.pdf")

    output_path = Path(output_path)

    if project_root is None:
        project_root = output_path.resolve().parent.parent
    else:
        project_root = Path(project_root)
    output_path.parent.mkdir(parents=True, exist_ok=True)

    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=A4,
        leftMargin=20 * mm,
        rightMargin=20 * mm,
        topMargin=20 * mm,
        bottomMargin=20 * mm,
        title="QA Execution Report",
        author="AI Test Orchestrator",
    )

    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "Title",
        parent=styles["Title"],
        fontSize=20,
        textColor=colors.HexColor("#1a237e"),
        spaceAfter=4,
    )

    subtitle_style = ParagraphStyle(
        "Subtitle",
        parent=styles["Normal"],
        fontSize=11,
        textColor=GREY_COLOR,
        spaceAfter=2,
    )

    heading_style = ParagraphStyle(
        "Heading",
        parent=styles["Heading2"],
        fontSize=13,
        textColor=colors.HexColor("#1a237e"),
        spaceBefore=10,
        spaceAfter=4,
    )

    normal_style = ParagraphStyle(
        "Body",
        parent=styles["Normal"],
        fontSize=10,
        textColor=colors.HexColor("#212121"),
        spaceAfter=3,
    )

    pass_style = ParagraphStyle(
        "Pass",
        parent=styles["Normal"],
        fontSize=10,
        textColor=PASS_COLOR,
        spaceAfter=3,
    )

    fail_style = ParagraphStyle(
        "Fail",
        parent=styles["Normal"],
        fontSize=10,
        textColor=FAIL_COLOR,
        spaceAfter=3,
    )

    error_style = ParagraphStyle(
        "Error",
        parent=styles["Normal"],
        fontSize=8,
        textColor=GREY_COLOR,
        leftIndent=10,
        spaceAfter=6,
        fontName="Courier",
    )

    content = []

    # --- Header ---
    content.append(Paragraph("QA Execution Report", title_style))
    content.append(
        Paragraph("AI Test Orchestrator — Intelligent QA Execution & Reporting", subtitle_style)
    )
    content.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor("#1a237e")))
    content.append(Spacer(1, 6 * mm))

    # --- Execution Status ---
    execution_status = data.get("execution_status", "UNKNOWN")
    status_color = PASS_COLOR if execution_status == "PASSED" else FAIL_COLOR

    status_style = ParagraphStyle(
        "Status",
        parent=styles["Normal"],
        fontSize=14,
        textColor=status_color,
        spaceAfter=6,
    )

    content.append(Paragraph(f"Execution Status: {execution_status}", status_style))

    # --- Summary ---
    content.append(Paragraph("Summary", heading_style))
    content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#bbbbbb")))
    content.append(Spacer(1, 2 * mm))

    summary = data.get("summary", {})

    content.append(Paragraph(f"Total Tests:  {summary.get('total', 0)}", normal_style))
    content.append(Paragraph(f"Passed:  {summary.get('passed', 0)}", pass_style))
    content.append(Paragraph(f"Failed:  {summary.get('failed', 0)}", fail_style))
    content.append(Paragraph(f"Duration:  {summary.get('duration', 0)} seconds", normal_style))
    content.append(
        Paragraph(f"Generated:  {datetime.now().strftime('%d-%b-%Y  %H:%M')}", normal_style)
    )

    # --- Test Results ---
    content.append(Spacer(1, 4 * mm))
    content.append(Paragraph("Test Results", heading_style))
    content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#bbbbbb")))
    content.append(Spacer(1, 2 * mm))

    all_tests = data.get("all_tests", [])

    if all_tests:
        for test in all_tests:
            status = test.get("status", "UNKNOWN")
            name = test.get("name", "Unknown Test")

            if status == "PASSED":
                content.append(Paragraph(f"&#10003;  {name}", pass_style))
            else:
                content.append(Paragraph(f"&#10007;  {name}", fail_style))

    # --- Failed Test Details ---
    failed_tests = data.get("failed_tests", [])

    if failed_tests:
        content.append(Spacer(1, 4 * mm))
        content.append(Paragraph("Failure Details", heading_style))
        content.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#bbbbbb")))
        content.append(Spacer(1, 2 * mm))

        log_style = ParagraphStyle(
            "Log",
            parent=styles["Normal"],
            fontSize=8,
            textColor=PASS_COLOR,
            leftIndent=12,
            spaceAfter=2,
            fontName="Courier",
        )

        step_fail_style = ParagraphStyle(
            "StepFail",
            parent=styles["Normal"],
            fontSize=9,
            textColor=FAIL_COLOR,
            leftIndent=12,
            spaceAfter=3,
            fontName="Courier",
        )

        for test in failed_tests:
            name = test.get("name", "Unknown Test")
            failing_step = test.get("failing_step")
            crash_message = test.get("crash_message", "")
            execution_log = test.get("execution_log", [])
            screenshot = test.get("screenshot")

            content.append(Paragraph(f"&#10007;  {name}", fail_style))
            content.append(Spacer(1, 2 * mm))

            # Execution trace — completed actions
            if execution_log:
                content.append(Paragraph("Execution Trace:", normal_style))
                for log_msg in execution_log:
                    content.append(Paragraph(f"&#10003;  {log_msg}", log_style))
                content.append(Spacer(1, 2 * mm))

            # Failing step
            if failing_step:
                content.append(
                    Paragraph(
                        f"&#10007;  Failing Step:  {failing_step}",
                        step_fail_style,
                    )
                )
                content.append(Spacer(1, 1 * mm))

            # Clean assertion error
            if crash_message:
                content.append(
                    Paragraph(
                        crash_message.replace("\n", "<br/>"),
                        error_style,
                    )
                )

            # Screenshot
            if screenshot:
                screenshot_abs = project_root / screenshot
                if screenshot_abs.exists():
                    try:
                        img = Image(str(screenshot_abs))
                        max_width = 120 * mm
                        ratio = img.imageWidth / img.imageHeight
                        img.drawWidth = max_width
                        img.drawHeight = max_width / ratio
                        content.append(Spacer(1, 2 * mm))
                        content.append(img)
                    except Exception:
                        content.append(Paragraph(f"Screenshot: {screenshot}", error_style))
                else:
                    content.append(Paragraph(f"Screenshot not found: {screenshot}", error_style))

            content.append(Spacer(1, 4 * mm))

    doc.build(content)

    return output_path
