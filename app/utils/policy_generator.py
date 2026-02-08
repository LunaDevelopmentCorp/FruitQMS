from reportlab.lib.pagesizes import letter, A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT
import os
from datetime import datetime

def generate_policy_pdf(wizard, policy_type):
    """Generate policy PDF based on wizard data"""

    # Create uploads directory if it doesn't exist
    upload_dir = os.path.join('instance', 'uploads', 'policies')
    os.makedirs(upload_dir, exist_ok=True)

    filename = f'{policy_type}_{wizard.id}_{datetime.now().strftime("%Y%m%d")}.pdf'
    filepath = os.path.join(upload_dir, filename)

    doc = SimpleDocTemplate(filepath, pagesize=A4)
    story = []
    styles = getSampleStyleSheet()

    # Custom styles
    title_style = ParagraphStyle(
        'CustomTitle',
        parent=styles['Heading1'],
        fontSize=24,
        textColor=colors.HexColor('#28a745'),
        spaceAfter=30,
        alignment=TA_CENTER
    )

    heading_style = ParagraphStyle(
        'CustomHeading',
        parent=styles['Heading2'],
        fontSize=14,
        textColor=colors.HexColor('#28a745'),
        spaceAfter=12
    )

    # Generate content based on policy type
    if policy_type == 'haccp':
        story = generate_haccp_content(wizard, title_style, heading_style, styles)
    elif policy_type == 'spray_program':
        story = generate_spray_program_content(wizard, title_style, heading_style, styles)
    elif policy_type == 'environmental':
        story = generate_environmental_content(wizard, title_style, heading_style, styles)
    elif policy_type == 'waste_management':
        story = generate_waste_management_content(wizard, title_style, heading_style, styles)
    elif policy_type == 'training_log':
        story = generate_training_log_content(wizard, title_style, heading_style, styles)
    elif policy_type == 'traceability':
        story = generate_traceability_content(wizard, title_style, heading_style, styles)

    doc.build(story)
    return filepath


