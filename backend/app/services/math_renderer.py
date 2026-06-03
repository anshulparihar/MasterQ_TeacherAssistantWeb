import re
import io
import structlog

logger = structlog.get_logger(__name__)

# Heuristics for detecting if a string contains math that needs processing
MATH_PATTERNS = [
    r'\$\$?[^\$]+\$\$?',      # $...$ or $$...$$
    r'\\[a-zA-Z]+',           # \frac, \sqrt, \alpha, etc
    r'\^[a-zA-Z0-9\{\}\-]+',  # Superscript
    r'_[a-zA-Z0-9\{\}\-]+',   # Subscript
]

def has_math(text: str) -> bool:
    """Returns True if text contains any math expression patterns."""
    if not text:
        return False
    return any(re.search(pattern, text) for pattern in MATH_PATTERNS)

def simple_sub_super_to_reportlab(text: str) -> str:
    """
    Convert simple chemical/math notation to ReportLab XML tags.
    Runs before complex LaTeX check.
    Uses ReportLab-safe entities. Never inserts Unicode sub/super chars.
    """
    if not text:
        return ""
    
    # Process caret notation x^2 -> x<super>2</super>
    # Handle single char or braced x^{10}
    text = re.sub(r'\^\{([^}]+)\}', r'<super>\1</super>', text)
    text = re.sub(r'\^([a-zA-Z0-9\-\+])', r'<super>\1</super>', text)
    
    # Process underscore notation x_1 -> x<sub>1</sub>
    text = re.sub(r'_\{([^}]+)\}', r'<sub>\1</sub>', text)
    text = re.sub(r'_([a-zA-Z0-9])', r'<sub>\1</sub>', text)
    
    # Process standard chemical formulas loosely: H2O -> H<sub>2</sub>O
    # (Matches an uppercase letter followed by 1 or 2 digits)
    # Be careful not to replace random numbers.
    def chemical_sub(match):
        return f"{match.group(1)}<sub>{match.group(2)}</sub>"
    text = re.sub(r'([A-Z][a-z]?)([0-9]{1,2})(?![0-9A-Za-z])', chemical_sub, text)
    
    return text

def render_latex_to_png(latex_expr: str, fontsize: int = 14) -> bytes | None:
    """
    Render a LaTeX math expression to PNG bytes using matplotlib.
    """
    try:
        import matplotlib.pyplot as plt
        
        # Clean the latex expression (remove $$ or $ boundaries if present)
        clean_expr = latex_expr.strip()
        if clean_expr.startswith("$$") and clean_expr.endswith("$$"):
            clean_expr = clean_expr[2:-2]
        elif clean_expr.startswith("$") and clean_expr.endswith("$"):
            clean_expr = clean_expr[1:-1]
            
        fig, ax = plt.subplots(figsize=(0.01, 0.01))
        ax.text(0.5, 0.5, f'${clean_expr}$', fontsize=fontsize, ha='center', va='center',
                transform=ax.transAxes)
        ax.axis('off')
        
        buffer = io.BytesIO()
        plt.savefig(buffer, format='png', bbox_inches='tight', transparent=False, facecolor='white', dpi=150)
        plt.close(fig)
        return buffer.getvalue()
    except Exception as e:
        logger.error(f"Failed to render LaTeX: {latex_expr}", error=str(e))
        return None

def extract_math_segments(text: str) -> list[dict]:
    """
    Split text into segments: plain text and math blocks.
    Returns: [
      {"type": "text", "content": "The equation "},
      {"type": "math", "content": "\\frac{a}{b}", "png_bytes": bytes | None},
      ...
    ]
    """
    if not text:
        return []
        
    segments = []
    
    # Find all $...$ or $$...$$ blocks
    pattern = r'(\$\$?[^\$]+\$\$?)'
    parts = re.split(pattern, text)
    
    for part in parts:
        if not part:
            continue
            
        if part.startswith('$') and part.endswith('$'):
            # This is a math block
            png_bytes = render_latex_to_png(part)
            segments.append({
                "type": "math",
                "content": part,
                "png_bytes": png_bytes
            })
        else:
            # Plain text
            segments.append({
                "type": "text",
                "content": part
            })
            
    return segments
