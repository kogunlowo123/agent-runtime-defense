"""PDF document loader."""
from .loader_registry import register


@register("application/pdf")
def load_pdf(source_path: str) -> str:
    """Extract plain text from a PDF file using pypdf."""
    import pypdf

    reader = pypdf.PdfReader(source_path)
    pages = []
    for page in reader.pages:
        text = page.extract_text()
        if text:
            pages.append(text)
    return "\n\n".join(pages)