def generate_haccp_content(wizard, title_style, heading_style, styles):
    """Generate HACCP Plan content"""
    story = []

    story.append(Paragraph("HACCP Plan", title_style))
    story.append(Paragraph(f"<b>Organization:</b> {wizard.packhouse_name or 'Not Specified'}", styles['Normal']))
    story.append(Paragraph(f"<b>GGN:</b> {wizard.ggn_number or 'N/A'}", styles['Normal']))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("1. HACCP Team", heading_style))
    story.append(Paragraph("List the members of your HACCP team including names, positions, and responsibilities.", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    # HACCP Team Table
    team_data = [
        ['Name', 'Position', 'Responsibility'],
        ['', 'Quality Manager', 'HACCP Team Leader'],
        ['', 'Production Manager', 'Process oversight'],
        ['', 'Maintenance Supervisor', 'Equipment sanitation'],
    ]
    team_table = Table(team_data, colWidths=[2*inch, 2*inch, 2.5*inch])
    team_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(team_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("2. Product Description", heading_style))
    crops = wizard.crops_packed if wizard.crops_packed else 'Various fresh fruits'
    story.append(Paragraph(f"<b>Products:</b> {crops}", styles['Normal']))
    story.append(Paragraph("<b>Intended Use:</b> Fresh consumption", styles['Normal']))
    story.append(Paragraph("<b>Packaging:</b> Cartons, crates, punnets", styles['Normal']))
    story.append(Paragraph("<b>Storage:</b> Refrigerated (0-4°C)", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("3. Critical Control Points (CCPs)", heading_style))

    # CCPs Table
    ccp_data = [
        ['CCP', 'Hazard', 'Control Measure', 'Critical Limit', 'Monitoring'],
        ['Receiving', 'Contamination', 'Supplier approval', 'Approved suppliers only', 'Check supplier list'],
        ['Washing', 'Chemical residue', 'Water quality', 'Chlorine 50-200 ppm', 'Test daily'],
        ['Cold Storage', 'Microbial growth', 'Temperature control', '0-4°C', 'Monitor hourly'],
        ['Packing', 'Cross-contamination', 'Hygiene procedures', 'Clean equipment', 'Visual inspection'],
    ]

    ccp_table = Table(ccp_data, colWidths=[1*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    ccp_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
        ('VALIGN', (0, 0), (-1, -1), 'TOP')
    ]))
    story.append(ccp_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("4. Verification Procedures", heading_style))
    story.append(Paragraph("• Weekly review of monitoring records", styles['Normal']))
    story.append(Paragraph("• Monthly calibration of monitoring equipment", styles['Normal']))
    story.append(Paragraph("• Annual HACCP plan review and update", styles['Normal']))
    story.append(Paragraph("• External audit verification", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("5. Record Keeping", heading_style))
    story.append(Paragraph("All HACCP records must be maintained for a minimum of 2 years and include:", styles['Normal']))
    story.append(Paragraph("• CCP monitoring records", styles['Normal']))
    story.append(Paragraph("• Corrective action records", styles['Normal']))
    story.append(Paragraph("• Verification and validation records", styles['Normal']))
    story.append(Paragraph("• Training records", styles['Normal']))

    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("_" * 80, styles['Normal']))
    story.append(Paragraph("<b>Generated by FruitQMS - GLOBALG.A.P. Compliant</b>", styles['Normal']))

    return story


def generate_spray_program_content(wizard, title_style, heading_style, styles):
    """Generate Spray/IPM Program content"""
    story = []

    story.append(Paragraph("Integrated Pest Management (IPM) Program", title_style))
    story.append(Paragraph(f"<b>Farm:</b> {wizard.packhouse_name or 'Not Specified'}", styles['Normal']))
    story.append(Paragraph(f"<b>Generated:</b> {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("1. IPM Principles", heading_style))
    story.append(Paragraph("Our Integrated Pest Management program follows these core principles:", styles['Normal']))
    story.append(Paragraph("• Prevention: Cultural practices to reduce pest pressure", styles['Normal']))
    story.append(Paragraph("• Monitoring: Regular scouting and pest identification", styles['Normal']))
    story.append(Paragraph("• Economic thresholds: Spray only when economically justified", styles['Normal']))
    story.append(Paragraph("• Non-chemical control: Biological control, traps, resistant varieties", styles['Normal']))
    story.append(Paragraph("• Chemical control: Last resort, using approved products", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("2. Approved Pesticides List", heading_style))
    story.append(Paragraph("Only use pesticides:", styles['Normal']))
    story.append(Paragraph("• Approved for use in your country", styles['Normal']))
    story.append(Paragraph("• Registered for the target crop", styles['Normal']))
    story.append(Paragraph("• Listed on GLOBALG.A.P. approved database", styles['Normal']))
    story.append(Paragraph("• Applied according to label instructions", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("3. Spray Application Records", heading_style))

    # Spray record template
    spray_data = [
        ['Date', 'Block', 'Product', 'Active Ingredient', 'Rate', 'Reason', 'Operator'],
        ['', '', '', '', '', '', ''],
        ['', '', '', '', '', '', ''],
        ['', '', '', '', '', '', ''],
    ]

    spray_table = Table(spray_data, colWidths=[0.8*inch, 0.8*inch, 1.2*inch, 1.2*inch, 0.8*inch, 1.2*inch, 1*inch])
    spray_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 7),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(spray_table)
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("4. Pre-Harvest Intervals (PHI)", heading_style))
    story.append(Paragraph("All spray applications must respect PHI requirements:", styles['Normal']))
    story.append(Paragraph("• Check product label for specific PHI", styles['Normal']))
    story.append(Paragraph("• Record PHI on spray application form", styles['Normal']))
    story.append(Paragraph("• Do not harvest before PHI expires", styles['Normal']))
    story.append(Paragraph("• Maintain buffer zones where required", styles['Normal']))

    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("_" * 80, styles['Normal']))
    story.append(Paragraph("<b>Generated by FruitQMS - GLOBALG.A.P. Compliant</b>", styles['Normal']))

    return story


def generate_environmental_content(wizard, title_style, heading_style, styles):
    """Generate Environmental Policy content"""
    story = []

    story.append(Paragraph("Environmental Management Policy", title_style))
    story.append(Paragraph(f"<b>Organization:</b> {wizard.packhouse_name or 'Not Specified'}", styles['Normal']))
    story.append(Paragraph(f"<b>Effective Date:</b> {datetime.now().strftime('%Y-%m-%d')}", styles['Normal']))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("Policy Statement", heading_style))
    story.append(Paragraph(
        "We are committed to protecting the environment and promoting sustainable agricultural practices. "
        "This policy outlines our commitment to environmental stewardship in all our operations.",
        styles['Normal']
    ))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("1. Biodiversity Conservation", heading_style))
    story.append(Paragraph("• Maintain buffer zones around natural habitats", styles['Normal']))
    story.append(Paragraph("• Protect endangered species and ecosystems", styles['Normal']))
    story.append(Paragraph("• Promote beneficial insects and pollinators", styles['Normal']))
    story.append(Paragraph("• Avoid clearing virgin land", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("2. Water Management", heading_style))
    story.append(Paragraph("• Use water efficiently through drip irrigation", styles['Normal']))
    story.append(Paragraph("• Monitor water quality regularly", styles['Normal']))
    story.append(Paragraph("• Prevent contamination of water sources", styles['Normal']))
    story.append(Paragraph("• Implement water recycling where possible", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("3. Soil Management", heading_style))
    story.append(Paragraph("• Prevent soil erosion through cover crops", styles['Normal']))
    story.append(Paragraph("• Maintain soil organic matter", styles['Normal']))
    story.append(Paragraph("• Conduct regular soil testing", styles['Normal']))
    story.append(Paragraph("• Use sustainable fertilization practices", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))

    story.append(Paragraph("4. Energy Efficiency", heading_style))
    story.append(Paragraph("• Use energy-efficient equipment", styles['Normal']))
    story.append(Paragraph("• Reduce fossil fuel consumption", styles['Normal']))
    story.append(Paragraph("• Consider renewable energy sources", styles['Normal']))
    story.append(Paragraph("• Monitor and reduce carbon footprint", styles['Normal']))

    story.append(Spacer(1, 0.5*inch))
    story.append(Paragraph("Signed: _____________________ Date: _____________________", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph("_" * 80, styles['Normal']))
    story.append(Paragraph("<b>Generated by FruitQMS - GLOBALG.A.P. Compliant</b>", styles['Normal']))

    return story


def generate_waste_management_content(wizard, title_style, heading_style, styles):
    """Generate Waste Management Plan"""
    story = []

    story.append(Paragraph("Waste Management Plan", title_style))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("Waste Segregation", heading_style))
    story.append(Paragraph("All waste must be segregated into the following categories:", styles['Normal']))
    story.append(Paragraph("• Organic waste: Culled fruit, plant material → Composting", styles['Normal']))
    story.append(Paragraph("• Recyclable: Cardboard, plastic, metal → Recycling facility", styles['Normal']))
    story.append(Paragraph("• Hazardous: Empty pesticide containers → Licensed disposal", styles['Normal']))
    story.append(Paragraph("• General waste: Non-recyclable → Municipal disposal", styles['Normal']))

    return story


def generate_training_log_content(wizard, title_style, heading_style, styles):
    """Generate Training Log Template"""
    story = []

    story.append(Paragraph("Worker Training Log", title_style))
    story.append(Spacer(1, 0.3*inch))

    training_data = [
        ['Date', 'Worker Name', 'Training Topic', 'Trainer', 'Signature'],
        ['', '', 'Food Safety & Hygiene', '', ''],
        ['', '', 'Pesticide Safety', '', ''],
        ['', '', 'First Aid', '', ''],
        ['', '', 'Equipment Operation', '', ''],
    ]

    training_table = Table(training_data, colWidths=[1.2*inch, 1.8*inch, 2*inch, 1.5*inch, 1.5*inch])
    training_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(training_table)

    return story


def generate_traceability_content(wizard, title_style, heading_style, styles):
    """Generate Traceability Template"""
    story = []

    story.append(Paragraph("Traceability System", title_style))
    story.append(Spacer(1, 0.3*inch))

    story.append(Paragraph("Harvest Traceability", heading_style))

    trace_data = [
        ['Lot #', 'Block/Field', 'Harvest Date', 'Quantity', 'Destination'],
        ['', '', '', '', ''],
        ['', '', '', '', ''],
    ]

    trace_table = Table(trace_data, colWidths=[1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch, 1.5*inch])
    trace_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#28a745')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 1, colors.black)
    ]))
    story.append(trace_table)

    return story
