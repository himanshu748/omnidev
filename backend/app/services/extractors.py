"""
Text extraction for every file type the index understands.

Images are the interesting one. macOS ships a first-class OCR engine in the
Vision framework, reachable from Python through PyObjC: on-device, free, no
model download, and measured at 42 ms per screenshot warm (647 ms on the
first call, which loads the models). That is cheap enough to OCR every image
eagerly rather than making it opt-in. It also beats Tesseract badly on UI
screenshots, which is most of what a developer's Desktop actually holds.

Scanned PDFs reuse the same path: when the text layer is empty, the page is
rasterised with Quartz and handed to Vision, so no extra dependency is
needed for that either.

Office and iWork files are zip containers, so stdlib zipfile plus a tag strip
covers them without pulling in python-docx and friends.
"""

from __future__ import annotations

import html.parser
import io
import plistlib
import re
import zipfile
from pathlib import Path

DOC_EXTS = {".md", ".markdown", ".txt", ".rst", ".pdf", ".html", ".htm", ".text"}
IMAGE_EXTS = {".png", ".jpg", ".jpeg", ".heic", ".heif", ".webp", ".tiff", ".tif", ".gif", ".bmp"}
OFFICE_EXTS = {".docx", ".pptx", ".xlsx"}
IWORK_EXTS = {".pages", ".key", ".numbers"}
EMAIL_EXTS = {".eml"}
CODE_EXTS = {
    ".py", ".js", ".jsx", ".ts", ".tsx", ".swift", ".go", ".rs", ".java",
    ".kt", ".rb", ".c", ".h", ".cpp", ".hpp", ".m", ".cs", ".php", ".css",
    ".scss", ".sql", ".sh", ".zsh", ".bash", ".yaml", ".yml", ".toml",
    ".json", ".xml", ".proto", ".graphql", ".vue", ".svelte", ".lua", ".pl",
}

ALL_TEXTLIKE_EXTS = (
    DOC_EXTS | IMAGE_EXTS | OFFICE_EXTS | IWORK_EXTS | EMAIL_EXTS | CODE_EXTS
)

# A PDF page yielding less than this is treated as scanned and gets OCR.
SCANNED_PAGE_CHAR_THRESHOLD = 50
MAX_PDF_PAGES = 100
MAX_ARCHIVE_ENTRIES = 500
OCR_MIN_CHARS = 3


class ExtractionError(ValueError):
    """The file could not be turned into text."""


# ── Vision OCR ──────────────────────────────────────────────
_vision_unavailable_reason: str | None = None


def ocr_available() -> bool:
    return _load_vision() is not None


def _load_vision():
    """Import PyObjC Vision lazily; cache the failure so we retry cheaply."""
    global _vision_unavailable_reason
    if _vision_unavailable_reason is not None:
        return None
    try:
        import Vision
        from Foundation import NSURL
        from Quartz import CIImage

        return Vision, NSURL, CIImage
    except Exception as exc:
        _vision_unavailable_reason = str(exc)
        return None


def ocr_image(path: Path) -> str:
    """Recognise text in an image with the macOS Vision framework."""
    loaded = _load_vision()
    if loaded is None:
        raise ExtractionError(
            "On-device OCR is unavailable (PyObjC Vision failed to import). "
            "Install pyobjc-framework-Vision to index images."
        )
    Vision, NSURL, CIImage = loaded
    image = CIImage.imageWithContentsOfURL_(NSURL.fileURLWithPath_(str(path)))
    if image is None:
        raise ExtractionError(f"Not a readable image: {path.name}")
    return _recognise(Vision, image)


def _recognise(Vision, ci_image) -> str:
    handler = Vision.VNImageRequestHandler.alloc().initWithCIImage_options_(ci_image, None)
    request = Vision.VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(0)  # accurate
    request.setUsesLanguageCorrection_(True)
    ok, error = handler.performRequests_error_([request], None)
    if not ok:
        raise ExtractionError(f"OCR failed: {error}")
    lines = []
    for observation in request.results() or []:
        candidates = observation.topCandidates_(1)
        if candidates and len(candidates):
            lines.append(candidates[0].string())
    return "\n".join(lines)


