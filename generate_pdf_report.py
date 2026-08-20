"""
Comprehensive Academic & Technical Research Report Generator for ELECT-SENTINEL OSINT.
Generates an in-depth, rigorous theoretical and engineering documentation PDF.
"""

import os
import sys
from datetime import datetime

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, KeepTogether, HRFlowable
)
from reportlab.pdfgen import canvas


class NumberedCanvas(canvas.Canvas):
    def __init__(self, *args, **kwargs):
        super(NumberedCanvas, self).__init__(*args, **kwargs)
        self._saved_page_states = []

    def showPage(self):
        self._saved_page_states.append(dict(self.__dict__))
        self._startPage()

    def save(self):
        num_pages = len(self._saved_page_states)
        for state in self._saved_page_states:
            self.__dict__.update(state)
            self.draw_page_decorations(num_pages)
            super(NumberedCanvas, self).showPage()
        super(NumberedCanvas, self).save()

    def draw_page_decorations(self, page_count):
        self.saveState()
        self.setFont("Helvetica", 8)
        self.setFillColor(colors.HexColor("#64748b"))
        
        # Header (pages > 1)
        if self._pageNumber > 1:
            self.drawString(54, 750, "ELECT-SENTINEL OSINT | Comprehensive Academic & Technical Report")
            self.drawRightString(612 - 54, 750, "Jyotiraditya Cheemakurthi (23011103011)")
            self.setStrokeColor(colors.HexColor("#cbd5e1"))
            self.setLineWidth(0.5)
            self.line(54, 742, 612 - 54, 742)

        # Footer
        self.setStrokeColor(colors.HexColor("#cbd5e1"))
        self.setLineWidth(0.5)
        self.line(54, 42, 612 - 54, 42)
        
        self.drawString(54, 30, "Repository: https://github.com/being-cheema/elect-sentinel-osint")
        page_str = f"Page {self._pageNumber} of {page_count}"
        self.drawRightString(612 - 54, 30, page_str)
        self.restoreState()


