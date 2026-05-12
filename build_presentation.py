"""Build the project presentation from FINAL.ipynb and final_report.tex.

Style: minimal academic. Off-white background, dark slate text,
single muted accent. No flash, no clip-art, no gradients.
"""

from pathlib import Path
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.dml.color import RGBColor as Color

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT = Path(r"c:/Users/leona/AppData/Local/Programs/Python/Neuro-1")
FIG = ROOT / "outputs" / "figures"
LEOFIG = ROOT / "Leo"
OUT = ROOT / "Leo" / "MICrONS_Structure_Function_Presentation.pptx"

# ---------------------------------------------------------------------------
# Palette (muted, academic)
# ---------------------------------------------------------------------------
BG = Color(0xF7, 0xF6, 0xF2)        # off-white / paper
TITLE_C = Color(0x1F, 0x2A, 0x37)   # near-black slate
BODY_C = Color(0x37, 0x41, 0x51)    # dark gray
MUTED_C = Color(0x6B, 0x72, 0x80)   # muted gray for footer
ACCENT_C = Color(0x0F, 0x4C, 0x5C)  # deep teal
RULE_C = Color(0xC9, 0xC2, 0xB6)    # warm separator line

FONT = "Calibri"

SLIDE_W, SLIDE_H = Inches(13.333), Inches(7.5)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def set_bg(slide, color=BG):
    bg = slide.background
    fill = bg.fill
    fill.solid()
    fill.fore_color.rgb = color


def add_text(slide, left, top, width, height, text,
             size=18, bold=False, color=BODY_C, align=PP_ALIGN.LEFT,
             font=FONT, anchor=MSO_ANCHOR.TOP, line_spacing=1.15):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)
    tf.vertical_anchor = anchor

    lines = text.split("\n") if isinstance(text, str) else text
    for i, line in enumerate(lines):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = align
        p.line_spacing = line_spacing
        run = p.add_run()
        run.text = line
        run.font.name = font
        run.font.size = Pt(size)
        run.font.bold = bold
        run.font.color.rgb = color
    return tb


def add_bullets(slide, left, top, width, height, items,
                size=18, color=BODY_C, font=FONT,
                line_spacing=1.25, bullet_char="—"):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)

    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.alignment = PP_ALIGN.LEFT
        p.line_spacing = line_spacing
        p.space_after = Pt(6)
        run = p.add_run()
        run.text = f"{bullet_char}  {item}"
        run.font.name = font
        run.font.size = Pt(size)
        run.font.color.rgb = color
    return tb


def add_rule(slide, left, top, width, color=RULE_C, weight=0.75):
    line = slide.shapes.add_connector(1, left, top, left + width, top)
    line.line.color.rgb = color
    line.line.width = Pt(weight)
    return line


def header(slide, title, eyebrow=None):
    """Standard slide header: small eyebrow + title + thin rule."""
    if eyebrow:
        add_text(slide, Inches(0.55), Inches(0.40), Inches(12.0), Inches(0.3),
                 eyebrow.upper(), size=11, bold=True, color=ACCENT_C)
        title_top = Inches(0.72)
    else:
        title_top = Inches(0.50)
    add_text(slide, Inches(0.55), title_top, Inches(12.2), Inches(0.7),
             title, size=28, bold=True, color=TITLE_C)
    add_rule(slide, Inches(0.55), Inches(1.45), Inches(12.2))


def footer(slide, slide_num, total):
    add_text(slide, Inches(0.55), Inches(7.10), Inches(8.0), Inches(0.3),
             "MICrONS  ·  Structure & Function in a Visual-Cortex Network",
             size=9, color=MUTED_C)
    add_text(slide, Inches(11.5), Inches(7.10), Inches(1.4), Inches(0.3),
             f"{slide_num} / {total}",
             size=9, color=MUTED_C, align=PP_ALIGN.RIGHT)


def add_image_fit(slide, path, left, top, max_w, max_h):
    """Add image scaled to fit inside the (max_w, max_h) box, preserving ratio."""
    if not Path(path).exists():
        add_text(slide, left, top, max_w, max_h,
                 f"[missing image: {Path(path).name}]",
                 size=12, color=MUTED_C, align=PP_ALIGN.CENTER,
                 anchor=MSO_ANCHOR.MIDDLE)
        return None
    pic = slide.shapes.add_picture(str(path), left, top)
    # Scale down to fit
    ratio = min(max_w / pic.width, max_h / pic.height, 1.0)
    pic.width = int(pic.width * ratio)
    pic.height = int(pic.height * ratio)
    # Center inside the box
    pic.left = int(left + (max_w - pic.width) / 2)
    pic.top = int(top + (max_h - pic.height) / 2)
    return pic