def _ocr_pdf_page(path: Path, page_number: int) -> str:
    """Rasterise one PDF page with Quartz and OCR it."""
    loaded = _load_vision()
    if loaded is None:
        return ""
    Vision, NSURL, CIImage = loaded
    try:
        from Quartz import (
            CGPDFDocumentCreateWithURL,
            CGPDFDocumentGetPage,
            CGPDFPageGetBoxRect,
            kCGPDFMediaBox,
        )
        import Quartz
    except Exception:
        return ""

    document = CGPDFDocumentCreateWithURL(NSURL.fileURLWithPath_(str(path)))
    if document is None:
        return ""
    page = CGPDFDocumentGetPage(document, page_number)
    if page is None:
        return ""
    rect = CGPDFPageGetBoxRect(page, kCGPDFMediaBox)
    scale = 2.0
    width = int(rect.size.width * scale)
    height = int(rect.size.height * scale)
    if width <= 0 or height <= 0 or width * height > 40_000_000:
        return ""

    color_space = Quartz.CGColorSpaceCreateDeviceRGB()
    context = Quartz.CGBitmapContextCreate(
        None, width, height, 8, 0, color_space,
        Quartz.kCGImageAlphaPremultipliedFirst | Quartz.kCGBitmapByteOrder32Little,
    )
    if context is None:
        return ""
    Quartz.CGContextSetRGBFillColor(context, 1, 1, 1, 1)
    Quartz.CGContextFillRect(context, Quartz.CGRectMake(0, 0, width, height))
    Quartz.CGContextScaleCTM(context, scale, scale)
    Quartz.CGContextTranslateCTM(context, -rect.origin.x, -rect.origin.y)
    Quartz.CGContextDrawPDFPage(context, page)
    cg_image = Quartz.CGBitmapContextCreateImage(context)
    if cg_image is None:
        return ""
    ci_image = CIImage.imageWithCGImage_(cg_image)
    try:
        return _recognise(Vision, ci_image)
    except ExtractionError:
        return ""


# ── HTML ────────────────────────────────────────────────────
class _HTMLTextParser(html.parser.HTMLParser):
    def __init__(self) -> None:
        super().__init__()
        self._parts: list[str] = []
        self._skip = 0

    def handle_starttag(self, tag, attrs):
        if tag in {"script", "style", "noscript"}:
            self._skip += 1

    def handle_endtag(self, tag):
        if tag in {"script", "style", "noscript"} and self._skip:
            self._skip -= 1

    def handle_data(self, data):
        if not self._skip:
            self._parts.append(data)

    def text(self) -> str:
        return re.sub(r"\n{3,}", "\n\n", "".join(self._parts))


def _strip_html(raw: str) -> str:
    parser = _HTMLTextParser()
    parser.feed(raw)
    return parser.text()


# ── PDF ─────────────────────────────────────────────────────
def _extract_pdf(path: Path) -> str:
    from pypdf import PdfReader

    try:
        reader = PdfReader(io.BytesIO(path.read_bytes()))
    except Exception as exc:
        raise ExtractionError(f"Unreadable PDF: {exc}") from exc

    pages: list[str] = []
    scanned_pages = 0
    for index, page in enumerate(reader.pages[:MAX_PDF_PAGES], start=1):
        try:
            text = page.extract_text() or ""
        except Exception:
            text = ""
        if len(text.strip()) < SCANNED_PAGE_CHAR_THRESHOLD and scanned_pages < 20:
            scanned_pages += 1
            ocr_text = _ocr_pdf_page(path, index)
            if len(ocr_text.strip()) > len(text.strip()):
                text = ocr_text
        pages.append(text)
    return "\n\n".join(pages)


# ── Office (OOXML) ──────────────────────────────────────────
_XML_TAG_RE = re.compile(r"<[^>]+>")
_PARA_BREAK_RE = re.compile(r"</(w:p|a:p|text:p)>")


def _xml_to_text(data: bytes) -> str:
    raw = data.decode("utf-8", errors="ignore")
    raw = _PARA_BREAK_RE.sub("\n", raw)
    text = _XML_TAG_RE.sub(" ", raw)
    text = text.replace("&amp;", "&").replace("&lt;", "<").replace("&gt;", ">")
    text = re.sub(r"[ \t]{2,}", " ", text)
    return re.sub(r"\n{3,}", "\n\n", text).strip()


