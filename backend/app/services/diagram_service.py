import io
import json
import asyncio
from uuid import uuid4
import structlog
import google.generativeai as genai
from app.config import settings
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import schemdraw
import schemdraw.elements as elm
import cairosvg

try:
    from rdkit import Chem
    from rdkit.Chem import Draw
    RDKIT_AVAILABLE = True
except ImportError:
    RDKIT_AVAILABLE = False

logger = structlog.get_logger()
genai.configure(api_key=settings.GEMINI_API_KEY)

class DiagramGenerationService:
    
    def __init__(self):
        self.semaphore = asyncio.Semaphore(settings.LLM_SEMAPHORE_LIMIT)

        self.gemini = genai.GenerativeModel(settings.GEMINI_MODEL_NAME)
    
    async def detect_diagram_need_batch(
        self,
        questions: list[dict],
        subject: str
    ) -> list[dict]:
        """Batched diagram detection to avoid hitting 15 RPM rate limit."""
        if not questions:
            return []
            
        questions_json = json.dumps([{
            "id": i, 
            "text": q.get('question_text'), 
            "type": q.get('question_type')
        } for i, q in enumerate(questions)])
        
        prompt = f"""Subject: {subject}
Here is a list of questions:
{questions_json}

For each question, determine if it REQUIRES a diagram/figure to be clear and answerable.
Only say yes if the question explicitly mentions a diagram, or if it is impossible to understand without one.

Return JSON ONLY. It MUST be a JSON array of objects, one for each question, in the exact same order:
[
  {{
    "needs_diagram": true/false,
    "diagram_type": "math_graph|geometry|circuit|physics_vectors|data_chart|chemistry_molecule|ray_diagram|other",
    "diagram_spec": {{}},
    "fallback_to_svg": false
  }}
]

If diagram_type is ray_diagram, biology, or anything not in the list: set fallback_to_svg: true.
Do NOT include markdown formatting like ```json.
"""
        
        async with self.semaphore:
            try:
                response = await asyncio.to_thread(
                    self.gemini.generate_content,
                    prompt,
                    generation_config=genai.GenerationConfig(response_mime_type="application/json")
                )
                results = json.loads(response.text)
                if isinstance(results, list) and len(results) == len(questions):
                    return results
                else:
                    logger.error(f"Batch diagram detection returned {len(results)} items, expected {len(questions)}")
                    return [{'needs_diagram': False} for _ in questions]
            except Exception as e:
                logger.error(f"Failed to detect diagram needs: {e}")
                return [{'needs_diagram': False} for _ in questions]

    def _setup_matplotlib_style(self):
        plt.clf()
        fig = plt.figure(figsize=(5, 4), dpi=150)
        ax = fig.add_subplot(111)
        ax.set_facecolor('white')
        fig.patch.set_facecolor('white')
        plt.rcParams.update({
            'font.family': 'sans-serif',
            'font.sans-serif': ['DejaVu Sans'],
            'font.size': 10,
            'text.color': 'black',
            'axes.labelcolor': 'black',
            'xtick.color': 'black',
            'ytick.color': 'black'
        })
        return fig, ax

    def _matplotlib_to_bytes(self, fig) -> bytes:
        buf = io.BytesIO()
        fig.savefig(buf, format='png', bbox_inches='tight', facecolor='white', edgecolor='none')
        plt.close(fig)
        buf.seek(0)
        return buf.read()

    async def _matplotlib_graph(self, spec: dict) -> bytes:
        import numpy as np
        fig, ax = self._setup_matplotlib_style()
        
        if spec.get("show_grid", True):
            ax.grid(True, linestyle='--', color='gray', alpha=0.3)
        if spec.get("show_axes", True):
            ax.axhline(0, color='black', linewidth=1)
            ax.axvline(0, color='black', linewidth=1)
            
        x_range = spec.get("x_range", [-10, 10])
        x = np.linspace(x_range[0], x_range[1], 400)
        
        for func_str in spec.get("functions", []):
            try:
                safe_dict = {"x": x, "sin": np.sin, "cos": np.cos, "tan": np.tan, "exp": np.exp, "log": np.log, "pi": np.pi}
                y = eval(func_str, {"__builtins__": None}, safe_dict)
                ax.plot(x, y, color='black', linewidth=1.5)
            except Exception as e:
                logger.warning(f"Failed to plot function {func_str}: {e}")
                
        if "y_range" in spec:
            ax.set_ylim(spec["y_range"])
            
        if spec.get("x_label"): ax.set_xlabel(spec["x_label"])
        if spec.get("y_label"): ax.set_ylabel(spec["y_label"])
        if spec.get("title"): ax.set_title(spec["title"])
        
        for point in spec.get("key_points", []):
            ax.plot(point["x"], point["y"], 'ko', markersize=4)
            if "label" in point:
                ax.annotate(point["label"], (point["x"], point["y"]), xytext=(5, 5), textcoords='offset points')
                
        return self._matplotlib_to_bytes(fig)

    async def _geometry_figure(self, spec: dict) -> bytes:
        fig, ax = self._setup_matplotlib_style()
        ax.set_aspect('equal')
        ax.axis('off')
        
        for shape in spec.get("shapes", []):
            if shape["type"] in ["triangle", "polygon"]:
                vertices = shape.get("vertices", [])
                if vertices:
                    poly = patches.Polygon(vertices, closed=True, fill=False, edgecolor='black', linewidth=1.5)
                    ax.add_patch(poly)
                    labels = shape.get("labels", {})
                    for label, pt in labels.items():
                        ax.annotate(label, pt, xytext=(5, 5), textcoords='offset points', fontsize=11)
            elif shape["type"] == "circle":
                center = shape.get("center", [0,0])
                radius = shape.get("radius", 1)
                circ = patches.Circle(center, radius, fill=False, edgecolor='black', linewidth=1.5)
                ax.add_patch(circ)
            elif shape["type"] == "line":
                start = shape.get("start", [0,0])
                end = shape.get("end", [1,1])
                ax.plot([start[0], end[0]], [start[1], end[1]], color='black', linewidth=1.5)
                
        for meas in spec.get("measurements", []):
            start = meas.get("from")
            end = meas.get("to")
            label = meas.get("label")
            if start and end:
                ax.annotate(label, xy=end, xytext=start, 
                            arrowprops=dict(arrowstyle='<->', color='black'),
                            ha='center', va='center', bbox=dict(boxstyle='round,pad=0.2', fc='white', ec='none'))
                            
        for rm in spec.get("right_angle_markers", []):
            sq = patches.Rectangle((rm[0], rm[1]), 0.3, 0.3, fill=False, edgecolor='black', linewidth=1)
            ax.add_patch(sq)
            
        ax.autoscale_view()
        return self._matplotlib_to_bytes(fig)

    async def _circuit_diagram(self, spec: dict) -> bytes:
        if spec.get("connections") == "mixed" or len(spec.get("components", [])) > 5:
            return await self._gemini_svg(f"Circuit diagram: {spec.get('description', '')}", spec)
            
        try:
            d = schemdraw.Drawing()
            d.config(fontsize=12, color='black', bgcolor='white')
            
            for comp in spec.get("components", []):
                ctype = comp.get("type")
                label = comp.get("label", "")
                val = comp.get("value", "")
                lbl = f"{label}={val}" if val else label
                
                if ctype == "resistor": d += elm.Resistor().label(lbl)
                elif ctype == "battery": d += elm.Battery().label(lbl)
                elif ctype == "capacitor": d += elm.Capacitor().label(lbl)
                elif ctype == "switch": d += elm.Switch().label(lbl)
                elif ctype == "bulb": d += elm.Lamp().label(lbl)
                else: d += elm.Line().label(lbl)
                    
            return d.get_imagedata('png')
        except Exception as e:
            logger.warning(f"Schemdraw failed: {e}. Falling back to SVG.")
            return await self._gemini_svg("Circuit diagram", spec)

    async def _physics_vectors(self, spec: dict) -> bytes:
        fig, ax = self._setup_matplotlib_style()
        ax.set_aspect('equal')
        if spec.get("reference_object") == "none":
            ax.axis('off')
        else:
            ax.grid(True, linestyle='--', alpha=0.3)
            
        for vec in spec.get("vectors", []):
            start = vec.get("start", [0,0])
            end = vec.get("end", [1,1])
            dx = end[0] - start[0]
            dy = end[1] - start[1]
            style = vec.get("style", "normal")
            
            ls = '--' if style == 'resultant' else '-'
            
            ax.add_patch(patches.FancyArrow(start[0], start[1], dx, dy, 
                                            width=0.05, head_width=0.3, head_length=0.4, 
                                            color='black', linestyle=ls, length_includes_head=True))
            
            label = vec.get("label")
            if label:
                ax.annotate(label, (end[0], end[1]), xytext=(5, 5), textcoords='offset points')
                
        ax.autoscale_view()
        return self._matplotlib_to_bytes(fig)

    async def _data_chart(self, spec: dict) -> bytes:
        fig, ax = self._setup_matplotlib_style()
        chart_type = spec.get("chart_type", "bar")
        data = spec.get("data", {})
        labels = data.get("labels", [])
        values = data.get("values", [])
        
        if chart_type == "bar":
            ax.bar(labels, values, color='white', edgecolor='black', hatch='//')
        elif chart_type == "line":
            ax.plot(labels, values, marker='o', color='black', linewidth=1.5)
        elif chart_type == "pie":
            ax.pie(values, labels=labels, colors=['white']*len(values), wedgeprops=dict(edgecolor='black'))
            
        if chart_type != "pie":
            if spec.get("x_label"): ax.set_xlabel(spec["x_label"])
            if spec.get("y_label"): ax.set_ylabel(spec["y_label"])
            
        if spec.get("title"): ax.set_title(spec["title"])
        return self._matplotlib_to_bytes(fig)

    async def _chemistry_molecule(self, spec: dict) -> bytes:
        if RDKIT_AVAILABLE:
            try:
                smiles = spec.get("smiles")
                if smiles:
                    mol = Chem.MolFromSmiles(smiles)
                    if spec.get("show_hydrogens"):
                        mol = Chem.AddHs(mol)
                    img = Draw.MolToImage(mol, size=(400, 300), bg_color='white')
                    buf = io.BytesIO()
                    img.save(buf, format='PNG')
                    return buf.getvalue()
            except Exception as e:
                logger.warning(f"RDKit failed: {e}")
        
        return await self._gemini_svg("Chemical molecule", spec)

    async def _gemini_svg(self, question_text: str, diagram_spec: dict) -> bytes:
        prompt = f"""Generate clean SVG code for a diagram suitable for an academic question paper.
        
Question: {question_text}
Diagram needed: {json.dumps(diagram_spec)}

SVG requirements:
- viewBox="0 0 400 300"
- Black lines only (stroke="black"), no colors except white background
- Font: Arial, size 12-14px for labels
- Clean, minimal academic style matching CBSE/JEE question paper diagrams
- All elements clearly labeled
- No decorative elements

Return ONLY the SVG code starting with <svg> and ending with </svg>.
No explanation, no markdown, no code blocks."""

        async with self.semaphore:
            response = await asyncio.to_thread(self.gemini.generate_content, prompt)
            svg_text = response.text.strip()
            
            if svg_text.startswith("```xml"):
                svg_text = svg_text[6:-3].strip()
            elif svg_text.startswith("```svg"):
                svg_text = svg_text[6:-3].strip()
            elif svg_text.startswith("```"):
                svg_text = svg_text[3:-3].strip()
                
            png_bytes = cairosvg.svg2png(bytestring=svg_text.encode('utf-8'), dpi=300)
            return png_bytes

    async def generate_diagram(
        self,
        question_text: str,
        diagram_type: str,
        diagram_spec: dict,
        fallback_to_svg: bool
    ) -> bytes | None:
        try:
            if fallback_to_svg:
                return await self._gemini_svg(question_text, diagram_spec)
            
            generators = {
                'math_graph': self._matplotlib_graph,
                'geometry': self._geometry_figure,
                'circuit': self._circuit_diagram,
                'physics_vectors': self._physics_vectors,
                'data_chart': self._data_chart,
                'chemistry_molecule': self._chemistry_molecule,
            }
            
            fn = generators.get(diagram_type, self._gemini_svg)
            if fn == self._gemini_svg:
                return await fn(question_text, diagram_spec)
            return await fn(diagram_spec)
            
        except Exception as e:
            logger.error(f"Diagram generation failed [{diagram_type}]: {e}")
            return None

    async def generate_diagram_and_upload(
        self,
        question_text: str,
        detection: dict,
        storage_service,
        user_id: str
    ) -> str | None:
        if not detection.get('needs_diagram'):
            return None
            
        png_bytes = await self.generate_diagram(
            question_text,
            detection.get('diagram_type', 'other'),
            detection.get('diagram_spec', {}),
            detection.get('fallback_to_svg', False)
        )
        
        if not png_bytes:
            return None
            
        key = f"diagrams/{user_id}/{uuid4()}.png"
        storage_service.upload_file(
            settings.MINIO_BUCKET_USER, key, png_bytes, "image/png"
        )
        return storage_service.generate_presigned_url(settings.MINIO_BUCKET_USER, key, expires=31536000)

diagram_service = DiagramGenerationService()
