#!/usr/bin/env python3
import argparse
import json
import math
import re
from collections import Counter
from pathlib import Path

import fitz


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data"

SUBJECTS = {
    "physics": {
        "label": "Physics",
        "syllabus": ROOT / "6091_y26_sy.pdf",
        "pdf_dirs": [ROOT / "2024", ROOT / "2025"],
        "syllabus_out": OUT_DIR / "syllabus.json",
        "questions_out": OUT_DIR / "questions.json",
        "topic_keywords": {
            1: "measurement si unit scalar vector vernier caliper micrometer ruler stopwatch precision accuracy magnitude prefix",
            2: "kinematics speed velocity acceleration displacement distance time graph free fall gradient area motion rest uniform",
            3: "force forces friction tension normal air resistance mass weight gravity gravitational newton inertia terminal velocity free body resultant",
            4: "moment moments pivot torque equilibrium centre gravity stability balance clockwise anticlockwise scaffold lever",
            5: "pressure hydraulic density fluid liquid column manometer atmosphere atmospheric pascal area volume height",
            6: "work power efficiency kinetic potential conservation renewable fossil nuclear solar wind hydroelectric geothermal energy store",
            7: "solid liquid gas particle particles molecule molecules atom atoms brownian random kinetic pressure states matter",
            8: "conduction convection radiation thermal equilibrium temperature heat heating insulator conductor surface colour texture",
            9: "specific heat capacity latent melting boiling evaporation condensation cooling curve internal temperature change state",
            10: "wave waves sound ultrasound echo frequency wavelength amplitude period transverse longitudinal compression rarefaction ripple",
            11: "electromagnetic spectrum radio microwave infrared visible ultraviolet xray x ray gamma wavelength frequency radiation",
            12: "light reflection refraction refractive index critical angle total internal optical fibre lens focal image ray mirror prism",
            13: "static electricity charge charges electrostatic electron electrons induction electric field precipitator attract repel coulomb",
            14: "current charge emf potential difference voltage resistance resistor ohm iv characteristic diode filament conductor circuit",
            15: "series parallel circuit circuits ammeter voltmeter resistor potentiometer thermistor ldr led branch component battery switch",
            16: "mains plug fuse fuses circuit breaker live neutral earth earthing insulation double insulation kettle appliance cable kilowatt hour",
            17: "magnet magnets magnetic field compass induced magnetism bar magnet permanent temporary iron steel pole poles",
            18: "electromagnetism solenoid current carrying conductor motor motor coil split ring commutator fleming left hand magnetic effect force",
            19: "electromagnetic induction induced emf generator transformer faraday lenz slip rings primary secondary turns high voltage transmission",
            20: "radioactivity radioactive decay isotope isotopes nuclide nucleus proton neutron nucleon alpha beta gamma half life background fission fusion radiation",
        },
    },
    "chem": {
        "label": "Chemistry",
        "syllabus": ROOT / "chem" / "6092_y26_sy.pdf",
        "pdf_dirs": [ROOT / "chem" / "2024", ROOT / "chem" / "2025"],
        "syllabus_out": OUT_DIR / "chem-syllabus.json",
        "questions_out": OUT_DIR / "chem-questions.json",
        "topic_keywords": {
            1: "apparatus burette pipette measuring cylinder gas syringe separation purification filtration crystallisation evaporation sublimation distillation fractional chromatography rf melting boiling purity solvent",
            2: "kinetic particle theory solid liquid gas diffusion atom proton neutron electron nucleus shell isotope nuclide atomic structure nucleon ion",
            3: "ionic covalent metallic bonding dot cross lattice electrostatic attraction molecule macromolecular graphite diamond graphene silicon dioxide melting boiling conductor malleable ductile",
            4: "mole molar mass relative atomic molecular formula empirical stoichiometry equation ionic equation concentration titration yield purity avogadro volume gas",
            5: "acid alkali base ph neutralisation salt ammonia ammonium carbonate sulfate chloride nitrate hydroxide solubility titration precipitation haber",
            6: "qualitative analysis sodium hydroxide aqueous ammonia precipitate cation anion gas test limewater litmus splint barium nitrate silver nitrate",
            7: "redox oxidation reduction oxidising reducing agent electron transfer oxidation state electrolysis electrolyte electrode anode cathode molten aqueous",
            8: "periodic table group period alkali metal halogen noble gas transition element reactivity series displacement rusting corrosion galvanising sacrificial protection",
            9: "energetics enthalpy exothermic endothermic activation energy energy profile bond breaking bond making heat temperature change",
            10: "rate reaction collision concentration pressure particle size temperature catalyst activation energy enzyme graph gradient volume gas",
            11: "organic alkane alkene alcohol carboxylic acid homologous series functional group saturated unsaturated hydrocarbon crude oil cracking polymerisation ester ethanol ethanoic",
            12: "air pollutant carbon monoxide nitrogen oxide sulfur dioxide ozone acid rain greenhouse carbon dioxide methane global warming carbon cycle catalytic converter cfc",
        },
    },
    "bio": {
        "label": "Biology",
        "syllabus": ROOT / "bio" / "6093_y26_sy.pdf",
        "pdf_dirs": [ROOT / "bio" / "2024", ROOT / "bio" / "2025"],
        "syllabus_out": OUT_DIR / "bio-syllabus.json",
        "questions_out": OUT_DIR / "bio-questions.json",
        "topic_keywords": {
            1: "cell wall membrane cytoplasm nucleus vacuole chloroplast mitochondria ribosome golgi endoplasmic reticulum plant animal specialised root hair red blood",
            2: "diffusion osmosis active transport concentration gradient water potential plasmolysis turgid flaccid villi root hair",
            3: "carbohydrate fat protein starch reducing sugar benedict iodine biuret ethanol enzyme active site substrate temperature ph lock key",
            4: "digestion digestive alimentary canal mouth salivary stomach duodenum pancreas liver ileum villus absorption assimilation peristalsis bile alcohol",
            5: "blood heart artery vein capillary plasma red white platelets haemoglobin oxygen cardiac cycle systole diastole coronary transfusion",
            6: "respiration breathing gas exchange alveoli trachea bronchi bronchiole diaphragm intercostal aerobic anaerobic oxygen debt tobacco nicotine tar",
            7: "excretion kidney nephron ureter bladder urethra dialysis ultrafiltration selective reabsorption urine urea nitrogenous",
            8: "homeostasis hormone endocrine insulin glucagon diabetes adh osmoregulation nervous reflex eye pupil hypothalamus temperature receptor neurone effector",
            9: "infectious disease pathogen bacteria virus influenza pneumococcal vaccine antibody antibiotic resistance transmission symptoms",
            10: "leaf xylem phloem photosynthesis transpiration translocation stomata chlorophyll limiting factor root hair sucrose vascular bundle",
            11: "ecosystem food chain food web producer consumer decomposer trophic pyramid biomass carbon cycle global warming deforestation conservation biodiversity",
            12: "dna gene chromosome nucleotide base pairing polypeptide genetic code transgenic insulin biotechnology genetic engineering",
            13: "reproduction asexual sexual mitosis meiosis gamete zygote flower pollination fertilisation seed fruit menstrual pregnancy hiv std",
            14: "inheritance allele genotype phenotype dominant recessive homozygous heterozygous monohybrid codominance sex chromosome mutation variation selection",
        },
    },
}

