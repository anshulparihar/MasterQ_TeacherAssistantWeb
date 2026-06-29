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
# removed global genai config
from app.core.llm_wrapper import LLMWrapper
# vision_model = genai.GenerativeModel(...) # using LLMWrapper
MAX_CONCURRENT_OCR = 5
ocr_semaphore = asyncio.Semaphore(MAX_CONCURRENT_OCR)
MAX_OCR_RETRIES = 3

class UnsupportedFileTypeError(Exception):
    pass

def ocr_with_tesseract(pil_image, lang="eng") -> tuple[str, float]:
    try:
        gray = pil_image.convert('L')
        binarized = gray.point(lambda x: 0 if x < 128 else 255, '1')
        text = pytesseract.image_to_string(binarized, lang=lang)
        return text.strip(), 80.0
    except Exception as e:
        logger.error(f"Tesseract OCR failed: {e}")
        return "", 0.0

async def ocr_with_gemini(pil_image, page_num) -> tuple[str, float]:
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

    for retry in range(MAX_OCR_RETRIES):
        try:
            async with ocr_semaphore:
                response = await LLMWrapper.generate_content_async(
                    model_name=settings.GEMINI_MODEL_NAME,
                    prompt=[prompt, {"mime_type": "image/png", "data": img_bytes}],
                    stream=False
                )
                return response.text.strip(), 95.0
        except Exception as e:
            if "503" in str(e) and retry < MAX_OCR_RETRIES - 1:
                logger.warning(f"Page {page_num}: 503 error, retry {retry + 1}/{MAX_OCR_RETRIES}")
                await asyncio.sleep(1)
            else:
                raise e
    return "", 0.0

async def ocr_image(pil_image, page_num, lang="eng") -> tuple[str, float]:
    try:
        return await ocr_with_gemini(pil_image, page_num)
    except Exception as e:
        logger.warning(f"Gemini OCR failed page {page_num}: {e}. Falling back to Tesseract.")
        return await asyncio.to_thread(ocr_with_tesseract, pil_image, lang)

async def parse_pdf(file_bytes: bytes, lang="eng") -> dict:
    try:
        pdf_reader = PyPDF2.PdfReader(io.BytesIO(file_bytes))
    except Exception as e:
        raise ValueError(f"Could not read PDF: {e}")

    logger.info(f"Extracting text from PDF ({len(pdf_reader.pages)} pages)")
    
    pages_dict = {}
    ocr_pages_needed = []
    
    for i, page in enumerate(pdf_reader.pages):
        page_num = i + 1
        text = page.extract_text()
        
        if text and text.strip():
            pages_dict[page_num] = {"text": f"[PAGE {page_num}]\n{text.strip()}", "conf": 100.0}
        else:
            x_object = page.get("/Resources", {}).get("/XObject", {})
            # Need to resolve indirect objects
            try:
                images = any(obj for obj in x_object if x_object[obj].get_object().get("/Subtype") == "/Image")
            except:
                images = True # fallback assumption
                
            if images:
                ocr_pages_needed.append(page_num)
            else:
                pages_dict[page_num] = {"text": "", "conf": 100.0}

    # Parallel processing of OCR pages
    if ocr_pages_needed:
        logger.info(f"Loading {len(ocr_pages_needed)} pages for parallel OCR processing...")
        # Load images. To avoid loading huge files entirely if only some pages needed, we convert only needed pages if possible.
        # But pdf2image converts everything if no bounds given. Since we have file_bytes, converting all is easiest.
        images = await asyncio.to_thread(convert_from_bytes, file_bytes)
        
        async def process_page(p_num):
            if p_num - 1 < len(images):
                img = images[p_num - 1]
                text, conf = await ocr_image(img, p_num, lang)
                if text:
                    return p_num, {"text": f"[PAGE {p_num}]\n{text}", "conf": conf}
            return p_num, {"text": "", "conf": 0.0}
            
        tasks = [process_page(p) for p in ocr_pages_needed]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        for res in results:
            if not isinstance(res, Exception):
                p_num, data = res
                pages_dict[p_num] = data
            else:
                logger.error(f"OCR Parallel task failed: {res}")

    # Reconstruct in order
    full_text = ""
    total_conf = 0.0
    valid_pages = 0
    
    for i in range(1, len(pdf_reader.pages) + 1):
        if i in pages_dict and pages_dict[i]["text"]:
            full_text += pages_dict[i]["text"] + "\n\n"
            total_conf += pages_dict[i]["conf"]
            valid_pages += 1
            
    avg_conf = total_conf / valid_pages if valid_pages > 0 else 0.0
    return {"text": full_text.strip(), "confidence": avg_conf}

async def _parse_docx(file_bytes: bytes) -> str:
    doc = await asyncio.to_thread(docx.Document, io.BytesIO(file_bytes))
    return "\n".join([paragraph.text for paragraph in doc.paragraphs if paragraph.text.strip()])

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