# ---------------------------------------------------------------------------
# Build deck
# ---------------------------------------------------------------------------

prs = Presentation()
prs.slide_width = SLIDE_W
prs.slide_height = SLIDE_H
BLANK = prs.slide_layouts[6]

# Total slides: will be patched after build for footer numbering.
slides_data = []   # list of (build_fn,)

# --- Slide 1: Title ---------------------------------------------------------

def slide_title():
    s = prs.slides.add_slide(BLANK)
    set_bg(s)
    add_text(s, Inches(0.8), Inches(2.2), Inches(11.8), Inches(0.35),
             "MICRONS  ·  GROUP PROJECT", size=12, bold=True, color=ACCENT_C)
    add_text(s, Inches(0.8), Inches(2.6), Inches(11.8), Inches(1.5),
             "Structure and Function in a\nMICrONS Visual-Cortex Network",
             size=42, bold=True, color=TITLE_C, line_spacing=1.05)
    add_rule(s, Inches(0.8), Inches(4.45), Inches(3.0), color=ACCENT_C, weight=1.25)
    add_text(s, Inches(0.8), Inches(4.6), Inches(11.8), Inches(0.5),
             "Does synaptic wiring predict neural activity?",
             size=18, color=BODY_C)
    add_text(s, Inches(0.8), Inches(6.4), Inches(11.8), Inches(0.4),
             "Pair-level evidence, control tests, and a topology check",
             size=12, color=MUTED_C)
    return s

slide_title()

# --- Slide 2: The Question --------------------------------------------------

def slide_question():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "The Question", eyebrow="Introduction")
    add_text(s, Inches(0.55), Inches(1.75), Inches(12.2), Inches(0.5),
             "How strongly does synaptic wiring predict neural activity?",
             size=22, bold=True, color=TITLE_C)
    add_bullets(s, Inches(0.55), Inches(2.7), Inches(12.2), Inches(4.0), [
        "Structural graphs describe possible communication pathways.",
        "Functional graphs describe co-variation in measured responses.",
        "Connectomics asks whether the first predicts the second — and in what sense.",
        "We test this at two levels: individual neuron pairs, and whole-network topology.",
    ], size=18)
    return s

slide_question()

# --- Slide 3: Background ---------------------------------------------------

def slide_background():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "Background: Like-to-Like Wiring", eyebrow="Prior Work")
    add_bullets(s, Inches(0.55), Inches(1.75), Inches(12.2), Inches(4.5), [
        "Ko et al. (2011) — neurons with similar stimulus responses are more likely to be connected in mouse V1.",
        "Cossell et al. (2015) — connection strength scales with response correlation in V1 L2/3.",
        "Ding et al. (2025) — general wiring rule across mouse visual cortex from the MICrONS data.",
        "MICrONS (2025) — first co-registered EM connectivity + calcium imaging at multi-area scale.",
    ], size=17)
    add_text(s, Inches(0.55), Inches(6.0), Inches(12.2), Inches(0.6),
             "These results frame the assignment: enrichment, not deterministic prediction.",
             size=14, color=MUTED_C)
    return s

slide_background()

# --- Slide 4: Dataset -------------------------------------------------------

def slide_dataset():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "The MICrONS Dataset", eyebrow="Data")
    add_bullets(s, Inches(0.55), Inches(1.75), Inches(12.2), Inches(4.5), [
        "Mouse visual cortex, multi-area (V1, RL, AL) and multi-layer (L2/3 — L6).",
        "Electron-microscopy reconstruction of synaptic connectivity.",
        "Two-photon calcium imaging of single-neuron responses to visual stimuli.",
        "Co-registered: every analysed neuron has both an anatomy and an activity record.",
        "Subset of proofread and functionally matched excitatory neurons used here.",
    ], size=17)
    add_text(s, Inches(0.55), Inches(6.05), Inches(12.2), Inches(0.4),
             "Two cohorts: 906 cross-scan neurons (primary) and 93 same-scan V1/L4 neurons (validation).",
             size=14, color=MUTED_C)
    return s

slide_dataset()

# --- Slide 5: Two Networks --------------------------------------------------

