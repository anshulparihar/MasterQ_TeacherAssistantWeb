import io
import structlog
from uuid import UUID
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from fastapi import HTTPException

from app.models.question import QuestionPaper, Question, PaperDocument
from app.models.subject import Subject
from app.models.exam_type import ExamType
from app.services.storage_service import StorageService
from app.services import math_renderer

# ReportLab imports for PDF
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import inch, mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image, Table, TableStyle, PageBreak, KeepTogether, Flowable
from reportlab.lib.colors import black, darkgreen, gray
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT

# python-docx imports
from docx import Document
from docx.shared import Inches, Pt, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

logger = structlog.get_logger(__name__)

class ExportService:
    def __init__(self):
        self.storage = StorageService()
        self.math = math_renderer

    async def export_paper(
        self,
        db: AsyncSession,
        paper_id: UUID,
        user_id: UUID,
        export_format: str,
        include_answers: bool,
        include_explanations: bool,
        include_hints: bool
    ) -> tuple[bytes, str, str]:
        
        # 1. Fetch data
        paper_data = await self._fetch_paper_data(db, paper_id, user_id)
        
        # 2. Build file
        if export_format == "pdf":
            file_bytes = await self.export_pdf(paper_data, include_answers, include_explanations, include_hints)
            mime_type = "application/pdf"
            ext = "pdf"
        elif export_format == "docx":
            file_bytes = await self.export_docx(paper_data, include_answers, include_explanations, include_hints)
            mime_type = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"
            ext = "docx"
        else:
            raise HTTPException(status_code=400, detail="Invalid export format")
            
        safe_title = paper_data["paper"].title.replace(" ", "_").replace("/", "-")
        filename = f"{safe_title}_{datetime.now().strftime('%Y%m%d')}.{ext}"
        
        return file_bytes, filename, mime_type

    async def _fetch_paper_data(self, db: AsyncSession, paper_id: UUID, user_id: UUID) -> dict:
        result = await db.execute(select(QuestionPaper).where(QuestionPaper.id == paper_id))
        paper = result.scalars().first()
        
        if not paper:
            raise HTTPException(status_code=404, detail="Paper not found")
        if paper.user_id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized to access this paper")
            
        # Fetch Subject and ExamType (normally done with joinedload, doing it directly for simplicity)
        subj_res = await db.execute(select(Subject).where(Subject.id == paper.subject_id))
        subject = subj_res.scalars().first()
        
        exam_res = await db.execute(select(ExamType).where(ExamType.id == paper.exam_type_id))
        exam_type = exam_res.scalars().first()
        
        q_res = await db.execute(select(Question).where(Question.question_paper_id == paper_id))
        questions = list(q_res.scalars().all())
        
        # Organize questions
        sections = {
            "mcq": {"easy": [], "medium": [], "hard": []},
            "theory": {"easy": [], "medium": [], "hard": []}
        }
        
        for q in questions:
            if q.type in sections and q.difficulty in sections[q.type]:
                sections[q.type][q.difficulty].append(q)
                
        # Flatten ordered list
        ordered = []
        for diff in ["easy", "medium", "hard"]:
            ordered.extend(sections["mcq"][diff])
        for diff in ["easy", "medium", "hard"]:
            ordered.extend(sections["theory"][diff])
            
        # Scoring logic — read from exam guidelines JSON, not non-existent model columns
        guidelines = (exam_type.guidelines or {}) if exam_type else {}
        mcq_guidelines = guidelines.get("mcq", {})
        theory_guidelines = guidelines.get("theory", {})
        # Representative per-section mark label (used in export headers)
        mcq_marks = mcq_guidelines.get("easy", 1)
        theory_marks = theory_guidelines.get("easy", 5)
        # Total marks — prefer per-question marks stored on each Question record
        total = 0
        for q in ordered:
            if q.marks is not None:
                total += q.marks
            elif q.type == "mcq":
                total += mcq_marks
            else:
                total += theory_marks
        return {
            "paper": paper,
            "subject": subject.name if subject else "General Subject",
            "exam_type": exam_type.name if exam_type else "General Exam",
            "academic_level": "General",  # ExamType has no academic_level column
            "mcq_marks": mcq_marks,
            "theory_marks": theory_marks,
            "total_marks": total,
            "sections": sections,
            "all_questions_ordered": ordered
        }

    async def _download_diagram(self, diagram_url: str | None) -> bytes | None:
        if not diagram_url:
            return None
        try:
            import httpx
            async with httpx.AsyncClient(timeout=15.0) as client:
                response = await client.get(diagram_url)
                if response.status_code == 200:
                    return response.content
            logger.error(f"Failed to download diagram: HTTP {response.status_code}")
            return None
        except Exception as e:
            logger.error(f"Exception downloading diagram: {e}")
            return None

    # =========================================================================
    # PDF EXPORTER
    # =========================================================================
    
    async def export_pdf(self, paper_data: dict, include_answers: bool, include_explanations: bool, include_hints: bool) -> bytes:
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer, 
            pagesize=A4,
            rightMargin=72, leftMargin=72,
            topMargin=72, bottomMargin=72
        )
        
        styles = getSampleStyleSheet()
        
        title_style = ParagraphStyle('TitleStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=16, alignment=TA_CENTER, spaceAfter=6)
        sub_style = ParagraphStyle('SubStyle', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=11, alignment=TA_CENTER, spaceAfter=12)
        header_style = ParagraphStyle('SectionHeader', parent=styles['Normal'], fontName='Helvetica-Bold', fontSize=12, spaceBefore=16, spaceAfter=8)
        question_style = ParagraphStyle('Question', parent=styles['Normal'], fontName='Helvetica', fontSize=11, spaceBefore=10, spaceAfter=4)
        option_style = ParagraphStyle('Option', parent=styles['Normal'], fontName='Helvetica', fontSize=11, leftIndent=30, spaceAfter=4)
        answer_text_style = ParagraphStyle('Answer', parent=styles['Normal'], fontName='Helvetica', fontSize=10, textColor=darkgreen, spaceBefore=4, spaceAfter=4)
        hint_style = ParagraphStyle('Hint', parent=styles['Normal'], fontName='Helvetica-Oblique', fontSize=9, textColor=gray, spaceBefore=4, spaceAfter=4)
        
        elements = []
        
        # --- HEADER ---
        elements.append(Paragraph(f"{paper_data['subject']} Examination Paper", title_style))
        elements.append(Paragraph(f"{paper_data['exam_type']} | Academic Level: {paper_data['academic_level']}", sub_style))
        
        # Horizontal Rule + Meta
        data = [[f"Max Marks: {paper_data['total_marks']}", f"Date: {paper_data['paper'].created_at.strftime('%B %d, %Y')}"]]
        t = Table(data, colWidths=[3*inch, 3*inch])
        t.setStyle(TableStyle([
            ('LINEABOVE', (0,0), (-1,-1), 1, black),
            ('LINEBELOW', (0,0), (-1,-1), 1, black),
            ('ALIGN', (0,0), (0,0), 'LEFT'),
            ('ALIGN', (1,0), (1,0), 'RIGHT'),
            ('FONTNAME', (0,0), (-1,-1), 'Helvetica-Bold'),
            ('BOTTOMPADDING', (0,0), (-1,-1), 6),
            ('TOPPADDING', (0,0), (-1,-1), 6),
        ]))
        elements.append(t)
        elements.append(Spacer(1, 12))
        
        elements.append(Paragraph("General Instructions:", ParagraphStyle('', fontName='Helvetica-Bold', fontSize=10)))
        elements.append(Paragraph("1. All questions are compulsory.", styles['Normal']))
        elements.append(Paragraph("2. Marks for each question are shown in brackets [ ].", styles['Normal']))
        elements.append(Paragraph("3. Draw diagrams wherever necessary.", styles['Normal']))
        elements.append(Spacer(1, 16))
        
        # --- QUESTIONS ---
        global_q_num = 1
        
        # Process MCQ
        mcqs = []
        for diff in ["easy", "medium", "hard"]: mcqs.extend(paper_data['sections']['mcq'][diff])
        
        if mcqs:
            elements.append(Paragraph("SECTION A — MULTIPLE CHOICE QUESTIONS", header_style))
            for q in mcqs:
                q_text_processed = self.math.simple_sub_super_to_reportlab(q.text)
                q_marks = q.marks if q.marks is not None else paper_data['mcq_marks']
                marks_text = f"[{q_marks} Mark{'s' if q_marks > 1 else ''}]"
                
                # Check for LaTeX blocks
                segments = self.math.extract_math_segments(q_text_processed)
                # To simplify ReportLab inline mixing, we just inject text if no math, else fallback to raw text 
                # (Platypus Flowables inline is highly complex without raw XML). 
                # For this MVP, we will render the whole question as a Paragraph. 
                # LaTeX blocks are left as strings if not supported inline, or rendered safely using reportlab safe sub/super.
                
                # Note: ReportLab Paragraph handles <sub> and <super> perfectly.
                header_table = Table([[Paragraph(f"Q{global_q_num}. {q_text_processed}", question_style), Paragraph(marks_text, ParagraphStyle('', alignment=TA_RIGHT, fontName='Helvetica-Bold'))]], colWidths=[5*inch, 1*inch])
                header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('TOPPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 0)]))
                
                q_elements = [header_table]
                
                if getattr(q, 'diagram_url', None):
                    img_bytes = await self._download_diagram(q.diagram_url)
                    if img_bytes:
                        try:
                            from reportlab.lib.utils import ImageReader
                            img_io = io.BytesIO(img_bytes)
                            img_reader = ImageReader(img_io)
                            orig_w, orig_h = img_reader.getSize()
                            max_w = 4 * inch
                            ratio = min(max_w / orig_w, 1.0)
                            draw_w = orig_w * ratio
                            draw_h = orig_h * ratio
                            
                            img_io.seek(0)
                            rl_img = Image(img_io, width=draw_w, height=draw_h)
                            rl_img.hAlign = 'CENTER'
                            q_elements.append(Spacer(1, 8))
                            q_elements.append(rl_img)
                            q_elements.append(Spacer(1, 8))
                        except Exception as e:
                            logger.error(f"Failed to embed PDF diagram: {e}")

                if q.options:
                    for idx, opt in enumerate(q.options):
                        opt_text = self.math.simple_sub_super_to_reportlab(opt)
                        char = chr(65+idx)
                        q_elements.append(Paragraph(f"({char}) {opt_text}", option_style))
                
                elements.append(KeepTogether(q_elements))
                global_q_num += 1

        # Process Theory
        theory = []
        for diff in ["easy", "medium", "hard"]: theory.extend(paper_data['sections']['theory'][diff])
        
        if theory:
            elements.append(Spacer(1, 16))
            elements.append(Paragraph("SECTION B — THEORY / SHORT ANSWER QUESTIONS", header_style))
            for q in theory:
                q_text_processed = self.math.simple_sub_super_to_reportlab(q.text)
                q_marks = q.marks if q.marks is not None else paper_data['theory_marks']
                marks_text = f"[{q_marks} Mark{'s' if q_marks > 1 else ''}]"
                
                header_table = Table([[Paragraph(f"Q{global_q_num}. {q_text_processed}", question_style), Paragraph(marks_text, ParagraphStyle('', alignment=TA_RIGHT, fontName='Helvetica-Bold'))]], colWidths=[5*inch, 1*inch])
                header_table.setStyle(TableStyle([('VALIGN', (0,0), (-1,-1), 'TOP'), ('TOPPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 0)]))
                
                q_elements = [header_table, Spacer(1, 10)]
                
                if getattr(q, 'diagram_url', None):
                    img_bytes = await self._download_diagram(q.diagram_url)
                    if img_bytes:
                        try:
                            from reportlab.lib.utils import ImageReader
                            img_io = io.BytesIO(img_bytes)
                            img_reader = ImageReader(img_io)
                            orig_w, orig_h = img_reader.getSize()
                            max_w = 4 * inch
                            ratio = min(max_w / orig_w, 1.0)
                            draw_w = orig_w * ratio
                            draw_h = orig_h * ratio
                            
                            img_io.seek(0)
                            rl_img = Image(img_io, width=draw_w, height=draw_h)
                            rl_img.hAlign = 'CENTER'
                            q_elements.append(rl_img)
                            q_elements.append(Spacer(1, 10))
                        except Exception as e:
                            logger.error(f"Failed to embed PDF diagram: {e}")

                elements.append(KeepTogether(q_elements))
                global_q_num += 1
                
        # --- ANSWERS ---
        if include_answers:
            elements.append(PageBreak())
            elements.append(Paragraph("ANSWER KEY & SOLUTIONS", title_style))
            elements.append(Spacer(1, 16))
            
            if mcqs:
                elements.append(Paragraph("MCQ Answers:", header_style))
                grid = []
                row = []
                for idx, q in enumerate(mcqs):
                    row.append(f"Q{idx+1}: {q.correct_answer or 'N/A'}")
                    if len(row) == 5:
                        grid.append(row)
                        row = []
                if row:
                    while len(row) < 5: row.append("")
                    grid.append(row)
                
                if grid:
                    t = Table(grid, colWidths=[1.2*inch]*5)
                    t.setStyle(TableStyle([('FONTNAME', (0,0), (-1,-1), 'Helvetica'), ('ALIGN', (0,0), (-1,-1), 'LEFT')]))
                    elements.append(t)
                elements.append(Spacer(1, 16))
                
            if theory:
                elements.append(Paragraph("Theory Answers:", header_style))
                for idx, q in enumerate(theory):
                    ans_elements = [Paragraph(f"Q{len(mcqs) + idx + 1}.", ParagraphStyle('', fontName='Helvetica-Bold'))]
                    if q.model_answer:
                        ans_elements.append(Paragraph(self.math.simple_sub_super_to_reportlab(q.model_answer), answer_text_style))
                    if include_explanations and getattr(q, 'explanation', None):
                        ans_elements.append(Paragraph(f"Explanation: {self.math.simple_sub_super_to_reportlab(q.explanation)}", hint_style))
                    if include_hints and getattr(q, 'hint', None):
                        ans_elements.append(Paragraph(f"Hint: {self.math.simple_sub_super_to_reportlab(q.hint)}", hint_style))
                    ans_elements.append(Spacer(1, 8))
                    elements.append(KeepTogether(ans_elements))

        doc.build(elements)
        return buffer.getvalue()

    # =========================================================================
    # DOCX EXPORTER
    # =========================================================================

    async def export_docx(self, paper_data: dict, include_answers: bool, include_explanations: bool, include_hints: bool) -> bytes:
        doc = Document()
        
        # Set A4 Page Size
        section = doc.sections[0]
        section.page_width = Inches(8.27)
        section.page_height = Inches(11.69)
        section.top_margin = Inches(1)
        section.bottom_margin = Inches(1)
        section.left_margin = Inches(1)
        section.right_margin = Inches(1)
        
        # Styles defaults are Times New Roman natively in python-docx
        
        # Header
        p = doc.add_heading(f"{paper_data['subject']} Examination Paper", 0)
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        p = doc.add_paragraph(f"{paper_data['exam_type']} | Academic Level: {paper_data['academic_level']}")
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        
        p = doc.add_paragraph()
        p.add_run(f"Max Marks: {paper_data['total_marks']}").bold = True
        p.add_run("\t\t\t") # Tab to push right
        p.add_run(f"Date: {paper_data['paper'].created_at.strftime('%B %d, %Y')}").bold = True
        
        p = doc.add_paragraph("General Instructions:")
        p.runs[0].bold = True
        instructions = [
            "1. All questions are compulsory.",
            "2. Marks for each question are shown in brackets [ ].",
            "3. Draw diagrams wherever necessary."
        ]
        for inst in instructions:
            doc.add_paragraph(inst)
            
        doc.add_paragraph() # Spacer
        
        global_q_num = 1
        
        mcqs = []
        for diff in ["easy", "medium", "hard"]: mcqs.extend(paper_data['sections']['mcq'][diff])
        
        if mcqs:
            doc.add_heading("SECTION A — MULTIPLE CHOICE QUESTIONS", level=1)
            for q in mcqs:
                p = doc.add_paragraph()
                p.add_run(f"Q{global_q_num}. ")
                
                # Math segmentation for DOCX
                segments = self.math.extract_math_segments(q.text)
                for seg in segments:
                    if seg["type"] == "text":
                        # Prevent newline issues in python-docx
                        text_lines = seg["content"].split('\n')
                        for i, line in enumerate(text_lines):
                            if line: p.add_run(line)
                            if i < len(text_lines) - 1: p = doc.add_paragraph()
                    elif seg["type"] == "math" and seg["png_bytes"]:
                        run = p.add_run()
                        run.add_picture(io.BytesIO(seg["png_bytes"]), height=Inches(0.3))
                
                # Marks
                q_marks = q.marks if q.marks is not None else paper_data['mcq_marks']
                p.add_run(f"\t\t[{q_marks} Mark{'s' if q_marks > 1 else ''}]").bold = True
                
                if getattr(q, 'diagram_url', None):
                    img_bytes = await self._download_diagram(q.diagram_url)
                    if img_bytes:
                        try:
                            img_io = io.BytesIO(img_bytes)
                            dp = doc.add_paragraph()
                            dp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            run = dp.add_run()
                            run.add_picture(img_io, width=Inches(4))
                        except Exception as e:
                            logger.error(f"Failed to embed DOCX diagram: {e}")

                if q.options:
                    for idx, opt in enumerate(q.options):
                        opt_p = doc.add_paragraph()
                        opt_p.paragraph_format.left_indent = Inches(0.5)
                        
                        opt_segments = self.math.extract_math_segments(opt)
                        opt_p.add_run(f"({chr(65+idx)}) ")
                        for seg in opt_segments:
                            if seg["type"] == "text":
                                opt_p.add_run(seg["content"])
                            elif seg["type"] == "math" and seg["png_bytes"]:
                                run = opt_p.add_run()
                                run.add_picture(io.BytesIO(seg["png_bytes"]), height=Inches(0.2))
                global_q_num += 1

        theory = []
        for diff in ["easy", "medium", "hard"]: theory.extend(paper_data['sections']['theory'][diff])
        
        if theory:
            doc.add_heading("SECTION B — THEORY / SHORT ANSWER QUESTIONS", level=1)
            for q in theory:
                p = doc.add_paragraph()
                p.add_run(f"Q{global_q_num}. ")
                
                segments = self.math.extract_math_segments(q.text)
                for seg in segments:
                    if seg["type"] == "text":
                        text_lines = seg["content"].split('\n')
                        for i, line in enumerate(text_lines):
                            if line: p.add_run(line)
                            if i < len(text_lines) - 1: p = doc.add_paragraph()
                    elif seg["type"] == "math" and seg["png_bytes"]:
                        run = p.add_run()
                        run.add_picture(io.BytesIO(seg["png_bytes"]), height=Inches(0.3))
                
                q_marks = q.marks if q.marks is not None else paper_data['theory_marks']
                p.add_run(f"\t\t[{q_marks} Mark{'s' if q_marks > 1 else ''}]").bold = True
                
                if getattr(q, 'diagram_url', None):
                    img_bytes = await self._download_diagram(q.diagram_url)
                    if img_bytes:
                        try:
                            img_io = io.BytesIO(img_bytes)
                            dp = doc.add_paragraph()
                            dp.alignment = WD_ALIGN_PARAGRAPH.CENTER
                            run = dp.add_run()
                            run.add_picture(img_io, width=Inches(4))
                        except Exception as e:
                            logger.error(f"Failed to embed DOCX diagram: {e}")

                doc.add_paragraph() # Spacer for answer
                global_q_num += 1

        # --- ANSWERS ---
        if include_answers:
            doc.add_page_break()
            doc.add_heading("ANSWER KEY & SOLUTIONS", level=0)
            
            if mcqs:
                doc.add_heading("MCQ Answers:", level=2)
                p = doc.add_paragraph()
                for idx, q in enumerate(mcqs):
                    p.add_run(f"Q{idx+1}: {q.correct_answer or 'N/A'}\t")
                    if (idx + 1) % 5 == 0:
                        p = doc.add_paragraph()
            
            if theory:
                doc.add_heading("Theory Answers:", level=2)
                for idx, q in enumerate(theory):
                    p = doc.add_paragraph()
                    p.add_run(f"Q{len(mcqs) + idx + 1}. ").bold = True
                    
                    if q.model_answer:
                        ans_run = p.add_run(q.model_answer)
                        ans_run.font.color.rgb = RGBColor(0, 128, 0)
                        
                    if include_explanations and getattr(q, 'explanation', None):
                        exp_p = doc.add_paragraph("Explanation: " + q.explanation)
                        exp_p.runs[0].font.italic = True
                        exp_p.runs[0].font.color.rgb = RGBColor(128, 128, 128)
                        
                    if include_hints and getattr(q, 'hint', None):
                        hint_p = doc.add_paragraph("Hint: " + q.hint)
                        hint_p.runs[0].font.italic = True
                        hint_p.runs[0].font.color.rgb = RGBColor(128, 128, 128)
        
        buffer = io.BytesIO()
        doc.save(buffer)
        return buffer.getvalue()

export_service = ExportService()
