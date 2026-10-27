"""Reports routes – PDF generation with ReportLab."""
import os
import io
from datetime import datetime, timezone, date, timedelta
from flask import (
    render_template, send_file, redirect, url_for,
    flash, request, current_app, abort
)
from flask_login import login_required, current_user
from sqlalchemy import func

from . import reports_bp
try:
    from backend.extensions import db
    from database.models import Meal, WaterLog, ReportRecord
except ImportError:
    from extensions import db
    from models import Meal, WaterLog, ReportRecord


@reports_bp.route("/")
@login_required
def index():
    """Reports page – list generated reports and offer to create a new one."""
    reports = (
        ReportRecord.query
        .filter_by(user_id=current_user.id)
        .order_by(ReportRecord.generated_at.desc())
        .all()
    )
    return render_template("reports/index.html", reports=reports)


@reports_bp.route("/generate", methods=["POST"])
@login_required
def generate():
    """Generate a PDF habit summary report for a chosen period."""
    period_str = request.form.get("period", "week")

    today = date.today()
    if period_str == "week":
        start = today - timedelta(days=today.weekday())
        end   = today
    elif period_str == "month":
        start = today.replace(day=1)
        end   = today
    else:
        try:
            start = date.fromisoformat(request.form.get("start_date", ""))
            end   = date.fromisoformat(request.form.get("end_date", ""))
        except ValueError:
            flash("Invalid date range.", "danger")
            return redirect(url_for("reports.index"))

    # Fetch data
    is_demo_user = (current_user.email or "").startswith("demo@") or getattr(current_user, "student_id", "") == "DEMO001"

    meals_q = Meal.query.filter(
        Meal.user_id == current_user.id,
        func.date(Meal.meal_date) >= start,
        func.date(Meal.meal_date) <= end,
    )
    if not is_demo_user:
        meals_q = meals_q.filter(Meal.is_demo == False)
    meals = meals_q.order_by(Meal.meal_date).all()

    water_q = WaterLog.query.filter(
        WaterLog.user_id == current_user.id,
        func.date(WaterLog.logged_at) >= start,
        func.date(WaterLog.logged_at) <= end,
    )
    if not is_demo_user:
        water_q = water_q.filter(WaterLog.is_demo == False)
    water_logs = water_q.all()

    pdf_bytes = _build_pdf(current_user, meals, water_logs, start, end)

    filename = f"gutguard_report_{start.isoformat()}_{end.isoformat()}.pdf"
    record = ReportRecord(
        user_id=current_user.id,
        filename=filename,
        period_start=datetime.combine(start, datetime.min.time()).replace(tzinfo=timezone.utc),
        period_end=datetime.combine(end, datetime.min.time()).replace(tzinfo=timezone.utc),
    )
    db.session.add(record)
    db.session.commit()

    return send_file(
        io.BytesIO(pdf_bytes),
        download_name=filename,
        as_attachment=True,
        mimetype="application/pdf",
    )


@reports_bp.route("/<int:report_id>/download")
@login_required
def download(report_id):
    """Re-download a previously generated report."""
    record = db.get_or_404(ReportRecord, report_id)
    if record.user_id != current_user.id:
        abort(403)

    start = record.period_start.date() if record.period_start else date.today()
    end   = record.period_end.date()   if record.period_end   else date.today()

    is_demo_user = (current_user.email or "").startswith("demo@") or getattr(current_user, "student_id", "") == "DEMO001"
    meals_q = Meal.query.filter(
        Meal.user_id == current_user.id,
        func.date(Meal.meal_date) >= start,
        func.date(Meal.meal_date) <= end,
    )
    if not is_demo_user:
        meals_q = meals_q.filter(Meal.is_demo == False)
    meals = meals_q.order_by(Meal.meal_date).all()

    water_q = WaterLog.query.filter(
        WaterLog.user_id == current_user.id,
        func.date(WaterLog.logged_at) >= start,
        func.date(WaterLog.logged_at) <= end,
    )
    if not is_demo_user:
        water_q = water_q.filter(WaterLog.is_demo == False)
    water_logs = water_q.all()

    pdf_bytes = _build_pdf(current_user, meals, water_logs, start, end)
    return send_file(
        io.BytesIO(pdf_bytes),
        download_name=record.filename,
        as_attachment=True,
        mimetype="application/pdf",
    )