def slide_two_networks():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "Two Networks, Different Mathematical Objects", eyebrow="Framework")
    # Left card
    add_text(s, Inches(0.55), Inches(1.85), Inches(5.9), Inches(0.5),
             "Structural network", size=18, bold=True, color=ACCENT_C)
    add_bullets(s, Inches(0.55), Inches(2.35), Inches(5.9), Inches(4.5), [
        "Sparse — most pairs have no synapse.",
        "Directed — C[i,j] is i → j.",
        "Weighted by synapse size / count.",
        "Derived from EM reconstructions.",
    ], size=15)
    # Right card
    add_text(s, Inches(7.0), Inches(1.85), Inches(5.9), Inches(0.5),
             "Functional network", size=18, bold=True, color=ACCENT_C)
    add_bullets(s, Inches(7.0), Inches(2.35), Inches(5.9), Inches(4.5), [
        "Dense — every pair has a correlation.",
        "Symmetric — F_corr(i,j) = F_corr(j,i).",
        "Signed — correlations can be negative.",
        "Derived from oracle response vectors.",
    ], size=15)
    # Divider
    add_rule(s, Inches(6.75), Inches(2.0), Inches(0), color=RULE_C)  # noop
    line = s.shapes.add_connector(1, Inches(6.75), Inches(1.85),
                                  Inches(6.75), Inches(6.4))
    line.line.color.rgb = RULE_C
    line.line.width = Pt(0.5)
    add_text(s, Inches(0.55), Inches(6.55), Inches(12.2), Inches(0.4),
             "Comparison is not trivial: the two objects do not have the same shape, density, or sign convention.",
             size=13, color=MUTED_C)
    return s

slide_two_networks()

# --- Slide 6: Research Questions -------------------------------------------

def slide_research_questions():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "Research Questions", eyebrow="Hypotheses")
    add_text(s, Inches(0.55), Inches(1.75), Inches(12.2), Inches(0.6),
             "Primary",
             size=16, bold=True, color=ACCENT_C)
    add_text(s, Inches(0.55), Inches(2.10), Inches(12.2), Inches(0.6),
             "Are directly connected neuron pairs more functionally correlated than unconnected pairs?",
             size=18, color=TITLE_C)
    add_text(s, Inches(0.55), Inches(3.10), Inches(12.2), Inches(0.6),
             "Secondary",
             size=16, bold=True, color=ACCENT_C)
    add_bullets(s, Inches(0.55), Inches(3.45), Inches(12.2), Inches(3.5), [
        "Is the effect graded by synapse strength?",
        "Does bidirectional connectivity add a reciprocity premium?",
        "Is it robust to distance, area, layer, cell type, and orientation tuning?",
        "Does it replicate in a same-scan validation cohort?",
        "Is structural-functional alignment visible at the level of network topology?",
    ], size=16)
    return s

slide_research_questions()

# --- Slide 7: Methodology overview -----------------------------------------

def slide_method_overview():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "Methodology — Overview", eyebrow="Method")
    add_bullets(s, Inches(0.55), Inches(1.75), Inches(12.2), Inches(5.0), [
        "Cohort: 906 functionally matched excitatory neurons (primary). 93 V1/L4 neurons, scan 9.3 (validation).",
        "Functional similarity: pairwise signal correlation F_corr over shared oracle-response vectors.",
        "Structural connectivity: directed edge table; C[i,j] = synapse i → j.",
        "Pair table: 409,965 unordered pairs labelled unconnected / unidirectional / bidirectional.",
        "Attributes per pair: summed synapse size, soma-soma distance, area, layer, cell type, orientation similarity.",
        "Inference: bootstrap CIs, Mann-Whitney tests, neuron-identity permutation nulls, distance matching, logistic models.",
    ], size=15)
    return s

slide_method_overview()

# --- Slide 8: Pipeline stages ----------------------------------------------

def slide_pipeline():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "Analysis Pipeline", eyebrow="Method")
    steps = [
        ("1.", "Pair baseline",
         "Connected vs. unconnected: means, bootstrap CIs, MW tests, neuron-identity permutations."),
        ("2.", "Edge weight",
         "Spearman correlation between summed synapse size and F_corr within connected pairs."),
        ("3.", "Reciprocity",
         "Compare bidirectional, unidirectional, and unconnected groups."),
        ("4.", "Controls",
         "Distance matching, within-bin contrasts, logistic regression with distance² terms, composition stratification, orientation subset."),
        ("5.", "Topology",
         "Node-level structural degree/strength vs. mean functional coupling; matched-density thresholded graphs."),
        ("6.", "Validation",
         "93-neuron same-scan cohort with trace, signal, and noise correlation; V1/RL/AL area checks."),
    ]
    y = 1.75
    for n, name, desc in steps:
        add_text(s, Inches(0.55), Inches(y), Inches(0.45), Inches(0.45),
                 n, size=18, bold=True, color=ACCENT_C)
        add_text(s, Inches(1.05), Inches(y), Inches(2.5), Inches(0.45),
                 name, size=15, bold=True, color=TITLE_C)
        add_text(s, Inches(3.6), Inches(y), Inches(9.4), Inches(0.55),
                 desc, size=13, color=BODY_C)
        y += 0.78
    return s

