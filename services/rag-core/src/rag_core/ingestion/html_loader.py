"""HTML document loader."""
from .loader_registry import register


@register("text/html")
def load_html(source_path: str) -> str:
    """Extract plain text from an HTML file using BeautifulSoup."""
    from bs4 import BeautifulSoup

    with open(source_path, "r", encoding="utf-8") as f:
        html = f.read()
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()
    return soup.get_text(separator="\n", strip=True)
