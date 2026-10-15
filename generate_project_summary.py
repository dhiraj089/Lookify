import os
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_report():
    output_path = "Lookify_Final_Technical_Report.pdf"
    doc = SimpleDocTemplate(output_path, pagesize=letter)
    styles = getSampleStyleSheet()
    elements = []

    # Title
    title_style = ParagraphStyle(
        'MainTitle', parent=styles['Heading1'], fontSize=24, fontName='Helvetica-Bold', 
        textColor=colors.black, spaceAfter=20, alignment=1
    )
    elements.append(Paragraph("Lookify: AI Fashion Platform - Technical Documentation", title_style))
    elements.append(Spacer(1, 0.2*72))

    # Introduction
    elements.append(Paragraph("1. Project Overview", styles['Heading2']))
    elements.append(Paragraph(
        "Lookify is an end-to-end AI-powered fashion platform that integrates a premium e-commerce frontend "
        "with deep learning models for visual search and virtual try-ons. The system is designed to provide "
        "a personalized shopping experience by analyzing visual features of clothing.", 
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.1*72))

    # Architecture
    elements.append(Paragraph("2. System Architecture", styles['Heading2']))
    data = [
        ["Module", "Technology", "Role"],
        ["Business Engine", "Flask (Python)", "API, User Mgmt, Orders, Invoicing"],
        ["AI Engine", "Streamlit", "Visual Recommender, Virtual Try-On"],
        ["Database", "JSON / MySQL", "Persistence of users and transactions"],
        ["Frontend", "HTML5, CSS3, JS", "Premium 'Streetwear' UI/UX"],
        ["Automation", "ReportLab, SMTPLib", "Automated PDF Invoices & Emails"]
    ]
    t = Table(data, colWidths=[110, 110, 280])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.black),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.grey)
    ]))
    elements.append(t)
    elements.append(Spacer(1, 0.2*72))

    # Machine Learning Section
    elements.append(Paragraph("3. Machine Learning Models", styles['Heading2']))
    ml_content = [
        ("Visual Similarity Search", "Based on ResNet-50 CNN. Extracts 2048-dimensional features to find similar items via K-Nearest Neighbors (KNN)."),
        ("Virtual Try-On", "Utilizes IDM-VTON (Diffusion Model) to warp garments onto human bodies realistically while preserving lighting."),
        ("AI Fashion Stylist", "Integrated Google Gemini Pro LLM to provide occasion-based fashion advice and trend analysis.")
    ]
    for title, desc in ml_content:
        elements.append(Paragraph(f"<b>{title}:</b> {desc}", styles['Normal']))
        elements.append(Spacer(1, 4))
    
    elements.append(Spacer(1, 0.1*72))

    # Features
    elements.append(Paragraph("4. Key Features Implemented", styles['Heading2']))
    features = [
        "Premium UI: Streetwear aesthetic with glassmorphism and custom animations.",
        "Auto-Invoicing: Real-time generation of PDF receipts using ReportLab.",
        "Email Notifications: Asynchronous mailing system for order confirmations.",
        "Session Handoff: Seamless cart transfer between the Flask and Streamlit apps.",
        "Fuzzy Search: Tokenized search algorithm querying 44k+ datasets in milliseconds."
    ]
    for feat in features:
        elements.append(Paragraph(f"• {feat}", styles['Normal']))

    # Footer
    elements.append(Spacer(1, 0.5*72))
    elements.append(Paragraph("© 2026 Lookify Technical Division", styles['Normal']))

    doc.build(elements)
    print(f"Report generated at: {os.path.abspath(output_path)}")

if __name__ == "__main__":
    generate_report()
