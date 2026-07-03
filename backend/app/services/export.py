import io
from datetime import datetime
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

def generate_markdown_stream(entries: list) -> io.BytesIO:
    """Generate an in-memory UTF-8 Markdown text file stream for a list of journal entries."""
    buffer = io.BytesIO()
    md_lines = []
    
    for entry in entries:
        # Format tag chips
        tags_str = ", ".join([f"#{t.name}" for t in entry.tags]) if entry.tags else "None"
        
        md_lines.append(f"# {entry.title}\n")
        md_lines.append(f"**Date:** {entry.created_at.strftime('%Y-%m-%d %H:%M')}")
        md_lines.append(f"**Mood:** {entry.mood}/5 | **Stress:** {entry.stress_level}/5 | **Energy:** {entry.energy_level}/5 | **Sleep:** {entry.sleep_hours}h")
        md_lines.append(f"**Tags:** {tags_str}\n")
        md_lines.append("---\n")
        md_lines.append(f"{entry.content}\n\n")
        
    full_text = "\n".join(md_lines)
    buffer.write(full_text.encode('utf-8'))
    buffer.seek(0)
    return buffer

def generate_pdf_stream(entries: list) -> io.BytesIO:
    """Generate an in-memory ReportLab Platypus PDF document stream for a list of journal entries."""
    buffer = io.BytesIO()
    
    # Establish document layouts with standard 0.75 in margins
    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=54,
        leftMargin=54,
        topMargin=54,
        bottomMargin=54
    )

    styles = getSampleStyleSheet()
    
    # Define custom clean styling parameters
    title_style = ParagraphStyle(
        'DocTitle',
        parent=styles['Heading1'],
        fontSize=20,
        leading=24,
        textColor=colors.HexColor('#1f2937'),
        spaceAfter=12
    )
    
    meta_style = ParagraphStyle(
        'DocMeta',
        parent=styles['Normal'],
        fontSize=9,
        leading=14,
        textColor=colors.HexColor('#4b5563'),
        spaceAfter=8
    )
    
    body_style = ParagraphStyle(
        'DocBody',
        parent=styles['Normal'],
        fontSize=11,
        leading=16,
        textColor=colors.HexColor('#111827'),
        spaceAfter=12
    )
    
    story = []
    
    for idx, entry in enumerate(entries):
        # Insert page breaks between entries (for history list downloads)
        if idx > 0:
            story.append(PageBreak())
            
        story.append(Paragraph(entry.title or "Untitled Entry", title_style))
        
        tags_str = ", ".join([f"#{t.name}" for t in entry.tags]) if entry.tags else "None"
        
        meta_html = (
            f"<b>Date:</b> {entry.created_at.strftime('%Y-%m-%d %H:%M')}<br/>"
            f"<b>Mood:</b> {entry.mood}/5 | <b>Stress:</b> {entry.stress_level}/5 | "
            f"<b>Energy:</b> {entry.energy_level}/5 | <b>Sleep:</b> {entry.sleep_hours}h<br/>"
            f"<b>Tags:</b> {tags_str}"
        )
        
        story.append(Paragraph(meta_html, meta_style))
        story.append(HRFlowable(
            width="100%", 
            thickness=1, 
            color=colors.HexColor('#e5e7eb'), 
            spaceBefore=4, 
            spaceAfter=12
        ))
        
        # Split body content by newlines to output proper Paragraph wrappers
        paragraphs = (entry.content or "").split('\n')
        for p in paragraphs:
            p_text = p.strip()
            if p_text:
                story.append(Paragraph(p_text, body_style))
            else:
                story.append(Spacer(1, 8))
                
    doc.build(story)
    buffer.seek(0)
    return buffer
