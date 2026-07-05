"""
Research tools: search, summarise, citations, gaps, report, PDF analysis.
"""
import arxiv
import pdfplumber
from agent.watsonx_client import generate
from agent.instructions import get_citation_style, get_depth_config


# ── arXiv Search ──────────────────────────────────────────────────────────────

def search_papers(query: str, max_results: int = None) -> list[dict]:
    cfg = get_depth_config()
    limit = max_results or cfg["max_papers"]
    client = arxiv.Client()
    search = arxiv.Search(query=query, max_results=limit, sort_by=arxiv.SortCriterion.Relevance)
    papers = []
    for r in client.results(search):
        papers.append({
            "title": r.title,
            "authors": [a.name for a in r.authors],
            "abstract": r.summary[:600],
            "year": r.published.year,
            "url": r.entry_id,
            "doi": getattr(r, "doi", None),
            "source": "arXiv",
        })
    return papers


# ── Summarise ─────────────────────────────────────────────────────────────────

def summarise_text(text: str, style: str = "moderate") -> str:
    length_map = {"brief": "2-3 sentences", "moderate": "1 paragraph", "detailed": "3-4 paragraphs"}
    length = length_map.get(style, "1 paragraph")
    prompt = (
        f"Summarise the following academic text in {length}. "
        f"Highlight the main contributions, methodology, and findings.\n\n"
        f"TEXT:\n{text[:4000]}"
    )
    return generate(prompt)


def summarise_paper(paper: dict) -> str:
    cfg = get_depth_config()
    text = f"Title: {paper['title']}\nAuthors: {', '.join(paper['authors'])}\nAbstract: {paper['abstract']}"
    return summarise_text(text, cfg["summary_length"])


# ── Key Insights ──────────────────────────────────────────────────────────────

def extract_insights(text: str) -> str:
    prompt = (
        "Extract 5-7 key insights from the following academic text. "
        "Present each insight as a concise bullet point.\n\n"
        f"TEXT:\n{text[:4000]}"
    )
    return generate(prompt)


# ── Citations ─────────────────────────────────────────────────────────────────

def generate_citation(paper: dict, style: str = None) -> str:
    style = style or get_citation_style()
    authors = paper.get("authors", ["Unknown Author"])
    title = paper.get("title", "Untitled")
    year = paper.get("year", "n.d.")
    url = paper.get("url", "")
    doi = paper.get("doi", "")
    source = paper.get("source", "")

    author_str = "; ".join(authors[:3]) + (" et al." if len(authors) > 3 else "")
    first_author_last = authors[0].split()[-1] if authors else "Unknown"

    if style == "APA":
        ref = f"{author_str} ({year}). *{title}*. {source}."
        if doi:
            ref += f" https://doi.org/{doi}"
        elif url:
            ref += f" {url}"
    elif style == "IEEE":
        initials = " ".join(n[0] + "." for n in authors[0].split()[:-1]) if authors else ""
        last = authors[0].split()[-1] if authors else "Unknown"
        ref = f'{initials} {last} et al., "{title}," {source}, {year}.'
        if doi:
            ref += f" doi: {doi}."
    elif style == "MLA":
        ref = f'{author_str}. "{title}." {source}, {year}.'
        if url:
            ref += f" {url}."
    else:
        ref = f"{author_str} ({year}). {title}. {source}."

    return ref


def generate_all_citations(papers: list[dict], style: str = None) -> str:
    style = style or get_citation_style()
    lines = [f"## References ({style})\n"]
    for i, p in enumerate(papers, 1):
        lines.append(f"{i}. {generate_citation(p, style)}")
    return "\n".join(lines)


# ── Research Gaps & Hypotheses ────────────────────────────────────────────────

def suggest_gaps(papers: list[dict], topic: str) -> str:
    abstracts = "\n\n".join(
        f"**{p['title']}** ({p['year']}): {p['abstract']}" for p in papers[:8]
    )
    prompt = (
        f"Based on the following research papers about '{topic}', identify:\n"
        "1. **Research Gaps** — what has NOT been studied or is under-explored?\n"
        "2. **Open Questions** — unresolved problems in this field.\n"
        "3. **Hypotheses** — 3 testable hypotheses for future research.\n\n"
        f"PAPERS:\n{abstracts}"
    )
    return generate(prompt)


# ── Structured Report ─────────────────────────────────────────────────────────

def generate_report(topic: str, papers: list[dict], extra_context: str = "") -> str:
    abstracts = "\n\n".join(
        f"- **{p['title']}** ({p['year']}): {p['abstract']}" for p in papers[:10]
    )
    prompt = (
        f"Write a structured academic research report on: **{topic}**\n\n"
        "Include the following sections:\n"
        "# 1. Introduction\n"
        "# 2. Literature Review\n"
        "# 3. Key Themes and Findings\n"
        "# 4. Research Gaps\n"
        "# 5. Conclusion\n"
        "# 6. References\n\n"
        f"Base the report on these papers:\n{abstracts}\n\n"
        f"Additional context: {extra_context}"
    )
    return generate(prompt, max_tokens=3000)


# ── PDF Analysis ──────────────────────────────────────────────────────────────

def extract_pdf_text(filepath: str) -> str:
    text = []
    with pdfplumber.open(filepath) as pdf:
        for page in pdf.pages[:30]:  # limit to 30 pages
            t = page.extract_text()
            if t:
                text.append(t)
    return "\n\n".join(text)


def analyse_pdf(filepath: str) -> dict:
    raw = extract_pdf_text(filepath)
    if not raw.strip():
        return {"error": "Could not extract text from PDF."}
    summary = summarise_text(raw, "moderate")
    insights = extract_insights(raw)
    return {
        "word_count": len(raw.split()),
        "summary": summary,
        "insights": insights,
        "raw_preview": raw[:1000],
    }


# ── Chat Q&A ──────────────────────────────────────────────────────────────────

def answer_research_question(question: str, context: str = "") -> str:
    prompt = question
    if context:
        prompt = f"Using the following context:\n{context[:3000]}\n\nAnswer: {question}"
    return generate(prompt)
