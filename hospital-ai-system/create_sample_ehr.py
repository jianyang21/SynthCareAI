"""Generate a sample EHR PDF for testing the Hospital AI System."""
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
import os

OUTPUT = os.path.join(os.path.dirname(__file__), "sample_ehr_patient1.pdf")


def create_sample_ehr():
    doc = SimpleDocTemplate(OUTPUT, pagesize=A4)
    styles = getSampleStyleSheet()
    title_style = ParagraphStyle("Title2", parent=styles["Title"], fontSize=18, spaceAfter=20)
    heading = ParagraphStyle("Heading", parent=styles["Heading2"], fontSize=14, spaceAfter=10)
    body = styles["BodyText"]

    elements = []

    # Header
    elements.append(Paragraph("🏥 City General Hospital", title_style))
    elements.append(Paragraph("Electronic Health Record (EHR)", heading))
    elements.append(Spacer(1, 10))

    # Patient Info
    elements.append(Paragraph("<b>Patient Information</b>", heading))
    patient_data = [
        ["Patient Name:", "Keshav Marian B"],
        ["Patient ID:", "1"],
        ["Date of Birth:", "January 15, 1995"],
        ["Gender:", "Male"],
        ["Blood Group:", "O+"],
        ["Phone:", "+91-9876543210"],
        ["Address:", "Chennai, Tamil Nadu, India"],
    ]
    t = Table(patient_data, colWidths=[2 * inch, 4 * inch])
    t.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.lightgrey),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t)
    elements.append(Spacer(1, 15))

    # Medical History
    elements.append(Paragraph("<b>Medical History</b>", heading))
    elements.append(Paragraph(
        "Patient has a history of <b>Type 2 Diabetes Mellitus</b> diagnosed in 2020. "
        "Also has <b>mild hypertension</b> (Stage 1) since 2021. Family history includes "
        "cardiovascular disease (father) and diabetes (mother). No known drug allergies. "
        "Non-smoker, occasional alcohol consumption.", body
    ))
    elements.append(Spacer(1, 10))

    # Diagnoses
    elements.append(Paragraph("<b>Current Diagnoses</b>", heading))
    elements.append(Paragraph("1. Type 2 Diabetes Mellitus (E11.9) — Under control with medication", body))
    elements.append(Paragraph("2. Essential Hypertension, Stage 1 (I10) — Managed with lifestyle + medication", body))
    elements.append(Paragraph("3. Vitamin D Deficiency (E55.9) — Supplementation ongoing", body))
    elements.append(Spacer(1, 10))

    # Medications / Prescriptions
    elements.append(Paragraph("<b>Current Prescriptions</b>", heading))
    med_data = [
        ["Medicine", "Dosage", "Frequency", "Duration"],
        ["Metformin 500mg", "500mg", "Twice daily after meals", "Ongoing"],
        ["Amlodipine 5mg", "5mg", "Once daily morning", "Ongoing"],
        ["Vitamin D3 60000 IU", "60000 IU", "Once weekly", "8 weeks"],
        ["Paracetamol 650mg", "650mg", "As needed for pain", "PRN"],
    ]
    t2 = Table(med_data, colWidths=[1.8 * inch, 1 * inch, 1.8 * inch, 1.2 * inch])
    t2.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 6),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#D6E4F0")]),
    ]))
    elements.append(t2)
    elements.append(Spacer(1, 15))

    # Lab Results
    elements.append(Paragraph("<b>Latest Lab Results (February 2026)</b>", heading))
    lab_data = [
        ["Test", "Result", "Reference Range", "Status"],
        ["Fasting Blood Sugar", "142 mg/dL", "70-100 mg/dL", "HIGH"],
        ["HbA1c", "7.2%", "<6.5%", "HIGH"],
        ["Blood Pressure", "138/88 mmHg", "<120/80 mmHg", "ELEVATED"],
        ["Total Cholesterol", "210 mg/dL", "<200 mg/dL", "BORDERLINE"],
        ["HDL Cholesterol", "45 mg/dL", ">40 mg/dL", "NORMAL"],
        ["LDL Cholesterol", "135 mg/dL", "<100 mg/dL", "HIGH"],
        ["Vitamin D", "18 ng/mL", "30-100 ng/mL", "LOW"],
        ["Creatinine", "0.9 mg/dL", "0.7-1.3 mg/dL", "NORMAL"],
        ["Hemoglobin", "14.2 g/dL", "13.5-17.5 g/dL", "NORMAL"],
    ]
    t3 = Table(lab_data, colWidths=[1.6 * inch, 1.2 * inch, 1.4 * inch, 1 * inch])
    t3.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#4472C4")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("PADDING", (0, 0), (-1, -1), 6),
    ]))
    elements.append(t3)
    elements.append(Spacer(1, 15))

    # Doctor's Notes
    elements.append(Paragraph("<b>Doctor's Notes</b>", heading))
    elements.append(Paragraph(
        "Patient presents with slightly elevated fasting blood sugar and HbA1c. "
        "Recommend increasing Metformin to 1000mg twice daily if next reading remains above 140. "
        "Blood pressure borderline — continue current Amlodipine dose and monitor. "
        "Cholesterol slightly elevated — advise dietary changes (reduce saturated fats, "
        "increase fiber intake). Continue Vitamin D supplementation for 8 more weeks "
        "and recheck levels. Schedule follow-up in 3 months.", body
    ))
    elements.append(Spacer(1, 10))

    # Allergies
    elements.append(Paragraph("<b>Allergies</b>", heading))
    elements.append(Paragraph("No known drug allergies (NKDA).", body))
    elements.append(Spacer(1, 10))

    # Follow-up
    elements.append(Paragraph("<b>Follow-up Plan</b>", heading))
    elements.append(Paragraph("1. Repeat HbA1c and Fasting Blood Sugar in 3 months", body))
    elements.append(Paragraph("2. Lipid panel recheck in 3 months", body))
    elements.append(Paragraph("3. Vitamin D recheck after 8 weeks", body))
    elements.append(Paragraph("4. Blood pressure monitoring — weekly at home", body))
    elements.append(Paragraph("5. Next appointment: May 2026 with Dr. Ramesh (Endocrinology)", body))

    doc.build(elements)
    print(f"Sample EHR PDF created: {OUTPUT}")
    return OUTPUT


if __name__ == "__main__":
    create_sample_ehr()
