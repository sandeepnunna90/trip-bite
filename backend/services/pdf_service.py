from jinja2 import Environment, FileSystemLoader
from weasyprint import HTML
import os

TEMPLATES_DIR = os.path.join(os.path.dirname(__file__), "..", "templates")


def render_trip_pdf(trip_data: dict) -> bytes:
    env = Environment(loader=FileSystemLoader(TEMPLATES_DIR))
    template = env.get_template("trip_pdf.html")
    html_content = template.render(trip=trip_data)
    pdf_bytes = HTML(string=html_content).write_pdf()
    return pdf_bytes
