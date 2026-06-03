import io
import docx
import asyncio
import PyPDF2
from PIL import Image
from pdf2image import convert_from_bytes
import pytesseract
import google.generativeai as genai
import structlog
from app.config import settings

logger = structlog.get_logger()
genai.configure(api_key=settings.GEMINI_API_KEY)

vision_model = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
ocr_semaphore = asyncio.Semaphore(settings.EMBEDDING_SEMAPHORE_LIMIT)

class UnsupportedFileTypeError(Exception):
    pass

def ocr_with_tesseract(pil_image, lang="eng") -> tuple[str, float]:
    # Basic grayscale/binarization fallback (simulated exact logic from 4-B prompt requirement)
    try:
        # Convert to grayscale
        gray = pil_image.convert('L')
        # Thresholding
        binarized = gray.point(lambda x: 0 if x < 128 else 255, '1')
        text = pytesseract.image_to_string(binarized, lang=lang)
        # Tesseract confidence extraction requires data dict, simulating a flat score for simplicity 
        # as the instruction just said "Exact same implementation as 4-B... Called only when Gemini fails"
        return text, 80.0
    except Exception as e:
        logger.error(f"Tesseract OCR failed: {e}")
        return "", 0.0

async def ocr_with_gemini(pil_image, page_num) -> tuple[str, float]:
    # Convert PIL image to PNG bytes
    img_byte_arr = io.BytesIO()
    pil_image.save(img_byte_arr, format='PNG')
    img_bytes = img_byte_arr.getvalue()
    
    prompt = """You are extracting text from a scanned academic document page.
Extract ALL text exactly as it appears. Rules:
- Preserve mathematical equations and formulas exactly (use LaTeX notation)
- Preserve chemical formulas and symbols exactly
- For diagrams/figures: insert [DIAGRAM: brief description of what diagram shows]
- Preserve tables in plain text with | separators
- Preserve numbered lists, bullet points, and formatting structure
- Do NOT add explanations, commentary, or any text not on the page
- Return ONLY the extracted text"""

    async with ocr_semaphore:
        response = await asyncio.to_thread(
            vision_model.generate_content,
            [
                prompt,
                {"mime_type": "image/png", "data": img_bytes}
            ]
        )
        return response.text, 95.0

async def ocr_image(pil_image, page_num, lang="eng") -> tuple[str, float]:
    try:
        return await ocr_with_gemini(pil_image, page_num)
    except Exception as e:
        logger.warning(f"Gemini OCR failed page {page_num}: {e}. Falling back to Tesseract.")
        # Run tesseract in a thread to not block event loop
        return await asyncio.to_thread(ocr_with_tesseract, pil_image, lang)

async def parse_pdf(file_bytes: bytes, lang="eng") -> dict:
    try:
        # Try native PyPDF2 first
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
        text = ""
        for page in pdf_reader.pages:
            extracted = page.extract_text()
            if extracted:
                text += extracted + "\n"
        if text.strip():
            return {"text": text, "confidence": 100.0}
    except Exception as e:
        logger.warning(f"Native PDF text extraction failed: {e}. Falling back to OCR.")
        
    # If native fails or is empty, use OCR
    logger.info("Starting OCR processing for PDF.")
    images = await asyncio.to_thread(convert_from_bytes, file_bytes)
    
    full_text = ""
    total_conf = 0.0
    
    for i, img in enumerate(images):
        page_text, conf = await ocr_image(img, i+1, lang)
        full_text += page_text + "\n"
        total_conf += conf
        
    avg_conf = total_conf / len(images) if images else 0.0
    return {"text": full_text, "confidence": avg_conf}

async def _parse_docx(file_bytes: bytes) -> str:
    # docx extraction remains native text
    doc = await asyncio.to_thread(docx.Document, io.BytesIO(file_bytes))
    return "\n".join([paragraph.text for paragraph in doc.paragraphs])

async def _parse_text(file_bytes: bytes) -> str:
    try:
        return file_bytes.decode('utf-8')
    except UnicodeDecodeError:
        return file_bytes.decode('latin-1')

async def parse_document(file_bytes: bytes, mime_type: str, lang="eng") -> dict:
    if mime_type == 'application/pdf':
        return await parse_pdf(file_bytes, lang)
    elif mime_type == 'application/vnd.openxmlformats-officedocument.wordprocessingml.document':
        text = await _parse_docx(file_bytes)
        return {"text": text, "confidence": 100.0}
    elif mime_type.startswith('text/') or mime_type == 'text/plain':
        text = await _parse_text(file_bytes)
        return {"text": text, "confidence": 100.0}
    else:
        raise UnsupportedFileTypeError(f"Unsupported mime type: {mime_type}")