STOPWORDS = {
    "the", "and", "for", "with", "that", "this", "from", "into", "are", "was",
    "were", "been", "being", "have", "has", "had", "will", "would", "could",
    "should", "can", "may", "must", "about", "between", "through", "when",
    "where", "which", "what", "using", "use", "uses", "used", "new", "such",
    "e", "g", "i", "ii", "iii", "iv", "v", "vi", "vii", "able", "candidates",
    "show", "understanding", "state", "describe", "explain", "recall", "apply",
    "relationship", "relationships", "calculate", "determine", "simple",
    "situations", "solve", "related", "problems", "terms", "effect", "effects",
    "given", "examples", "including", "required", "paper", "question", "fig",
    "diagram", "diagrams", "table", "tables", "data", "marks", "mark",
}

QUESTION_START_RE = re.compile(r"^\s*(\d{1,2})\s+(?=[A-Z0-9(])")
PAGE_NO_RE = re.compile(r"^\s*\d{1,3}\s*$")
ADMIN_LINE_RE = re.compile(
    r"("
    r"turn over|"
    r"read these instructions|instructions to candidates|write your|"
    r"do not use|you may use|approved scientific calculator|"
    r"additional materials|no additional materials|multiple choice answer sheet|"
    r"class\s*/?\s*index|centre number|index number|name\s*$|"
    r"for examiner|examiner'?s use|total marks?|section [ab]\s*$|"
    r"preliminary exam(?:ination)?|secondary four|ordinary level|"
    r"this document consists|this question paper consists|printed pages?|"
    r"candidates answer|answer all questions|answer one question|question answer marks|"
    r"circle your choice|hand in|dark blue|black pen|soft pencil|"
    r"paper clips|correction fluid|staples|highlighters|"
    r"copyright|permission to reproduce|"
    r"^\s*\d+\s*(hour|h)\b|^\s*\d+\s*h\s*\d+\s*min|"
    r"\b\d+\s*(minutes?|mins?)\b"
    r")",
    re.I,
)