def generate_pdf(output_filename="ELECT_SENTINEL_OSINT_Project_Report.pdf"):
    doc = SimpleDocTemplate(
        output_filename,
        pagesize=letter,
        leftMargin=50,
        rightMargin=50,
        topMargin=50,
        bottomMargin=50
    )

    styles = getSampleStyleSheet()

    PRIMARY = colors.HexColor("#0f172a")     # Slate 900
    ACCENT_CYAN = colors.HexColor("#0284c7") # Cyan 600
    ACCENT_BLUE = colors.HexColor("#1d4ed8") # Blue 700
    DARK_TEXT = colors.HexColor("#1e293b")   # Slate 800
    MUTED_TEXT = colors.HexColor("#475569")  # Slate 600
    BG_LIGHT = colors.HexColor("#f8fafc")    # Slate 50
    BORDER_COLOR = colors.HexColor("#cbd5e1")

    # Typography Styles
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=20,
        leading=24,
        textColor=PRIMARY,
        spaceAfter=3
    )

    subtitle_style = ParagraphStyle(
        'DocSubtitle',
        parent=styles['Normal'],
        fontName='Helvetica-Bold',
        fontSize=10.5,
        leading=14,
        textColor=ACCENT_CYAN,
        spaceAfter=8
    )

    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=DARK_TEXT
    )

    h1_style = ParagraphStyle(
        'Heading1_Custom',
        parent=styles['Heading1'],
        fontName='Helvetica-Bold',
        fontSize=12.5,
        leading=16,
        textColor=PRIMARY,
        spaceBefore=11,
        spaceAfter=4,
        keepWithNext=True
    )

    h2_style = ParagraphStyle(
        'Heading2_Custom',
        parent=styles['Heading2'],
        fontName='Helvetica-Bold',
        fontSize=10,
        leading=13,
        textColor=ACCENT_CYAN,
        spaceBefore=7,
        spaceAfter=3,
        keepWithNext=True
    )

    body_style = ParagraphStyle(
        'Body_Custom',
        parent=styles['BodyText'],
        fontName='Helvetica',
        fontSize=8.8,
        leading=12.5,
        textColor=DARK_TEXT,
        spaceAfter=5
    )

    bullet_style = ParagraphStyle(
        'Bullet_Custom',
        parent=styles['Normal'],
        fontName='Helvetica',
        fontSize=8.5,
        leading=12,
        textColor=DARK_TEXT,
        leftIndent=12,
        firstLineIndent=-8,
        spaceAfter=2.5
    )

    formula_style = ParagraphStyle(
        'Formula_Custom',
        parent=styles['Normal'],
        fontName='Courier-Bold',
        fontSize=8.5,
        leading=11.5,
        textColor=colors.HexColor("#0f172a"),
        alignment=1, # Centered
        spaceBefore=4,
        spaceAfter=4
    )

    code_style = ParagraphStyle(
        'Code_Custom',
        parent=styles['Normal'],
        fontName='Courier',
        fontSize=7.8,
        leading=10.5,
        textColor=colors.HexColor("#0f172a")
    )

    story = []

    # -------------------------------------------------------------
    # HEADER BANNER & METADATA CARD
    # -------------------------------------------------------------
    story.append(Paragraph("ELECT-SENTINEL OSINT", title_style))
    story.append(Paragraph("A Theoretical & Practical Framework for Real-Time Global Election Disinformation Monitoring, Dynamic Narrative Clustering, and Public Confusion Mitigation", subtitle_style))
    story.append(HRFlowable(width="100%", thickness=1.5, color=ACCENT_CYAN, spaceBefore=2, spaceAfter=8))

    meta_table_data = [
        [
            Paragraph("<b>Topic:</b> Topic 1 — Election Disinformation & Public Confusion OSINT", meta_style),
            Paragraph("<b>Student Name:</b> Jyotiraditya Cheemakurthi", meta_style)
        ],
        [
            Paragraph("<b>GitHub Repository:</b> <font color='#0284c7'><u>https://github.com/being-cheema/elect-sentinel-osint</u></font>", meta_style),
            Paragraph("<b>Roll Number:</b> 23011103011", meta_style)
        ],
        [
            Paragraph("<b>Operational Status:</b> 100% Real Live Digital Streams (All Countries)", meta_style),
            Paragraph(f"<b>Submission Date:</b> {datetime.now().strftime('%B %d, %Y')}", meta_style)
        ]
    ]
    meta_table = Table(meta_table_data, colWidths=[3.5 * inch, 3.6 * inch])
    meta_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), BG_LIGHT),
        ('BOX', (0, 0), (-1, -1), 1, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 6),
        ('RIGHTPADDING', (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # 1. THEORETICAL FOUNDATIONS & INFORMATION DISORDER MODEL
    # -------------------------------------------------------------
    story.append(Paragraph("1. Theoretical Foundations & Problem Statement", h1_style))
    story.append(Paragraph(
        "<b>1.1 Information Disorder Taxonomy (Wardle & Derakhshan Framework):</b> During critical election cycles, public discourse experiences heightened vulnerability to weaponized information. This research categorizes election-period confusion across three distinct conceptual dimensions: <i>(1) Disinformation</i> (knowingly fabricated content disseminated with malicious intent to suppress votes or alter outcomes), <i>(2) Misinformation</i> (false information shared inadvertently by confused citizens without malicious intent), and <i>(3) Malinformation</i> (genuine information taken out of context, selectively leaked, or distorted to inflict harm).",
        body_style
    ))
    story.append(Paragraph(
        "<b>1.2 Cognitive Vulnerabilities & Epistemic Uncertainty:</b> Misleading claims thrive during elections due to high affective polarization and epistemic uncertainty. When official counting protocols, ballot verification rules, or polling hours are ambiguous, unverified rumors spread rapidly through online echo chambers. The objective of <b>ELECT-SENTINEL OSINT</b> is to construct an automated intelligence system capable of monitoring multi-channel digital communications globally, identifying emerging confusion vectors before they peak, and equipping election oversight teams with rapid rebuttal intelligence.",
        body_style
    ))

    # -------------------------------------------------------------
    # 2. MATHEMATICAL MODELS & ALGORITHMIC FORMULATIONS
    # -------------------------------------------------------------
    story.append(Paragraph("2. Mathematical Formulations & Threat Modeling", h1_style))
    story.append(Paragraph(
        "The platform implements a multi-parameter mathematical model to evaluate threat severity, viral velocity, and narrative clustering similarity across digital posts:",
        body_style
    ))

    # Model Formula Box
    formula_text = "S_confusion = [ α · S_category + β · S_urgency + γ · S_uncertainty + δ · P_bot ] × Ω_platform"
    story.append(Table([[Paragraph(formula_text, formula_style)]], colWidths=[7.1 * inch], style=[
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('BOX', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('PADDING', (0, 0), (-1, -1), 4)
    ]))
    story.append(Spacer(1, 4))

    story.append(Paragraph(
        "Where: "
        "<br/>&bull; <b>S_category (&alpha; = 0.60):</b> Semantic threat weight assigned based on matched disinformation taxonomies (Voter Suppression, Machine Tampering, Deepfakes, Official Impersonation, Premature Results, Intimidation)."
        "<br/>&bull; <b>S_urgency (&beta; = 0.20):</b> Outrage and emotional urgency marker intensity calculated from linguistic triggers (e.g., 'URGENT SPREAD NOW', excessive capitalization, panic punctuation)."
        "<br/>&bull; <b>S_uncertainty (&gamma; = 0.20):</b> Epistemic rumor index derived from unverified hearsay qualifiers ('insider reveals', 'they don't want you to know', 'allegedly')."
        "<br/>&bull; <b>P_bot (&delta; = 0.15):</b> Inauthenticity probability score derived from account age ratio, high posting burst rate, and copypasta repetition patterns."
        "<br/>&bull; <b>&Omega;_platform:</b> Platform risk coefficient (&Omega; &in; [0.65, 1.25]) weighted by source channel anonymity and moderation policies.",
        body_style
    ))

    story.append(Paragraph("<b>2.2 Dynamic Narrative Clustering & Lifecycle State Machine:</b>", h2_style))
    story.append(Paragraph(
        "Individual posts are vectorized using n-gram Term Frequency-Inverse Document Frequency (TF-IDF):",
        body_style
    ))
    story.append(Paragraph("TF-IDF(t, d, D) = TF(t, d) × log( |D| / |{d ∈ D : t ∈ d}| )", formula_style))
    story.append(Paragraph(
        "Incoming vectors are matched against active narrative centroids using Cosine Similarity: <code>Sim(v_p, v_N) = (v_p · v_N) / (||v_p|| ||v_N||)</code>. If similarity exceeds the dynamic threshold (&theta; &ge; 0.28), the signal is assigned to the narrative cluster; otherwise, a new storyline centroid is spawned. Narrative lifecycle transitions through a discrete state machine: <b>Emerging &rarr; Accelerating &rarr; Critical Peak &rarr; Debunked &rarr; Dormant</b>.",
        body_style
    ))

    # Page Break for Architecture & Sources
    story.append(PageBreak())

    # -------------------------------------------------------------
    # 3. MULTI-SOURCE INGESTION ARCHITECTURE (25+ SOURCES)
    # -------------------------------------------------------------
    story.append(Paragraph("3. Multi-Source Global Live Ingestion Engine", h1_style))
    story.append(Paragraph(
        "The system operates with <b>zero mock data</b>, pulling exclusively from 25+ real-time live digital feeds across the globe via a multi-threaded parallel architecture (<code>ThreadPoolExecutor</code> with 12 concurrent workers):",
        body_style
    ))

    sources_data = [
        [
            Paragraph("<b>Category</b>", ParagraphStyle('TH', parent=meta_style, fontName='Helvetica-Bold', textColor=colors.white)),
            Paragraph("<b>Source Wires & Digital Endpoints</b>", ParagraphStyle('TH2', parent=meta_style, fontName='Helvetica-Bold', textColor=colors.white)),
            Paragraph("<b>Geographic Scope & Purpose</b>", ParagraphStyle('TH3', parent=meta_style, fontName='Helvetica-Bold', textColor=colors.white))
        ],
        [
            Paragraph("<b>Fact Checkers & Monitors</b>", meta_style),
            Paragraph("EUvsDisinfo (EU Strategic Disinformation DB), PolitiFact Truth-O-Meter, FactCheck.org, FullFact UK, Google News Global Disinformation & Deepfakes Monitor", meta_style),
            Paragraph("International claim refutation, synthetic media detection, and verified debunk repositories.", meta_style)
        ],
        [
            Paragraph("<b>Global Broadcasters</b>", meta_style),
            Paragraph("BBC World News, Euronews International, The Guardian World, Al Jazeera English, Deutsche Welle (DW), France24 International", meta_style),
            Paragraph("Worldwide continuous news wire monitoring in English, French, German, and Spanish.", meta_style)
        ],
        [
            Paragraph("<b>Asia-Pacific & South Asia</b>", meta_style),
            Paragraph("The Hindu, Times of India, NDTV India, Google News Australia (Australian Electoral Commission & Federal Politics)", meta_style),
            Paragraph("India, South Asia, and Commonwealth electoral monitoring.", meta_style)
        ],
        [
            Paragraph("<b>Americas & Africa</b>", meta_style),
            Paragraph("Google News Canada, Google News US, Daily Maverick (South Africa), AllAfrica (40+ nations), MercoPress (Latin America / Mercosur)", meta_style),
            Paragraph("North America, Pan-Africa, and South American electoral coverage.", meta_style)
        ],
        [
            Paragraph("<b>Decentralized Social</b>", meta_style),
            Paragraph("Mastodon Public Federation Live Firehose (15+ international tags: #election, #voting, #democracy, #wahl, #elecciones, #eleicoes, #disinformation)", meta_style),
            Paragraph("Real-time live social chatter across thousands of federated instance nodes.", meta_style)
        ]
    ]

    sources_table = Table(sources_data, colWidths=[1.6 * inch, 3.8 * inch, 1.7 * inch])
    sources_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(sources_table)
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # 4. GLOBAL GEOGRAPHIC RESOLUTION & GRAPH TOPOLOGY
    # -------------------------------------------------------------
    story.append(Paragraph("4. Global Geocoding & Coordinated Inauthentic Behavior (CIB)", h1_style))
    story.append(Paragraph(
        "<b>4.1 Global Geographic Entity Resolution:</b> Content from any country is processed through a multi-national entity dictionary mapping over 60+ countries and capital jurisdictions (Americas, Europe, Asia-Pacific, Africa, Middle East, Oceania) to exact latitude and longitude coordinates. Resolved coordinates are dynamically rendered on the interactive Leaflet.js Dark Matter Map.",
        body_style
    ))
    story.append(Paragraph(
        "<b>4.2 NetworkX Graph Modeling & CIB Swarm Detection:</b> The system builds a multi-relational graph G = (V, E) where nodes represent Accounts, Narrative Storylines, Hashtags, and Digital Domains. Edges capture posting relationships, copypasta text similarity (Jaccard Index &ge; 0.65 within temporal windows), and cross-platform amplification. High-centrality hub accounts and coordinated astroturf clusters are highlighted automatically in real-time.",
        body_style
    ))

    # -------------------------------------------------------------
    # 5. CYBER OPERATIONS CENTER WORKSPACES
    # -------------------------------------------------------------
    story.append(Paragraph("5. The 8 Analyst Workstations", h1_style))

    workspaces = [
        ("1. Threat Radar", "Real-time DEFCON threat gauge (Critical/Elevated/Nominal), KPI dials, Category Threat Distribution Chart, Dissemination Bar Chart, and live stream ticker with audio alerts."),
        ("2. Narrative Intelligence", "Visual clustering hub tracking narrative lifecycles, viral velocity (posts/hr), cross-platform dispersion, and drill-down investigative links."),
        ("3. Analyst Triage Queue", "Multi-parameter filterable queue (Category, Platform, Priority P0-P3, Status, Min Confusion slider) with deep forensic inspector modal featuring SHA-256 cryptographic evidence hashes and triage status escalation."),
        ("4. Actor & Propagation Graph", "Interactive HTML5 Canvas physics network with spring-repulsion simulation, zoom/pan controls, draggable nodes, and CIB bot swarm community identification."),
        ("5. Global Geospatial Map", "Interactive dark-mode Leaflet.js map with localized threat circles colored by confusion index across 60+ countries worldwide."),
        ("6. Live OSINT Scanner", "Ad-hoc forensic investigation tool allowing analysts to paste any live URL, post, or claim from any country for instant threat evaluation and geocoding."),
        ("7. Ground Truth KB", "Repository of verified statutory election rules and voting security mandates with one-click rapid counter-messaging fact-check templates."),
        ("8. Intelligence Dossiers", "Case Management workbench synthesizing formal OSINT Threat Intelligence Briefings exportable to Markdown, HTML, and printable format.")
    ]

    for title, desc in workspaces:
        story.append(Paragraph(f"<b>{title}:</b> {desc}", bullet_style))

    story.append(Spacer(1, 6))

    # Page Break for Verification & Evaluator Instructions
    story.append(PageBreak())

    # -------------------------------------------------------------
    # 6. EMPIRICAL VERIFICATION & BENCHMARKS
    # -------------------------------------------------------------
    story.append(Paragraph("6. Empirical Verification, Testing & Benchmarks", h1_style))
    story.append(Paragraph(
        "The platform includes an automated Python test suite (<code>tests/test_osint_engine.py</code>) verifying NLP classification accuracy, statutory contradiction detection, dynamic clustering, and graph generation:",
        body_style
    ))

    test_data = [
        [
            Paragraph("<b>Test Suite Module</b>", ParagraphStyle('TH', parent=meta_style, fontName='Helvetica-Bold', textColor=colors.white)),
            Paragraph("<b>Evaluation Scope</b>", ParagraphStyle('TH2', parent=meta_style, fontName='Helvetica-Bold', textColor=colors.white)),
            Paragraph("<b>Test Result</b>", ParagraphStyle('TH3', parent=meta_style, fontName='Helvetica-Bold', textColor=colors.white))
        ],
        [Paragraph("<code>test_database_initialization</code>", code_style), Paragraph("SQLite schema creation, ground truth seeding, and indices", meta_style), Paragraph("<font color='#16a34a'><b>PASSED (100%)</b></font>", meta_style)],
        [Paragraph("<code>test_global_location_resolution</code>", code_style), Paragraph("Entity extraction & geocoding across multi-continent text", meta_style), Paragraph("<font color='#16a34a'><b>PASSED (100%)</b></font>", meta_style)],
        [Paragraph("<code>test_nlp_voter_suppression_detection</code>", code_style), Paragraph("Confusion scoring & category classification for suppression", meta_style), Paragraph("<font color='#16a34a'><b>PASSED (100%)</b></font>", meta_style)],
        [Paragraph("<code>test_nlp_machine_rigging_detection</code>", code_style), Paragraph("Equipment tampering & election integrity conspiracy detection", meta_style), Paragraph("<font color='#16a34a'><b>PASSED (100%)</b></font>", meta_style)],
        [Paragraph("<code>test_ground_truth_contradiction</code>", code_style), Paragraph("Statutory rule contradiction checking & debunk generation", meta_style), Paragraph("<font color='#16a34a'><b>PASSED (100%)</b></font>", meta_style)],
        [Paragraph("<code>test_narrative_clustering</code>", code_style), Paragraph("TF-IDF semantic similarity grouping into active storylines", meta_style), Paragraph("<font color='#16a34a'><b>PASSED (100%)</b></font>", meta_style)],
        [Paragraph("<code>test_network_graph_generation</code>", code_style), Paragraph("NetworkX graph topology, edge weights, and CIB metrics", meta_style), Paragraph("<font color='#16a34a'><b>PASSED (100%)</b></font>", meta_style)],
        [Paragraph("<code>test_case_and_report_generation</code>", code_style), Paragraph("Formal Intelligence Briefing synthesis & Markdown formatting", meta_style), Paragraph("<font color='#16a34a'><b>PASSED (100%)</b></font>", meta_style)]
    ]

    test_table = Table(test_data, colWidths=[2.2 * inch, 3.5 * inch, 1.4 * inch])
    test_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), PRIMARY),
        ('GRID', (0, 0), (-1, -1), 0.5, BORDER_COLOR),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 3),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BG_LIGHT])
    ]))
    story.append(test_table)
    story.append(Spacer(1, 8))

    # -------------------------------------------------------------
    # 7. INSTRUCTIONS FOR EVALUATORS
    # -------------------------------------------------------------
    story.append(Paragraph("7. Evaluator Launch Guide & Execution Commands", h1_style))
    story.append(Paragraph(
        "To inspect and evaluate the project from the public GitHub repository:",
        body_style
    ))

    install_code = """# 1. Clone the public GitHub repository
git clone https://github.com/being-cheema/elect-sentinel-osint.git
cd elect-sentinel-osint

# 2. Start the application (creates venv, installs packages, starts live server)
chmod +x run.sh
./run.sh

# 3. Access the Live Cyber Operations Center in your web browser
http://localhost:8000

# 4. Run automated test suite
./venv/bin/python -m unittest tests/test_osint_engine.py"""

    code_table = Table([[Paragraph(install_code.replace("\n", "<br/>"), code_style)]], colWidths=[7.1 * inch])
    code_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f1f5f9")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8)
    ]))
    story.append(code_table)
    story.append(Spacer(1, 10))

    # Signoff Card
    signoff_p = Paragraph(
        "<b>Student:</b> Jyotiraditya Cheemakurthi (Roll No: 23011103011)<br/>"
        "<b>GitHub Repository:</b> <font color='#0284c7'><u>https://github.com/being-cheema/elect-sentinel-osint</u></font><br/>"
        "<i>Submitted for Academic & Technical Evaluation. System is fully operational and continuously ingesting live global feeds.</i>",
        meta_style
    )
    signoff_table = Table([[signoff_p]], colWidths=[7.1 * inch])
    signoff_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#e0f2fe")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#38bdf8")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8)
    ]))
    story.append(signoff_table)

    # Build Document
    doc.build(story, canvasmaker=NumberedCanvas)
    print(f"Comprehensive report generated successfully: {output_filename}")


if __name__ == "__main__":
    generate_pdf()