slide_pipeline()

# --- Slide 9: Hypothesis map -----------------------------------------------

def slide_hypothesis_map():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "Hypothesis Map", eyebrow="Structure of the analysis")
    items = [
        ("H1", "Connected vs. unconnected", "Direct pair-level test"),
        ("H2", "Synapse strength gradient", "Edge-weight refinement"),
        ("H3", "Reciprocity", "Bidirectional premium?"),
        ("H4", "Distance control", "Geometry confound"),
        ("H5", "Composition controls", "Area, layer, cell type"),
        ("H6", "Orientation similarity", "Tuning confound"),
        ("H7", "Hub-coupling & topology", "Node-level alignment"),
        ("V",  "93-neuron validation", "Same-scan replication"),
    ]
    y = 1.80
    for tag, name, role in items:
        add_text(s, Inches(0.55), Inches(y), Inches(0.6), Inches(0.4),
                 tag, size=15, bold=True, color=ACCENT_C)
        add_text(s, Inches(1.25), Inches(y), Inches(5.0), Inches(0.4),
                 name, size=15, color=TITLE_C, bold=True)
        add_text(s, Inches(6.25), Inches(y), Inches(6.5), Inches(0.4),
                 role, size=14, color=BODY_C)
        y += 0.55
    add_text(s, Inches(0.55), Inches(6.55), Inches(12.2), Inches(0.4),
             "H1 sets the baseline. H2–H3 refine it. H4–H6 stress-test it. H7 moves to topology.",
             size=13, color=MUTED_C)
    return s

slide_hypothesis_map()

# --- Slide 10: H1 setup -----------------------------------------------------

def slide_h1_setup():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "H1 — Connected Pairs Should Be More Correlated", eyebrow="Hypothesis 1")
    add_bullets(s, Inches(0.55), Inches(1.75), Inches(12.2), Inches(4.5), [
        "Pair classes: unconnected, unidirectional, bidirectional.",
        "Metric: pairwise signal correlation F_corr.",
        "Test: mean-difference with bootstrap 95% CI and one-sided Mann–Whitney.",
        "Null: neuron-identity permutation that shuffles labels but keeps the structural graph fixed.",
        "Why this null: pair rows are not independent — each neuron appears in many pairs.",
    ], size=16)
    return s

slide_h1_setup()

# --- Slide 11: H1 result + figure ------------------------------------------

def slide_h1_result():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "H1 — Result", eyebrow="Hypothesis 1")
    add_image_fit(s, FIG / "person1_h1_h3_pair_baseline.png",
                  Inches(0.55), Inches(1.65), Inches(8.0), Inches(5.2))
    add_text(s, Inches(8.9), Inches(1.75), Inches(4.0), Inches(0.5),
             "Headline", size=14, bold=True, color=ACCENT_C)
    add_bullets(s, Inches(8.9), Inches(2.15), Inches(4.0), Inches(4.5), [
        "ΔF̄_corr = 0.0334",
        "95 % CI [0.0307, 0.0360]",
        "≈ 20.6 σ above the permutation null mean",
        "Effect is modest but consistent across the distribution",
    ], size=13)
    return s

slide_h1_result()

# --- Slide 12: H1 conclusion ------------------------------------------------

def slide_h1_conclusion():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "H1 — Conclusion", eyebrow="Hypothesis 1")
    add_text(s, Inches(0.55), Inches(1.80), Inches(12.2), Inches(0.5),
             "Connected pairs are more correlated. The effect is real but small.",
             size=20, bold=True, color=TITLE_C)
    add_bullets(s, Inches(0.55), Inches(2.65), Inches(12.2), Inches(4.0), [
        "Far outside the neuron-identity permutation null, so not a pair-dependence artefact.",
        "Population-level enrichment, not pair-deterministic prediction.",
        "Most connected pairs are still only modestly correlated.",
        "Sets the baseline that all downstream tests revisit.",
    ], size=16)
    return s

slide_h1_conclusion()

# --- Slide 13: H2 -----------------------------------------------------------