def normalize_text(text):
    return re.sub(r"\s+", " ", text).strip()


def clean_learning_outcome_statement(text):
    text = normalize_text(text)
    text = re.split(r"\s+SECTION\s+(?:[IVX]+|\d+)[:\s]", text, maxsplit=1)[0]
    text = re.sub(r"\s+\d{1,2}$", "", text)
    return text.rstrip(". ")


def is_admin_line(text):
    compact = normalize_text(text)
    if not compact:
        return True
    if PAGE_NO_RE.match(compact):
        return True
    if ADMIN_LINE_RE.search(compact):
        return True
    if re.fullmatch(r"[\[\]().,/\\\-\s]+", compact):
        return True
    if re.fullmatch(r"(physics|chemistry|biology|paper\s+[123]|structured and free response|multiple choice|practical)", compact, re.I):
        return True
    return False


def is_admin_question_start(text):
    rest = re.sub(r"^\s*\d{1,2}\s+", "", text).strip()
    if is_admin_line(text) or is_admin_line(rest):
        return True
    if re.match(r"^[A-Z][a-z]+ \d{4}\b", rest):
        return True
    if re.match(r"^(January|February|March|April|May|June|July|August|September|October|November|December)\b", rest, re.I):
        return True
    if re.search(r"\b(hour|minutes?|additional materials|answer sheet)\b", rest, re.I):
        return True
    return False


def clean_question_text(text):
    kept = []
    for line in text.splitlines():
        line = normalize_text(line)
        if not is_admin_line(line):
            kept.append(line)
    text = " ".join(kept)
    text = re.sub(r"\b\d{4}\s+Preliminary Exam/[^A-Z]*(?=\b[A-Z]|\b\d{1,2}\b)", " ", text, flags=re.I)
    text = re.sub(r"\b[A-Z]{2,}/\d{2}/Preliminary Examination/[^A-Z]*(?=\b[A-Z]|\b\d{1,2}\b)", " ", text, flags=re.I)
    text = re.sub(r"\b(?:[A-Z]{2,}|[A-Z][a-z]+)/(?:\d{2,4}|[A-Z][a-z]+)/(?:Preliminary|Physics|Chemistry|Biology|609[123])[^A-Z]*(?=\b[A-Z][a-z]|\b\d{1,2}\b)", " ", text)
    text = re.sub(r"\bTotal\s+Question\s+Answer\s+Marks\b", " ", text, flags=re.I)
    return re.sub(r"\s+", " ", text).strip()


def tokenize(text):
    text = text.lower()
    text = text.replace("e.m.f", "emf").replace("p.d", "pd").replace("d.c", "dc")
    tokens = re.findall(r"[a-z][a-z0-9]+|[αβγµλρΩΩ]", text)
    return [token for token in tokens if token not in STOPWORDS and len(token) > 1]


def subject_content_lines(syllabus_pdf):
    doc = fitz.open(syllabus_pdf)
    start_page = None
    end_page = len(doc)
    for index, page in enumerate(doc):
        text = page.get_text()
        if start_page is None and "SUBJECT CONTENT" in text and "SECTION" in text and "Overview" in text:
            start_page = index
        if start_page is not None and index > start_page and "SUMMARY OF KEY" in text:
            end_page = index
            break
    if start_page is None:
        raise RuntimeError(f"Could not find SUBJECT CONTENT in {syllabus_pdf}")

    raw_lines = []
    for page_index in range(start_page, end_page):
        raw_lines.extend(doc[page_index].get_text().splitlines())
    lines = [normalize_text(line) for line in raw_lines]
    return [
        line for line in lines
        if line
        and not PAGE_NO_RE.match(line)
        and not re.match(r"^609\d\s+.+\s+GCE ORDINARY LEVEL SYLLABUS$", line)
    ]


