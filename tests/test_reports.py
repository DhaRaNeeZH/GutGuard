"""
Tests for PDF report generation and disclaimers using ReportLab.
"""
from datetime import date
from database.models import ReportRecord


def test_reports_index_page(auth_client):
    """Reports landing page displays generation form and disclaimer."""
    res = auth_client.get("/reports/")
    assert res.status_code == 200
    assert b"Meal Habit Reports" in res.data
    assert b"not medical assessments" in res.data


def test_generate_pdf_report(auth_client, student_user, db):
    """Generates a downloadable PDF report with ReportLab."""
    res = auth_client.post("/reports/generate", data={
        "period": "week",
    })

    assert res.status_code == 200
    assert res.headers["Content-Type"] == "application/pdf"
    assert "attachment" in res.headers.get("Content-Disposition", "")
    assert res.data.startswith(b"%PDF")

    # Verify a ReportRecord was saved
    record = ReportRecord.query.filter_by(user_id=student_user.id).first()
    assert record is not None
    assert "gutguard_report_" in record.filename


def test_generate_custom_date_range_report(auth_client, student_user, db):
    """Generates PDF report for a custom date range."""
    res = auth_client.post("/reports/generate", data={
        "period": "custom",
        "start_date": "2026-10-01",
        "end_date": "2026-10-15",
    })

    assert res.status_code == 200
    assert res.headers["Content-Type"] == "application/pdf"
    assert res.data.startswith(b"%PDF")


def test_download_past_report(auth_client, student_user, db):
    """Student can re-download previously generated reports."""
    # First generate a report to create a record
    auth_client.post("/reports/generate", data={"period": "week"})
    record = ReportRecord.query.filter_by(user_id=student_user.id).first()
    assert record is not None

    # Re-download the report
    res = auth_client.get(f"/reports/{record.id}/download")
    assert res.status_code == 200
    assert res.headers["Content-Type"] == "application/pdf"
    assert res.data.startswith(b"%PDF")