def slide_h2():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "H2 — Synapse Strength Gradient", eyebrow="Hypothesis 2")
    add_text(s, Inches(0.55), Inches(1.75), Inches(12.2), Inches(0.6),
             "Is the effect graded by anatomical edge weight, or only binary?",
             size=17, color=TITLE_C)
    add_bullets(s, Inches(0.55), Inches(2.45), Inches(12.2), Inches(3.5), [
        "Among connected pairs, Spearman ρ between summed synapse size and F_corr = 0.0686.",
        "95 % CI [0.0501, 0.0864] — positive and detectable.",
        "But small: edge weight explains a tiny fraction of pairwise correlation.",
    ], size=15)
    add_text(s, Inches(0.55), Inches(5.65), Inches(12.2), Inches(0.6),
             "Verdict",
             size=14, bold=True, color=ACCENT_C)
    add_text(s, Inches(0.55), Inches(6.00), Inches(12.2), Inches(0.8),
             "Weight refines the binary H1 result rather than replacing it.",
             size=15, color=BODY_C)
    return s

slide_h2()

# --- Slide 14: H3 -----------------------------------------------------------

def slide_h3():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "H3 — Reciprocity", eyebrow="Hypothesis 3")
    add_text(s, Inches(0.55), Inches(1.75), Inches(12.2), Inches(0.6),
             "Do bidirectional pairs gain something beyond a single one-way connection?",
             size=17, color=TITLE_C)
    add_bullets(s, Inches(0.55), Inches(2.50), Inches(12.2), Inches(3.5), [
        "Mean ordering goes as expected: bidirectional > unidirectional > unconnected.",
        "Bidirectional − unidirectional ≈ 0.0126, permutation p ≈ 0.090.",
        "The reciprocity premium is not detected at conventional significance.",
        "Restricting to V1 — V1 pairs gives the same null result.",
    ], size=15)
    add_text(s, Inches(0.55), Inches(6.0), Inches(12.2), Inches(0.5),
             "Verdict",
             size=14, bold=True, color=ACCENT_C)
    add_text(s, Inches(0.55), Inches(6.35), Inches(12.2), Inches(0.6),
             "Connectedness matters; directionality of that connection does not, in this cohort.",
             size=15, color=BODY_C)
    return s

slide_h3()

# --- Slide 15: H4 question --------------------------------------------------

def slide_h4_question():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "H4 — Distance as a Confound", eyebrow="Control")
    add_bullets(s, Inches(0.55), Inches(1.75), Inches(12.2), Inches(4.0), [
        "Cortical connection probability decays steeply with soma-soma distance.",
        "Signal correlation also decays with distance — nearby neurons see similar visual inputs.",
        "Could H1 be a side-effect of shared geometry rather than a structure-function relation?",
        "Test: distance matching, within-bin contrasts, logistic models with distance and distance².",
    ], size=16)
    return s

slide_h4_question()

# --- Slide 16: H4 figure ----------------------------------------------------

def slide_h4_result():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "H4 — Distance Matching Shrinks but Does Not Erase H1", eyebrow="Control")
    add_image_fit(s, FIG / "H4d_shrinkage.png",
                  Inches(0.55), Inches(1.65), Inches(8.0), Inches(5.2))
    add_text(s, Inches(8.9), Inches(1.75), Inches(4.0), Inches(0.5),
             "After matching", size=14, bold=True, color=ACCENT_C)
    add_bullets(s, Inches(8.9), Inches(2.15), Inches(4.0), Inches(4.5), [
        "Raw ΔF̄_corr ≈ 0.033",
        "After distance matching: 0.0186",
        "Still positive within distance bins",
        "Positive in logistic model with distance² controls",
    ], size=13)
    return s

slide_h4_result()

# --- Slide 17: H5 ----------------------------------------------------------

def slide_h5():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "H5 — Composition Controls", eyebrow="Control")
    add_image_fit(s, FIG / "H5b_joint_logistic.png",
                  Inches(0.55), Inches(1.65), Inches(7.8), Inches(5.2))
    add_text(s, Inches(8.7), Inches(1.75), Inches(4.2), Inches(0.5),
             "Joint logistic model", size=14, bold=True, color=ACCENT_C)
    add_bullets(s, Inches(8.7), Inches(2.15), Inches(4.2), Inches(4.5), [
        "Predictors: F_corr, distance, same-area, same-layer, same-cell-type.",
        "Standardised β_F_corr = 0.130, 95 % CI [0.112, 0.148].",
        "F_corr remains a positive predictor of connection probability.",
        "H1 is not just \"pairs sharing a compartment\".",
    ], size=13)
    return s

slide_h5()

# --- Slide 18: H6 ----------------------------------------------------------