def extract_syllabus(syllabus_pdf):
    lines = subject_content_lines(syllabus_pdf)

    headings = []
    idx = 0
    while idx < len(lines):
        line = lines[idx]
        number = None
        title = None

        separate = re.match(r"^(\d{1,2})\.$", line)
        same_line = re.match(r"^(\d{1,2})\.\s+(.+)$", line)
        if separate and idx + 1 < len(lines):
            number = int(separate.group(1))
            title = lines[idx + 1]
            idx += 1
        elif same_line:
            number = int(same_line.group(1))
            title = same_line.group(2)

        if number and 1 <= number <= 25 and title and not title.lower().startswith(("candidates", "content", "learning", "section")):
            if not headings or headings[-1]["number"] != number:
                headings.append({"number": number, "title": title, "lineIndex": idx})
        idx += 1

    topics = []
    for heading_index, heading in enumerate(headings):
        number = heading["number"]
        start = heading["lineIndex"] + 1
        end = headings[heading_index + 1]["lineIndex"] if heading_index + 1 < len(headings) else len(lines)
        chunk_lines = lines[start:end]

        content = []
        in_content = False
        for line in chunk_lines:
            lower = line.lower()
            if lower == "content":
                in_content = True
                continue
            if lower.startswith("learning outcomes"):
                in_content = False
            if in_content and line != "•":
                content_line = normalize_text(line.replace("•", ""))
                if content_line:
                    content.append(content_line)

        learning_outcomes = []
        in_outcomes = False
        current_letter = None
        current_subtopic = None
        current_subtopic_title = None
        current_parts = []

        def flush_outcome():
            nonlocal current_letter, current_parts
            if current_letter and current_parts:
                statement = clean_learning_outcome_statement(" ".join(current_parts))
                code_prefix = current_subtopic or str(number)
                if statement:
                    learning_outcomes.append({
                        "code": f"{code_prefix}{current_letter}",
                        "letter": current_letter,
                        "subtopic": current_subtopic,
                        "subtopicTitle": current_subtopic_title,
                        "statement": statement,
                    })
            current_letter = None
            current_parts = []

        for line in chunk_lines:
            lower = line.lower()
            if lower.startswith("learning outcomes"):
                in_outcomes = True
                continue
            if not in_outcomes:
                continue
            if lower.startswith("candidates should be able to"):
                continue
            if re.match(r"^SECTION\s+(?:[IVX]+|\d+)", line):
                flush_outcome()
                in_outcomes = False
                continue

            subtopic = re.match(rf"^({number}\.\d+)\s+(.+)$", line)
            if subtopic:
                flush_outcome()
                current_subtopic = subtopic.group(1)
                current_subtopic_title = normalize_text(subtopic.group(2))
                continue

            outcome_start = re.match(r"^\(([a-z])\)\s*(.*)$", line)
            if outcome_start:
                flush_outcome()
                current_letter = outcome_start.group(1)
                current_parts = [outcome_start.group(2)] if outcome_start.group(2) else []
                continue

            if current_letter:
                current_parts.append(line)

        flush_outcome()

        topics.append({
            "number": number,
            "title": normalize_text(heading["title"]),
            "content": content,
            "learningOutcomes": learning_outcomes,
        })

    return topics


def line_items(page):
    items = []
    for block in page.get_text("blocks", sort=True):
        x0, y0, x1, y1, text, *_ = block
        lines = [normalize_text(line) for line in text.splitlines()]
        lines = [line for line in lines if line]
        if not lines:
            continue
        line_height = max(10, (y1 - y0) / len(lines))
        for index, line in enumerate(lines):
            ly0 = y0 + index * line_height
            ly1 = min(y1, ly0 + line_height)
            items.append({"text": line, "bbox": (x0, ly0, x1, ly1)})
    items.sort(key=lambda item: (round(item["bbox"][1], 1), item["bbox"][0]))
    return items


def find_question_starts(doc):
    starts = []
    for page_index, page in enumerate(doc):
        width = page.rect.width
        height = page.rect.height
        for item in line_items(page):
            text = item["text"]
            x0, y0, _x1, _y1 = item["bbox"]
            if y0 < 42 or y0 > height - 42:
                continue
            if PAGE_NO_RE.match(text):
                continue
            match = QUESTION_START_RE.match(text)
            if not match:
                continue
            number = int(match.group(1))
            if number < 1 or number > 80:
                continue
            if x0 > width * 0.24:
                continue
            if re.search(r"(marks?|section|paper|total|turn over|answer)", text, re.I):
                continue
            if is_admin_question_start(text):
                continue
            starts.append({
                "questionNumber": number,
                "pageIndex": page_index,
                "page": page_index + 1,
                "y": max(0, math.floor(y0) - 24),
                "bbox": [round(v, 2) for v in item["bbox"]],
                "firstLine": text,
            })
    return starts


