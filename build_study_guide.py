import os
import re
import glob
from bs4 import BeautifulSoup

def build_study_guide():
    # Find all 6 HTML files in order
    html_files = sorted(glob.glob("Google Professional Cloud Architect Practice Exam_Part * of 6.html"))
    if not html_files:
        print("No HTML files found! Make sure you run this script inside the SB-Google-PCA repo folder.")
        return

    questions_data = []
    seen_q_nums = set()

    for html_file in html_files:
        print(f"Parsing: {html_file} ...")
        with open(html_file, "r", encoding="utf-8", errors="ignore") as f:
            soup = BeautifulSoup(f.read(), "html.parser")

        # Find all elements that start a question header (e.g., "Question 1", "Question 102")
        # ExamCademy renders question headers with text matching "Question \d+"
        q_headers = soup.find_all(lambda tag: tag.name in ["h1", "h2", "h3", "h4", "div", "span"] 
                                  and re.match(r"^Question\s+\d+\b", tag.get_text(strip=True)))

        for header in q_headers:
            header_text = header.get_text(" ", strip=True)
            m = re.match(r"^Question\s+(\d+)\s*(?:/\s*(.*))?$", header_text)
            if not m:
                continue
            q_num = int(m.group(1))
            if q_num in seen_q_nums:
                continue

            # Walk up to the question card container
            card = header.parent
            while card and card.name != "body":
                text_check = card.get_text(" ", strip=True)
                if ("HIDE ANSWER" in text_check or "SHOW ANSWER" in text_check or "EXPLANATION" in text_check):
                    # Ensure this card doesn't contain multiple questions
                    other_qs = re.findall(r"Question\s+\d+\s*/", text_check)
                    if len(other_qs) <= 1:
                        break
                card = card.parent

            if not card or card.name == "body":
                continue

            seen_q_nums.add(q_num)

            # Extract topic title if in sibling or header
            topic = m.group(2) or ""
            if not topic:
                parent_header_text = header.parent.get_text(" ", strip=True)
                m2 = re.search(r"Question\s+\d+\s*/\s*([^\n]+)", parent_header_text)
                if m2:
                    topic = m2.group(1).strip()

            # Clone card to manipulate safely
            card_html = str(card)
            card_soup = BeautifulSoup(card_html, "html.parser")

            # Extract explanation if present
            explanation_text = ""
            for el in card_soup.find_all(lambda t: t.get_text(strip=True) == "EXPLANATION"):
                exp_container = el.parent
                if exp_container:
                    explanation_text = exp_container.get_text("\n", strip=True)
                    explanation_text = re.sub(r"^EXPLANATION\s*", "", explanation_text)
                    exp_container.decompose()
                    break

            # Remove UI buttons like HIDE ANSWER / LEARN MORE
            for btn in card_soup.find_all(["button"]):
                if "ANSWER" in btn.get_text(strip=True).upper():
                    btn.decompose()

            questions_data.append({
                "num": q_num,
                "topic": topic,
                "card_html": str(card_soup),
                "explanation": explanation_text
            })

    questions_data.sort(key=lambda x: x["num"])
    print(f"Total unique questions extracted: {len(questions_data)}")

    # Build a clean, print-ready HTML document (which you can Ctrl+P -> Save as PDF with zero header overlap)
    output_html = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<title>Google Professional Cloud Architect - Complete Study Guide (361 Questions)</title>
<style>
    body {
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        line-height: 1.5;
        color: #111;
        max-width: 900px;
        margin: 0 auto;
        padding: 20px;
        background: #fff;
    }
    h1.doc-title {
        text-align: center;
        border-bottom: 2px solid #222;
        padding-bottom: 12px;
        margin-bottom: 30px;
    }
    .question-block {
        border: 1px solid #d0d7de;
        border-radius: 8px;
        padding: 18px 22px;
        margin-bottom: 24px;
        page-break-inside: avoid;
        break-inside: avoid;
    }
    .question-block img {
        max-width: 100%;
        height: auto;
        display: block;
        margin: 12px 0;
    }
    /* Preserve yellow highlight on correct answers */
    [class*="yellow"], [class*="correct"], [style*="yellow"], [style*="#fef08a"], [style*="#fde047"], [class*="border-yellow"], [class*="bg-yellow"] {
        background-color: #fef9c3 !important;
        border: 2px solid #eab308 !important;
        font-weight: 600;
    }
    @media print {
        body { max-width: 100%; padding: 0; }
        .question-block { page-break-inside: avoid; break-inside: avoid; }
    }
</style>
</head>
<body>
<h1 class="doc-title">Google Professional Cloud Architect Practice Exam<br><small>Complete Study Guide (Questions 1 – 361)</small></h1>
"""
    for q in questions_data:
        output_html += f'<div class="question-block" id="q-{q["num"]}">\n'
        output_html += q["card_html"]
        if q["explanation"]:
            output_html += f'<div style="margin-top:12px; padding:10px 14px; background:#f6f8fa; border-left:4px solid #0969da; font-size:0.95em;"><strong>Explanation:</strong><br>{q["explanation"]}</div>\n'
        output_html += '</div>\n'

    output_html += "</body></html>"

    out_file = "Google_PCA_Complete_Study_Guide_361_Questions.html"
    with open(out_file, "w", encoding="utf-8") as f:
        f.write(output_html)

    print(f"Success! Saved clean study guide to: {out_file}")
    print("Open this file in Chrome/Edge and press Ctrl+P (Cmd+P) -> Save as PDF (with 'Background graphics' checked).")

if __name__ == "__main__":
    build_study_guide()