def slide_h6():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "H6 — Orientation Similarity", eyebrow="Control")
    add_image_fit(s, FIG / "H6b_joint_logistic.png",
                  Inches(0.55), Inches(1.65), Inches(7.8), Inches(5.2))
    add_text(s, Inches(8.7), Inches(1.75), Inches(4.2), Inches(0.5),
             "Like-to-like check", size=14, bold=True, color=ACCENT_C)
    add_bullets(s, Inches(8.7), Inches(2.15), Inches(4.2), Inches(4.5), [
        "Well-tuned subset only.",
        "Connected pairs are slightly more orientation-similar.",
        "F_corr remains the stronger predictor when modelled jointly with ori_sim and distance.",
        "Signal correlation is broader than a single tuning axis.",
    ], size=13)
    return s

slide_h6()

# --- Slide 19: From pairs to topology --------------------------------------

def slide_topology_intro():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "From Pairs to Topology", eyebrow="Network analysis")
    add_text(s, Inches(0.55), Inches(1.75), Inches(12.2), Inches(0.6),
             "The assignment also asks whether the two networks share broader structure.",
             size=17, color=TITLE_C)
    add_bullets(s, Inches(0.55), Inches(2.55), Inches(12.2), Inches(4.0), [
        "Node-level: degree, strength, hubness, mean functional coupling.",
        "Graph-level: clustering, thresholded density, degree distribution.",
        "Conceptual mismatch: sparse directed synapses vs. dense symmetric correlations.",
        "Two strategies — (a) compare continuous node-level signals, (b) threshold the functional graph to match structural density.",
    ], size=15)
    return s

slide_topology_intro()

# --- Slide 20: H7 hub coupling ---------------------------------------------

def slide_h7_hub():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "H7 — Hub Coupling (node-level)", eyebrow="Topology")
    add_image_fit(s, FIG / "h7_hub_coupling.png",
                  Inches(0.55), Inches(1.65), Inches(8.0), Inches(5.2))
    add_text(s, Inches(8.9), Inches(1.75), Inches(4.0), Inches(0.5),
             "Headline", size=14, bold=True, color=ACCENT_C)
    add_bullets(s, Inches(8.9), Inches(2.15), Inches(4.0), Inches(4.5), [
        "Partial Spearman ρ ≈ 0.110 between total structural strength and mean signed F_corr, after distance and area controls.",
        "≈ 1 % rank variance.",
        "Weakens under stricter controls.",
        "Absent for absolute (sign-agnostic) F_corr.",
    ], size=13)
    return s

slide_h7_hub()

# --- Slide 21: topology sensitivity ----------------------------------------

def slide_topology_sensitivity():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "Thresholded Topology Sensitivity", eyebrow="Topology")
    add_image_fit(s, FIG / "h7_topology_sensitivity.png",
                  Inches(0.55), Inches(1.65), Inches(8.0), Inches(5.2))
    add_text(s, Inches(8.9), Inches(1.75), Inches(4.0), Inches(0.5),
             "Matched-density graphs", size=14, bold=True, color=ACCENT_C)
    add_bullets(s, Inches(8.9), Inches(2.15), Inches(4.0), Inches(4.5), [
        "At matched density, structural-vs-functional degree ρ = 0.008 (p = 0.805).",
        "Functional clustering exceeds structural clustering.",
        "Topology metrics depend on density, sign convention, and threshold choice.",
        "No detectable degree-level alignment.",
    ], size=13)
    return s

slide_topology_sensitivity()

# --- Slide 22: 93-neuron validation introduction ---------------------------

def slide_validation_intro():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "93-Neuron Same-Scan Validation", eyebrow="Validation")
    add_bullets(s, Inches(0.55), Inches(1.75), Inches(12.2), Inches(4.5), [
        "Same animal, same recording session — V1 layer 4, scan 9.3.",
        "Smaller cohort but tighter measurement regime: trial-level repeated stimuli available.",
        "Three correlation measures: trace, signal, residual noise.",
        "Each measure isolates a different aspect of co-firing — signal subtracts stimulus mean; noise is the residual.",
    ], size=16)
    return s

slide_validation_intro()

# --- Slide 23: validation result -------------------------------------------

def slide_validation_result():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "Validation — H1 Replicates Across Measures", eyebrow="Validation")
    add_image_fit(s, FIG / "person4_scan93_area_checks.png",
                  Inches(0.55), Inches(1.65), Inches(8.0), Inches(5.2))
    add_text(s, Inches(8.9), Inches(1.75), Inches(4.0), Inches(0.5),
             "93-neuron cohort", size=14, bold=True, color=ACCENT_C)
    add_bullets(s, Inches(8.9), Inches(2.15), Inches(4.0), Inches(4.5), [
        "Trace Δ = 0.0258, CI [0.018, 0.034]",
        "Signal Δ = 0.0529",
        "Noise Δ = 0.0466",
        "Same direction as 906-neuron H1 — independent measurement regime.",
    ], size=13)
    return s