def extract_question_text(page_texts, start, end):
    fragments = []
    end_page = end["pageIndex"] + 1 if end else min(len(page_texts), start["pageIndex"] + 2)
    for page_index in range(start["pageIndex"], end_page):
        text = page_texts[page_index] if 0 <= page_index < len(page_texts) else ""
        lines = [normalize_text(line) for line in text.splitlines()]
        lines = [line for line in lines if line and not PAGE_NO_RE.match(line)]
        fragments.append("\n".join(lines))

    text = "\n".join(fragments)
    first = re.escape(str(start["questionNumber"]))
    start_match = re.search(rf"(?m)^\s*{first}\s+", text)
    if start_match:
        text = text[start_match.start():]

    if end and end["pageIndex"] == start["pageIndex"]:
        next_num = re.escape(str(end["questionNumber"]))
        next_match = re.search(rf"(?m)^\s*{next_num}\s+", text[len(str(start["questionNumber"])) + 1:])
        if next_match:
            text = text[: len(str(start["questionNumber"])) + 1 + next_match.start()]

    return clean_question_text(text)[:1800]


def build_topic_models(topics, topic_keywords):
    models = []
    all_docs = []
    for topic in topics:
        topic_doc = " ".join([topic["title"], *topic["content"], topic_keywords.get(topic["number"], "")])
        lo_docs = []
        for lo in topic["learningOutcomes"]:
            lo_doc = " ".join([
                topic_doc,
                lo.get("subtopicTitle") or "",
                lo["statement"],
            ])
            lo_docs.append((lo, Counter(tokenize(lo_doc))))
            all_docs.append(set(tokenize(lo_doc)))
        models.append((topic, Counter(tokenize(topic_doc)), lo_docs))

    df = Counter()
    for doc_tokens in all_docs:
        for token in doc_tokens:
            df[token] += 1
    n = max(1, len(all_docs))
    idf = {token: math.log((n + 1) / (count + 1)) + 1 for token, count in df.items()}
    return models, idf


def weighted_overlap(question_tokens, model_tokens, idf):
    if not question_tokens or not model_tokens:
        return 0.0
    q_counts = Counter(question_tokens)
    score = 0.0
    for token, count in q_counts.items():
        if token in model_tokens:
            score += min(count, 3) * (1 + math.log(model_tokens[token] + 1)) * idf.get(token, 1.0)
    return score


def forced_physics_topic_number(text):
    lower = text.lower()
    rules = [
        (20, r"\b(radioactive|radioactivity|half[- ]life|isotope|isotopes|nuclide|alpha|beta|gamma|background radiation|nuclear fission|nuclear fusion)\b"),
        (16, r"\b(mains plug|live wire|neutral wire|earth wire|earthing|fuse|fuses|circuit breaker|damaged insulation|double insulation|kwh|kw h|kilowatt)\b"),
        (4, r"\b(moment|moments|pivot|clockwise|anticlockwise|principle of moments|centre of gravity|scaffold|uniform rod|uniform beam)\b"),
        (15, r"\b(series circuit|parallel circuit|potential divider|potentiometer|thermistor|light-dependent resistor|ldr|effective resistance)\b"),
        (12, r"\b(refraction|reflection|refractive index|critical angle|total internal reflection|converging lens|focal length|ray diagram|plane mirror)\b"),
        (19, r"\b(transformer|generator|electromagnetic induction|induced e\.?m\.?f|faraday|lenz|slip rings|primary coil|secondary coil)\b"),
    ]
    for topic_number, pattern in rules:
        if re.search(pattern, lower):
            return topic_number
    return None