def _extract_office(path: Path) -> str:
    parts: list[str] = []
    try:
        with zipfile.ZipFile(path) as archive:
            names = [
                name
                for name in archive.namelist()[:MAX_ARCHIVE_ENTRIES]
                if name.endswith(".xml")
                and (
                    name.startswith("word/")
                    or name.startswith("ppt/slides/")
                    or name.startswith("xl/")
                )
                and "rels" not in name
            ]
            for name in sorted(names):
                try:
                    parts.append(_xml_to_text(archive.read(name)))
                except Exception:
                    continue
    except (zipfile.BadZipFile, OSError) as exc:
        raise ExtractionError(f"Unreadable Office file: {exc}") from exc
    return "\n\n".join(p for p in parts if p)


def _extract_iwork(path: Path) -> str:
    """iWork bundles carry a preview PDF, which is the cheapest text source."""
    candidates = ["QuickLook/Preview.pdf", "preview.pdf"]
    try:
        if path.is_dir():
            for candidate in candidates:
                inner = path / candidate
                if inner.is_file():
                    return _extract_pdf(inner)
            return ""
        with zipfile.ZipFile(path) as archive:
            for candidate in candidates:
                if candidate in archive.namelist():
                    from pypdf import PdfReader

                    reader = PdfReader(io.BytesIO(archive.read(candidate)))
                    return "\n\n".join(
                        (page.extract_text() or "") for page in reader.pages[:MAX_PDF_PAGES]
                    )
            for name in archive.namelist()[:MAX_ARCHIVE_ENTRIES]:
                if name.endswith(".plist") and "Metadata" in name:
                    try:
                        data = plistlib.loads(archive.read(name))
                        return "\n".join(str(v) for v in data.values() if isinstance(v, str))
                    except Exception:
                        continue
    except (zipfile.BadZipFile, OSError) as exc:
        raise ExtractionError(f"Unreadable iWork file: {exc}") from exc
    return ""


def _extract_email(path: Path) -> str:
    import email
    from email import policy

    try:
        message = email.message_from_bytes(path.read_bytes(), policy=policy.default)
    except Exception as exc:
        raise ExtractionError(f"Unreadable email: {exc}") from exc
    headers = [
        f"{field}: {message.get(field, '')}"
        for field in ("From", "To", "Subject", "Date")
        if message.get(field)
    ]
    body = ""
    try:
        part = message.get_body(preferencelist=("plain", "html"))
        if part is not None:
            body = part.get_content()
            if part.get_content_type() == "text/html":
                body = _strip_html(body)
    except Exception:
        body = ""
    return "\n".join(headers) + "\n\n" + body


# ── Dispatch ────────────────────────────────────────────────
def kind_for(path: Path) -> str:
    """The chunk kind stored alongside the text, used for filters and UI."""
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTS:
        return "image"
    if suffix in CODE_EXTS:
        return "code"
    return "doc"


def is_supported(path: Path) -> bool:
    return path.suffix.lower() in ALL_TEXTLIKE_EXTS


def extract_text(path: Path) -> str:
    """
    Turn a file into plain text. Raises ExtractionError when it cannot.

    Callers must run this under file_guards.run_with_timeout and must have
    already passed file_guards.precheck, which rules out evicted files.
    """
    suffix = path.suffix.lower()
    if suffix in IMAGE_EXTS:
        text = ocr_image(path)
        if len(text.strip()) < OCR_MIN_CHARS:
            return ""
        return text
    if suffix == ".pdf":
        return _extract_pdf(path)
    if suffix in OFFICE_EXTS:
        return _extract_office(path)
    if suffix in IWORK_EXTS:
        return _extract_iwork(path)
    if suffix in EMAIL_EXTS:
        return _extract_email(path)

    try:
        raw = path.read_text(encoding="utf-8", errors="replace")
    except OSError as exc:
        raise ExtractionError(f"Could not read {path.name}: {exc}") from exc
    if suffix in {".html", ".htm"}:
        return _strip_html(raw)
    return raw