slide_validation_result()

# --- Slide 24: signal/noise decomposition ----------------------------------

def slide_signal_noise():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "Signal vs. Noise Decomposition", eyebrow="Validation")
    add_text(s, Inches(0.55), Inches(1.75), Inches(12.2), Inches(0.5),
             "Why this matters",
             size=16, bold=True, color=ACCENT_C)
    add_bullets(s, Inches(0.55), Inches(2.20), Inches(12.2), Inches(4.5), [
        "Trace correlation mixes stimulus tuning with shared trial-to-trial noise.",
        "Signal correlation = correlation of per-stimulus means → tuning component.",
        "Noise correlation = correlation of residuals after subtracting stimulus mean → shared variability.",
        "The connected-pair effect appears in all three.",
        "Noise correlation is the strongest discriminator here: connected pairs share variability even after tuning is removed.",
    ], size=15)
    return s

slide_signal_noise()

# --- Slide 25: V1/RL/AL areas ----------------------------------------------

def slide_areas():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "V1 / RL / AL — Scope Across Areas", eyebrow="Validation")
    add_bullets(s, Inches(0.55), Inches(1.75), Inches(12.2), Inches(4.5), [
        "Cohort split: V1 = 728 neurons,  RL = 122,  AL = 56 — strongly imbalanced.",
        "V1: clear positive H1 effect.",
        "RL: positive but weaker, underpowered.",
        "AL: unresolved — confidence interval crosses zero.",
        "Cross-area pairs: positive overall.",
        "Read as exploratory: the non-V1 areas have too few neurons to draw strong claims.",
    ], size=15)
    return s

slide_areas()

# --- Slide 26: Summary table -----------------------------------------------

def slide_summary_table():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "Summary of Quantitative Results", eyebrow="Summary")
    rows = [
        ("Test", "Question", "Effect", "Verdict"),
        ("H1", "Connected vs. unconnected", "ΔF̄ = 0.0334", "Supported"),
        ("H2", "Synapse strength gradient", "ρ = 0.0686", "Supported, weak"),
        ("H3", "Bidirectional vs. unidirectional", "Δ = 0.0126, p = 0.09", "Not detected"),
        ("H4", "Distance control", "Δ = 0.0186 after matching", "Shrinks but holds"),
        ("H5", "Composition controls", "std. β = 0.130", "Holds"),
        ("H6", "Orientation control", "std. β = 0.122", "Not orientation alone"),
        ("H7", "Hub / topology alignment", "ρ ≈ 0.11; matched-deg ρ ≈ 0.008", "Narrow signal only"),
        ("V93", "Same-scan V1/L4 validation", "trace Δ = 0.0258", "Replicates H1"),
    ]
    # column widths
    col_x = [Inches(0.55), Inches(1.55), Inches(5.6), Inches(9.0), Inches(11.0)]
    col_w = [Inches(1.00), Inches(4.05), Inches(3.40), Inches(2.00), Inches(2.0)]
    y = 1.80
    row_h = 0.50
    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            is_header = (r == 0)
            add_text(s, col_x[c], Inches(y), col_w[c], Inches(row_h),
                     val,
                     size=12 if not is_header else 13,
                     bold=is_header,
                     color=TITLE_C if is_header else BODY_C)
        # underline header
        if r == 0:
            add_rule(s, Inches(0.55), Inches(y + row_h - 0.03), Inches(12.4),
                     color=ACCENT_C, weight=1.0)
        else:
            add_rule(s, Inches(0.55), Inches(y + row_h - 0.03), Inches(12.4),
                     color=RULE_C, weight=0.5)
        y += row_h
    return s

slide_summary_table()

# --- Slide 27: Discussion - two-level finding ------------------------------

def slide_discussion():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "Discussion — A Two-Level Finding", eyebrow="Interpretation")
    # Two columns
    add_text(s, Inches(0.55), Inches(1.80), Inches(5.9), Inches(0.5),
             "Pair level — positive", size=18, bold=True, color=ACCENT_C)
    add_bullets(s, Inches(0.55), Inches(2.30), Inches(5.9), Inches(4.5), [
        "Direct synaptic connection → higher expected F_corr.",
        "Survives distance, area, layer, cell-type, and orientation controls.",
        "Reads as enrichment, not deterministic prediction.",
        "Consistent with prior like-to-like wiring literature.",
    ], size=14)
    # divider
    line = s.shapes.add_connector(1, Inches(6.75), Inches(1.85),
                                  Inches(6.75), Inches(6.6))
    line.line.color.rgb = RULE_C
    line.line.width = Pt(0.5)

    add_text(s, Inches(7.0), Inches(1.80), Inches(5.9), Inches(0.5),
             "Topology level — inconclusive", size=18, bold=True, color=ACCENT_C)
    add_bullets(s, Inches(7.0), Inches(2.30), Inches(5.9), Inches(4.5), [
        "No robust hub-coupling effect under stricter controls.",
        "Matched-density degree correlations near zero.",
        "Functional clustering ≠ structural clustering.",
        "A genuine mismatch in network mathematical form, not only sampling.",
    ], size=14)
    return s

