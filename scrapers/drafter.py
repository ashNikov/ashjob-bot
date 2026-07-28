"""
Cover-letter drafter — Claude API.
Reads Uwem's CV once, takes a job, returns a tailored, human,
ATS-friendly cover letter. Honest about level, leads with real proof.
"""
import os
import pdfplumber
from anthropic import Anthropic
from dotenv import load_dotenv

load_dotenv()
client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

CV_PATH = os.path.join(os.path.dirname(__file__), "..", "profile", "cv.pdf")
_cv_cache = None


def cv_text():
    global _cv_cache
    if _cv_cache is None:
        with pdfplumber.open(CV_PATH) as pdf:
            _cv_cache = "\n".join(p.extract_text() or "" for p in pdf.pages)
    return _cv_cache


SYSTEM = """You are helping Uwem Udo, a self-taught DevSecOps and cloud \
security engineer in Uyo, Nigeria, write cover letters for job applications.

Rules for every letter:
- Sound like a real, thoughtful human wrote it, NOT AI-generated boilerplate. \
No "I am writing to express my interest", no "I am excited about the opportunity".
- Lead with concrete proof: his live production SaaS (AgentSec), public GitHub, \
real hands-on work. Show, do not claim.
- Mirror the specific keywords and requirements from the job description so it \
passes ATS screening, but weave them in naturally, never keyword-stuff.
- He has 3 years of hands-on experience. State it plainly if relevant; do not \
inflate beyond that.
- Keep it tight: 4 short paragraphs max. Every sentence earns its place.
- End with his name and contact (from the CV).

PUNCTUATION RULES (important for sounding human, not AI):
- Use ONLY normal punctuation: periods, commas, question marks, apostrophes, \
regular hyphens between words.
- NEVER use em-dashes or en-dashes. NEVER use curly/smart quotes. NEVER use \
semicolons or colons for dramatic effect. NEVER use the ellipsis character.
- Do not over-punctuate. Write plain, clear sentences a normal person types.

Output ONLY the letter text. No preamble, no notes."""


def draft(title: str, company: str, description: str) -> str:
    prompt = f"""Here is Uwem's CV:

{cv_text()}

---

Write a tailored cover letter for this job:

Title: {title}
Company: {company}

Job description:
{description[:4000]}

Write the letter now."""

    msg = client.messages.create(
        model="claude-sonnet-4-6",
        max_tokens=1024,
        system=SYSTEM,
        messages=[{"role": "user", "content": prompt}],
    )
    text = msg.content[0].text.strip()
    # safety net: strip any stray fancy chars if the model slips
    for bad, good in [("\u2014", "-"), ("\u2013", "-"), ("\u2019", "'"),
                      ("\u2018", "'"), ("\u201c", '"'), ("\u201d", '"'),
                      ("\u2026", "...")]:
        text = text.replace(bad, good)
    return text


if __name__ == "__main__":
    letter = draft(
        "DevOps Engineer",
        "ProctorU",
        "We need a DevOps engineer with AWS, Docker, CI/CD (GitHub Actions), "
        "Terraform, and Python. You'll manage cloud infrastructure, build "
        "deployment pipelines, and improve security posture.",
    )
    print("=" * 60)
    print(letter)
    print("=" * 60)
    print(f"\n[length: {len(letter)} chars]")