def _build_pdf(user, meals, water_logs, start: date, end: date) -> bytes:
    """Build and return PDF bytes using ReportLab."""
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import cm
    from reportlab.lib import colors
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
    )

    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=2*cm, rightMargin=2*cm,
        topMargin=2*cm, bottomMargin=2*cm,
    )

    styles = getSampleStyleSheet()
    green  = colors.HexColor("#059669")
    amber  = colors.HexColor("#D97706")
    dark   = colors.HexColor("#0F172A")

    title_style = ParagraphStyle(
        "Title", parent=styles["Title"],
        textColor=green, fontSize=22, spaceAfter=6
    )
    heading_style = ParagraphStyle(
        "Heading2", parent=styles["Heading2"],
        textColor=dark, fontSize=13, spaceBefore=14, spaceAfter=4
    )
    body_style = styles["BodyText"]
    disclaimer_style = ParagraphStyle(
        "Disclaimer", parent=styles["Italic"],
        textColor=colors.HexColor("#64748B"), fontSize=8, spaceAfter=4
    )

    story = []

    # Header
    story.append(Paragraph("GutGuard — Meal Habit Summary", title_style))
    story.append(Paragraph(
        f"Student: {user.display_name} | "
        f"Period: {start.strftime('%d %b %Y')} – {end.strftime('%d %b %Y')} | "
        f"Generated: {datetime.now().strftime('%d %b %Y %H:%M')}",
        body_style
    ))
    story.append(HRFlowable(width="100%", thickness=1, color=green, spaceAfter=8))

    # Disclaimer
    story.append(Paragraph(
        "⚠ IMPORTANT NOTICE: This report is a personal meal habit summary based solely on "
        "self-logged data. It is NOT a medical diagnosis, a clinical assessment, or a "
        "professional nutritional evaluation. The figures below reflect only what was recorded "
        "in GutGuard during the selected period. If you have concerns about your health, "
        "please consult a qualified healthcare professional.",
        disclaimer_style
    ))
    story.append(Spacer(1, 0.4*cm))

    # Summary table
    total_days = (end - start).days + 1
    days_logged = len({m.meal_date.date() for m in meals})
    type_counts = {"breakfast": 0, "lunch": 0, "dinner": 0, "snack": 0}
    for m in meals:
        type_counts[m.meal_type] += 1

    total_water = sum((w.quantity or 0) for w in water_logs if w.unit == "ml")

    story.append(Paragraph("Summary", heading_style))
    summary_data = [
        ["Metric", "Value"],
        ["Observation period (days)", str(total_days)],
        ["Days with at least one logged meal", str(days_logged)],
        ["Total meals logged", str(len(meals))],
        ["  Breakfasts", str(type_counts["breakfast"])],
        ["  Lunches",    str(type_counts["lunch"])],
        ["  Dinners",    str(type_counts["dinner"])],
        ["  Snacks",     str(type_counts["snack"])],
        ["Water logged (ml)", f"{total_water:.0f} ml"],
    ]
    tbl = Table(summary_data, colWidths=[10*cm, 5*cm])
    tbl.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), green),
        ("TEXTCOLOR",  (0, 0), (-1, 0), colors.white),
        ("FONTNAME",   (0, 0), (-1, 0), "Helvetica-Bold"),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0FDF4")]),
        ("GRID", (0, 0), (-1, -1), 0.4, colors.HexColor("#D1D5DB")),
        ("FONTSIZE", (0, 0), (-1, -1), 9),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
    ]))
    story.append(tbl)
    story.append(Spacer(1, 0.4*cm))

    # Meal log
    story.append(Paragraph("Logged Meals", heading_style))
    if meals:
        meal_rows = [["Date", "Type", "Items", "Notes"]]
        for m in meals:
            items_str = ", ".join(i.food_name for i in m.items) or "—"
            if len(items_str) > 60:
                items_str = items_str[:57] + "…"
            meal_rows.append([
                m.meal_date.strftime("%d %b"),
                m.meal_type.capitalize(),
                items_str,
                (m.notes or "")[:40],
            ])
        meal_tbl = Table(meal_rows, colWidths=[2*cm, 2.5*cm, 9*cm, 3*cm])
        meal_tbl.setStyle(TableStyle([
            ("BACKGROUND",  (0, 0), (-1, 0), green),
            ("TEXTCOLOR",   (0, 0), (-1, 0), colors.white),
            ("FONTNAME",    (0, 0), (-1, 0), "Helvetica-Bold"),
            ("FONTSIZE",    (0, 0), (-1, -1), 8),
            ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F0FDF4")]),
            ("GRID",        (0, 0), (-1, -1), 0.3, colors.HexColor("#D1D5DB")),
            ("TOPPADDING",  (0, 0), (-1, -1), 4),
            ("BOTTOMPADDING",(0,0), (-1, -1), 4),
        ]))
        story.append(meal_tbl)
    else:
        story.append(Paragraph("No meals logged in this period.", body_style))

    # Methodology note
    story.append(Spacer(1, 0.6*cm))
    story.append(Paragraph("Methodology & Limitations", heading_style))
    story.append(Paragraph(
        "Data source: Self-reported entries recorded by the student in GutGuard. "
        "Consistency figures count only days for which at least one meal was logged; "
        "unlogged days are not assumed to represent skipped meals. "
        "No nutritional analysis is performed unless verified data is available. "
        "This report is intended for personal reflection and, where the student "
        "explicitly chooses, for review by an authorized campus health professional.",
        body_style
    ))

    doc.build(story)
    return buf.getvalue()