slide_discussion()

# --- Slide 28: Limitations -------------------------------------------------

def slide_limitations():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "Limitations", eyebrow="Caveats")
    add_bullets(s, Inches(0.55), Inches(1.75), Inches(12.2), Inches(5.0), [
        "Pair non-independence: every neuron appears in many pairs; permutation tests help but don't eliminate hierarchical dependence.",
        "Structural graph is a proofread, functionally matched subset — not a complete connectome.",
        "Functional graph depends on the chosen response metric (signal vs. trace vs. noise).",
        "Topology comparison is sensitive to thresholding choices.",
        "Area imbalance: claims outside V1 are exploratory.",
        "Coarse composition labels — finer cell-type or transcriptional controls were not available.",
        "Single dataset — no across-animal replication in this notebook.",
    ], size=14)
    return s

slide_limitations()

# --- Slide 29: Future Work ---------------------------------------------------

def slide_future_work():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "Future Work", eyebrow="Next steps")
    add_bullets(s, Inches(0.55), Inches(1.75), Inches(12.2), Inches(5.0), [
        "Hierarchical / mixed-effects models that absorb the per-neuron dependence directly.",
        "Axon-dendrite opportunity controls — distinguish \"could not connect\" from \"chose not to\".",
        "Richer tuning decompositions beyond orientation: spatial / temporal frequency, motion direction.",
        "Repeated animals or scans to test generalisation outside MICrONS.",
        "Spectral / community-level comparisons rather than threshold-dependent topology metrics.",
    ], size=15)
    return s

slide_future_work()

# --- Slide 30: Conclusion ---------------------------------------------------

def slide_conclusion():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "Conclusion", eyebrow="Bottom line")
    add_text(s, Inches(0.55), Inches(1.85), Inches(12.2), Inches(1.4),
             "Anatomical connectivity carries a clear pair-level\n"
             "functional signal. Broader topology matching is not detected.",
             size=24, bold=True, color=TITLE_C, line_spacing=1.2)
    add_rule(s, Inches(0.55), Inches(3.65), Inches(3.0), color=ACCENT_C, weight=1.25)
    add_bullets(s, Inches(0.55), Inches(3.95), Inches(12.2), Inches(2.8), [
        "Connected neurons are, on average, more correlated.",
        "The effect is statistically robust, quantitatively modest, and survives the controls available here.",
        "The structural and functional networks do not show topology-level equivalence.",
        "Best read as enrichment, not one-to-one prediction.",
    ], size=15)
    return s

slide_conclusion()

# --- Slide 31: References --------------------------------------------------

def slide_references():
    s = prs.slides.add_slide(BLANK); set_bg(s)
    header(s, "References", eyebrow="Bibliography")
    refs = [
        "Ko, H. et al. (2011). Functional specificity of local synaptic connections in neocortical networks. Nature 473, 87–91.",
        "Cossell, L. et al. (2015). Functional organization of excitatory synaptic strength in primary visual cortex. Nature 518, 399–403.",
        "The MICrONS Consortium (2025). Functional connectomics spanning multiple areas of mouse visual cortex. Nature 640, 435–447.",
        "Ding, Z. et al. (2025). Functional connectomics reveals general wiring rule in mouse visual cortex. Nature 640, 459–469.",
    ]
    y = 1.85
    for r in refs:
        add_text(s, Inches(0.55), Inches(y), Inches(12.2), Inches(1.2),
                 r, size=14, color=BODY_C, line_spacing=1.25)
        y += 0.95
    return s

slide_references()

# ---------------------------------------------------------------------------
# Now add footers to every slide
# ---------------------------------------------------------------------------

total = len(prs.slides)
for i, sl in enumerate(prs.slides, start=1):
    if i == 1:
        # No page number on title slide, just the project line
        add_text(sl, Inches(0.55), Inches(7.10), Inches(8.0), Inches(0.3),
                 "MICrONS  ·  Structure & Function in a Visual-Cortex Network",
                 size=9, color=MUTED_C)
        continue
    footer(sl, i, total)

prs.save(str(OUT))
print(f"Wrote {OUT}")
print(f"Total slides: {total}")