def classify_question(text, models, idf, subject_key, topic_keywords):
    tokens = tokenize(text)
    best_topic = None
    best_topic_score = 0.0
    forced_topic = forced_physics_topic_number(text) if subject_key == "physics" else None

    for topic, topic_tokens, lo_docs in models:
        if forced_topic and topic["number"] != forced_topic:
            continue
        keyword_tokens = Counter(tokenize(topic_keywords.get(topic["number"], "")))
        topic_score = weighted_overlap(tokens, topic_tokens, idf) + weighted_overlap(tokens, keyword_tokens, idf) * 2.8
        if topic_score > best_topic_score:
            best_topic_score = topic_score
            best_topic = (topic, lo_docs)

    best_lo = None
    best_lo_score = 0.0
    if best_topic:
        topic, lo_docs = best_topic
        for lo, lo_tokens in lo_docs:
            lo_score = weighted_overlap(tokens, lo_tokens, idf)
            if lo_score > best_lo_score:
                best_lo_score = lo_score
                best_lo = lo

    confidence = min(0.98, (best_topic_score + best_lo_score) / 24) if best_topic_score else 0.0
    if confidence < 0.10:
        return {
            "topicNumber": None,
            "topicTitle": "Unclassified",
            "learningOutcomeCode": None,
            "learningOutcome": "Needs review",
            "confidence": round(confidence, 2),
        }

    return {
        "topicNumber": topic["number"],
        "topicTitle": topic["title"],
        "learningOutcomeCode": best_lo["code"] if best_lo else None,
        "learningOutcome": best_lo["statement"] if best_lo else "Needs review",
        "confidence": round(confidence, 2),
    }


def paper_kind(path):
    name = path.name.lower()
    if re.search(r"\b(ms|mark|answer|ans|solution|solutions|key)\b", name):
        return "Answer / marking scheme"
    if re.search(r"\bp1\b|paper 1|prelim_p1|phy_p1|chem_p1|bio_p1", name):
        return "Paper 1"
    if re.search(r"\bp2\b|paper 2|prelim_p2|phy_p2|chem_p2|bio_p2", name):
        return "Paper 2"
    if re.search(r"\bp3\b|paper 3|pract|preplist|prep list", name):
        return "Paper 3"
    return "Question paper"


def pdf_paths_for(config):
    paths = []
    for pdf_dir in config["pdf_dirs"]:
        if pdf_dir.exists():
            paths.extend(pdf_dir.glob("**/*.pdf"))
    return sorted(path for path in paths if path.resolve() != config["syllabus"].resolve())


def build_subject(subject_key):
    config = SUBJECTS[subject_key]
    OUT_DIR.mkdir(exist_ok=True)
    topics = extract_syllabus(config["syllabus"])
    topic_keywords = config.get("topic_keywords", {})
    models, idf = build_topic_models(topics, topic_keywords)
    questions = []
    skipped = []

    pdf_paths = pdf_paths_for(config)
    for pdf_path in pdf_paths:
        try:
            doc = fitz.open(pdf_path)
        except Exception as exc:
            skipped.append({"file": str(pdf_path.relative_to(ROOT)), "reason": str(exc)})
            continue

        starts = find_question_starts(doc)
        if not starts:
            skipped.append({"file": str(pdf_path.relative_to(ROOT)), "reason": "No question starts detected"})
            continue

        page_texts = [page.get_text() for page in doc]

        for idx, start in enumerate(starts):
            end = starts[idx + 1] if idx + 1 < len(starts) else None
            text = extract_question_text(page_texts, start, end)
            if len(text) < 24:
                continue
            classification = classify_question(text[:650], models, idf, subject_key, topic_keywords)
            rel_path = str(pdf_path.relative_to(ROOT))
            questions.append({
                "id": f"q{len(questions) + 1}",
                "subject": config["label"],
                "file": rel_path,
                "fileName": pdf_path.name,
                "year": pdf_path.parts[-2] if pdf_path.parent != ROOT else "",
                "paperKind": paper_kind(pdf_path),
                "questionNumber": start["questionNumber"],
                "page": start["page"],
                "y": start["y"],
                "bbox": start["bbox"],
                "preview": text[:520],
                **classification,
            })

    metadata = {
        "subject": config["label"],
        "sourceSyllabus": str(config["syllabus"].relative_to(ROOT)),
        "pdfCount": len(pdf_paths),
        "questionCount": len(questions),
        "skippedCount": len(skipped),
    }

    config["syllabus_out"].write_text(json.dumps(topics, ensure_ascii=False, indent=2), encoding="utf-8")
    config["questions_out"].write_text(json.dumps({
        "metadata": metadata,
        "questions": questions,
    }, ensure_ascii=False), encoding="utf-8")

    print(json.dumps(metadata, indent=2))


def main():
    parser = argparse.ArgumentParser(description="Build subject question indexes.")
    parser.add_argument("subjects", nargs="*", choices=sorted(SUBJECTS), help="Subjects to build. Defaults to all.")
    args = parser.parse_args()
    subjects = args.subjects or sorted(SUBJECTS)
    for subject in subjects:
        build_subject(subject)


if __name__ == "__main__":
    main()
