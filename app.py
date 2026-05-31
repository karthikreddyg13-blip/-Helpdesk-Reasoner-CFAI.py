"""
================================================================================
   INTELLIGENT AUTOMATED HELPDESK REASONER — Web App (Streamlit)
   For Explainable Complaint Resolution
================================================================================
   Deploy this for FREE at: https://streamlit.io/cloud
   Run locally: streamlit run app.py
================================================================================
"""

import re
import datetime
import streamlit as st

# ── Page Config ────────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Helpdesk Reasoner",
    page_icon="🤖",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=IBM+Plex+Mono:wght@400;600&family=IBM+Plex+Sans:wght@400;600;700&display=swap');

    html, body, [class*="css"] {
        font-family: 'IBM Plex Sans', sans-serif;
    }
    .main { background-color: #0e1117; }

    .header-box {
        background: linear-gradient(135deg, #1a1a2e 0%, #16213e 50%, #0f3460 100%);
        border: 1px solid #e94560;
        border-radius: 12px;
        padding: 28px 32px;
        margin-bottom: 24px;
        text-align: center;
    }
    .header-box h1 {
        font-family: 'IBM Plex Mono', monospace;
        color: #ffffff;
        font-size: 2rem;
        margin: 0 0 6px 0;
        letter-spacing: -0.5px;
    }
    .header-box p {
        color: #a0a0b0;
        margin: 0;
        font-size: 0.95rem;
    }

    .result-card {
        background: #1a1a2e;
        border: 1px solid #2a2a4a;
        border-radius: 10px;
        padding: 20px 24px;
        margin: 10px 0;
    }
    .result-card h4 {
        color: #f5a623;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.8rem;
        letter-spacing: 1.5px;
        margin: 0 0 8px 0;
        text-transform: uppercase;
    }
    .result-card .value {
        color: #ffffff;
        font-size: 1.2rem;
        font-weight: 600;
    }

    .step-box {
        background: #0d1117;
        border-left: 3px solid #e94560;
        border-radius: 0 8px 8px 0;
        padding: 10px 16px;
        margin: 6px 0;
        font-family: 'IBM Plex Mono', monospace;
        font-size: 0.82rem;
        color: #d0d0e0;
    }
    .step-box .step-num {
        color: #e94560;
        font-weight: 600;
    }

    .resolution-step {
        background: #0a1628;
        border: 1px solid #1a3a5c;
        border-radius: 8px;
        padding: 10px 16px;
        margin: 5px 0;
        color: #7dd3fc;
        font-size: 0.88rem;
    }

    .badge-high   { background:#e74c3c; color:white; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:700; }
    .badge-medium { background:#e67e22; color:white; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:700; }
    .badge-low    { background:#27ae60; color:white; padding:3px 10px; border-radius:20px; font-size:0.78rem; font-weight:700; }

    .escalation-alert {
        background: #2d0a0a;
        border: 1px solid #e74c3c;
        border-radius: 8px;
        padding: 14px 18px;
        color: #f87171;
        font-size: 0.9rem;
    }
    .escalation-ok {
        background: #0a2d1a;
        border: 1px solid #27ae60;
        border-radius: 8px;
        padding: 14px 18px;
        color: #4ade80;
        font-size: 0.9rem;
    }

    div[data-testid="stTextArea"] textarea {
        background: #0d1117 !important;
        color: #ffffff !important;
        border: 1px solid #2a2a4a !important;
        font-family: 'IBM Plex Mono', monospace !important;
        font-size: 0.9rem !important;
        border-radius: 8px !important;
    }
    div[data-testid="stButton"] > button {
        background: #e94560 !important;
        color: white !important;
        border: none !important;
        border-radius: 8px !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        padding: 12px 32px !important;
        width: 100% !important;
        transition: opacity 0.2s !important;
    }
    div[data-testid="stButton"] > button:hover { opacity: 0.85 !important; }
</style>
""", unsafe_allow_html=True)


# ================================================================================
#  KNOWLEDGE BASE
# ================================================================================

CATEGORIES = {
    "Payment Issue": {
        "keywords": ["payment","charged","refund","billing","invoice","money",
                     "deducted","transaction","fee","overcharged","double charged",
                     "failed payment","card","amount","rupees","rs"],
        "priority": "HIGH", "icon": "💳"
    },
    "Technical Error": {
        "keywords": ["error","not working","crash","bug","broken","fail","unable",
                     "cannot","login","password","otp","app","website","slow",
                     "freeze","blank","server","down","issue"],
        "priority": "HIGH", "icon": "⚙️"
    },
    "Account Issue": {
        "keywords": ["account","locked","blocked","suspended","username","verify",
                     "hacked","unauthorized","access denied","reset","delete account",
                     "deactivate","profile","security"],
        "priority": "MEDIUM", "icon": "👤"
    },
    "Delivery Delay": {
        "keywords": ["delay","late","not delivered","shipment","order","delivery",
                     "tracking","pending","stuck","dispatch","lost","missing",
                     "where is my","not arrived"],
        "priority": "MEDIUM", "icon": "🚚"
    },
    "Product Quality": {
        "keywords": ["damaged","broken","defective","wrong item","different","quality",
                     "replace","return","exchange","warranty","torn","scratched",
                     "missing parts","poor quality"],
        "priority": "MEDIUM", "icon": "📦"
    },
    "General Enquiry": {
        "keywords": ["how","what","when","where","help","information","guide",
                     "steps","policy","terms","question","explain"],
        "priority": "LOW", "icon": "❓"
    },
}

RESOLUTION_STEPS = {
    "Payment Issue"   : ["Verify transaction ID and purchase details from system","Check if payment was debited from customer account","Raise a refund/correction request in the billing system","Send confirmation email with expected timeline to customer","Follow up within 3–5 business days to confirm resolution"],
    "Technical Error" : ["Collect device info: type, OS version, app version","Ask customer to clear cache and restart the application","Check server/system status from admin dashboard","If login issue: send password reset link to registered email","If issue persists: escalate to technical team with logs"],
    "Account Issue"   : ["Verify customer identity via registered email or phone","Check account status in the admin panel","If hacked: immediately freeze account and alert security team","If locked: unlock after successful identity verification","Send confirmation to customer once account is restored"],
    "Delivery Delay"  : ["Retrieve order number and check real-time tracking status","Contact logistics/courier partner for latest update","Provide customer with expected delivery date","If significantly delayed: offer partial refund or re-dispatch","Close ticket only after customer confirms delivery"],
    "Product Quality" : ["Ask customer to share photo/video evidence of the issue","Verify purchase date and check warranty period","Approve replacement order or full refund","Arrange free pickup of the defective/wrong product","Dispatch replacement within 2 business days"],
    "General Enquiry" : ["Identify the exact topic the customer needs help with","Provide clear, step-by-step instructions","Share a help article or FAQ link if available","Confirm whether the response answered the query","Log query for FAQ update if asked frequently"],
}

ESCALATION_TEAM = {
    "Payment Issue"   : "Finance & Billing Department",
    "Technical Error" : "IT Support Team (Level 2)",
    "Account Issue"   : "Account Security Team",
    "Delivery Delay"  : "Logistics & Fulfilment Team",
    "Product Quality" : "Quality Assurance Team",
    "General Enquiry" : "Customer Support Team",
}

SLA = {"HIGH": "Within 2 hours", "MEDIUM": "Within 24 hours", "LOW": "Within 72 hours"}

STOP_WORDS = {
    "i","me","my","we","you","your","he","she","it","they","is","are","was",
    "were","am","be","been","have","has","had","do","does","did","a","an","the",
    "and","but","or","so","at","by","for","in","of","on","to","up","with","from",
    "this","that","these","very","just","also","still","get","hi","hello","dear",
    "sir","madam","please","kindly","thank"
}

SAMPLE_COMPLAINTS = {
    "💳 Double charge on order"         : "I was charged twice for order ORD-7821. Please refund Rs. 1500 immediately.",
    "⚙️ App keeps crashing"             : "The app keeps crashing every time I try to login. Very frustrated!",
    "👤 Account hacked"                 : "My account has been hacked and there are suspicious transactions I did not make.",
    "🚚 Order not delivered"            : "My delivery is 3 weeks late. Order ORD-984521 still shows pending status.",
    "📦 Received wrong product"         : "I received a completely damaged and wrong product in the box.",
    "❓ How to reset my password"       : "How do I reset my password? I forgot it completely.",
}


# ================================================================================
#  NLP + REASONING ENGINE
# ================================================================================

def score_categories(complaint_text):
    text_lower = complaint_text.lower()
    text_clean = re.sub(r"[^\w\s]", " ", text_lower)
    scores, matched = {}, {}
    for cat, data in CATEGORIES.items():
        hits, score = [], 0
        for kw in data["keywords"]:
            if kw in text_lower or kw in text_clean:
                hits.append(kw)
                score += 2 if " " in kw else 1
        scores[cat]  = score
        matched[cat] = hits
    return scores, matched

def detect_sentiment(text):
    t = text.lower()
    for w in ["angry","frustrated","ridiculous","unacceptable","worst","terrible","cheated","fraud","scam"]:
        if w in t: return "😠 ANGRY", 0.05
    for w in ["urgent","immediately","asap","emergency","right now","cannot wait","critical"]:
        if w in t: return "🚨 URGENT", 0.03
    return "😐 NEUTRAL", 0.0

def extract_entities(text):
    found = {}
    o = re.findall(r'\b(?:order|ord|ref)[:\-#]?\s*\d{4,12}\b', text, re.IGNORECASE)
    if o: found["Order ID"] = o
    a = re.findall(r'(?:rs\.?|rupees?|inr|₹)\s*[\d,]+|\b\d+\s*rupees?\b', text, re.IGNORECASE)
    if a: found["Amount"]   = a
    e = re.findall(r'\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b', text)
    if e: found["Email"]    = e
    p = re.findall(r'\b[6-9]\d{9}\b', text)
    if p: found["Phone"]    = p
    return found

def combine_cf(cf1, cf2):
    return round(cf1 + cf2 * (1 - cf1), 2)

def get_confidence_label(cf):
    if cf >= 0.85: return "🟢 VERY HIGH",   "#2ecc71"
    if cf >= 0.65: return "🟡 HIGH",         "#f5a623"
    if cf >= 0.45: return "🟠 MODERATE",     "#e67e22"
    return               "🔴 LOW",           "#e74c3c"

def analyse(complaint_text):
    scores, matched_kw = score_categories(complaint_text)
    entities           = extract_entities(complaint_text)
    sentiment, s_boost = detect_sentiment(complaint_text)

    max_score = max(scores.values()) if scores else 0
    if max_score == 0:
        best_cat = "General Enquiry"; base_cf = 0.20
    else:
        best_cat = max(scores, key=scores.get)
        base_cf  = round(min(scores[best_cat] / max_score, 1.0), 2)

    rule_cf     = 0.85 if scores[best_cat] >= 3 else 0.65 if scores[best_cat] >= 1 else 0.30
    combined_cf = min(round(combine_cf(base_cf, rule_cf) + s_boost, 2), 1.0)

    priority   = CATEGORIES[best_cat]["priority"]
    conf_label, conf_color = get_confidence_label(combined_cf)

    escalate, esc_reason = False, "Automated resolution sufficient"
    if combined_cf < 0.40:
        escalate, esc_reason = True, "Low confidence — human review needed"
    elif sentiment == "😠 ANGRY" and priority == "HIGH":
        escalate, esc_reason = True, "Angry customer + high priority — human empathy needed"

    return {
        "category"      : best_cat,
        "icon"          : CATEGORIES[best_cat]["icon"],
        "priority"      : priority,
        "sentiment"     : sentiment,
        "all_scores"    : scores,
        "matched_kw"    : matched_kw[best_cat],
        "base_cf"       : base_cf,
        "rule_cf"       : rule_cf,
        "combined_cf"   : combined_cf,
        "conf_label"    : conf_label,
        "conf_color"    : conf_color,
        "resolution"    : RESOLUTION_STEPS[best_cat],
        "escalate_to"   : ESCALATION_TEAM[best_cat],
        "sla"           : SLA[priority],
        "escalate"      : escalate,
        "esc_reason"    : esc_reason,
        "entities"      : entities,
        "word_count"    : len(complaint_text.split()),
    }


# ================================================================================
#  SESSION STATE
# ================================================================================
if "log" not in st.session_state:
    st.session_state.log = []


# ================================================================================
#  HEADER
# ================================================================================
st.markdown("""
<div class="header-box">
  <h1>🤖 Intelligent Automated Helpdesk Reasoner</h1>
  <p>AI-Powered Explainable Complaint Resolution · Rule-Based Expert System · MYCIN Certainty Factor</p>
</div>
""", unsafe_allow_html=True)


# ================================================================================
#  SIDEBAR
# ================================================================================
with st.sidebar:
    st.markdown("### 📋 Load Sample Complaint")
    sample_choice = st.selectbox("Choose a sample:", ["— type your own —"] + list(SAMPLE_COMPLAINTS.keys()))

    st.markdown("---")
    st.markdown("### 📚 How it Works")
    st.markdown("""
**Step 1 — NLP**  
Cleans text, removes stop words, scores each complaint category by keyword matches.

**Step 2 — CF Reasoning**  
Applies MYCIN Certainty Factor formula:
```
CF = CF1 + CF2 × (1 - CF1)
```

**Step 3 — Decision**  
Selects category, resolution path, priority, and escalation decision.

**Step 4 — Explanation**  
Shows full 8-step reasoning chain.
""")

    st.markdown("---")
    st.markdown("### 🏷️ Categories")
    for cat, data in CATEGORIES.items():
        badge_class = f"badge-{data['priority'].lower()}"
        st.markdown(f"{data['icon']} **{cat}** — `{data['priority']}`")

    st.markdown("---")
    if st.session_state.log:
        st.markdown(f"### 📊 Session: `{len(st.session_state.log)}` analysed")
        cats = [r["category"] for r in st.session_state.log]
        for cat in set(cats):
            st.markdown(f"- {CATEGORIES[cat]['icon']} {cat}: **{cats.count(cat)}**")


# ================================================================================
#  MAIN INPUT AREA
# ================================================================================
col_in, col_out = st.columns([1, 1], gap="large")

with col_in:
    st.markdown("#### 📝 Enter Complaint")

    # Auto-fill from sample
    default_text = ""
    if sample_choice != "— type your own —":
        default_text = SAMPLE_COMPLAINTS[sample_choice]

    complaint_input = st.text_area(
        label="complaint",
        value=default_text,
        placeholder="Type the customer complaint here...\n\nExample:\n'I was charged twice for my order. Please refund Rs. 1500 immediately!'",
        height=180,
        label_visibility="collapsed",
    )

    char_count = len(complaint_input.strip().split()) if complaint_input.strip() else 0
    st.caption(f"Words: {char_count}")

    analyse_clicked = st.button("🔍  ANALYSE COMPLAINT")

    if st.button("🗑️  Clear"):
        st.rerun()


# ================================================================================
#  OUTPUT AREA
# ================================================================================
with col_out:
    if analyse_clicked and complaint_input.strip():
        result = analyse(complaint_input.strip())
        st.session_state.log.append(result)

        # ── Classification Result ──────────────────────────────────────────────
        st.markdown("#### 🧠 Analysis Result")

        m1, m2, m3 = st.columns(3)
        with m1:
            st.markdown(f"""<div class="result-card">
                <h4>Category</h4>
                <div class="value">{result['icon']} {result['category']}</div>
            </div>""", unsafe_allow_html=True)
        with m2:
            badge = f"badge-{result['priority'].lower()}"
            st.markdown(f"""<div class="result-card">
                <h4>Priority</h4>
                <div class="value"><span class="{badge}">{result['priority']}</span></div>
            </div>""", unsafe_allow_html=True)
        with m3:
            st.markdown(f"""<div class="result-card">
                <h4>Confidence</h4>
                <div class="value" style="color:{result['conf_color']}">{result['conf_label']}</div>
            </div>""", unsafe_allow_html=True)

        # CF Progress Bar
        st.markdown(f"**Certainty Factor (CF): {result['combined_cf']:.2f}**")
        st.progress(result["combined_cf"])
        st.caption(f"Sentiment: {result['sentiment']}  |  SLA: {result['sla']}  |  Words analysed: {result['word_count']}")

        # ── Entities ──────────────────────────────────────────────────────────
        if result["entities"]:
            st.markdown("**🔎 Extracted Details:**")
            for k, v in result["entities"].items():
                st.markdown(f"- **{k}:** {', '.join(v)}")

        # ── Category Score Chart ───────────────────────────────────────────────
        st.markdown("**📊 Category Match Scores:**")
        max_s = max(result["all_scores"].values()) or 1
        for cat, score in sorted(result["all_scores"].items(), key=lambda x: x[1], reverse=True):
            norm = score / max_s
            icon = CATEGORIES[cat]["icon"]
            marker = " ✅" if cat == result["category"] else ""
            st.markdown(f"{icon} `{cat}`{marker}")
            st.progress(norm)

    elif analyse_clicked:
        st.warning("⚠️ Please enter a complaint before clicking Analyse.")
    else:
        st.markdown("""
<div style="background:#0d1117; border:1px dashed #2a2a4a; border-radius:10px; padding:40px; text-align:center; color:#555;">
    <div style="font-size:2.5rem;">🤖</div>
    <div style="color:#888; margin-top:12px;">Enter a complaint on the left<br>and click <b style="color:#e94560">Analyse Complaint</b></div>
</div>
""", unsafe_allow_html=True)


# ================================================================================
#  REASONING CHAIN + RESOLUTION  (below both columns)
# ================================================================================
if analyse_clicked and complaint_input.strip():
    result = st.session_state.log[-1]

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["🧠 Reasoning Chain", "✅ Resolution Steps", "📊 Session Log"])

    with tab1:
        st.markdown("#### Step-by-Step Reasoning Chain (Explainable AI)")
        steps = [
            f"Complaint received — {result['word_count']} words analysed.",
            f"NLP keyword match → Category identified as **{result['category']}** (Base CF = {result['base_cf']:.2f})",
            f"Matching keywords found: `{', '.join(result['matched_kw']) if result['matched_kw'] else 'general terms'}`",
            f"Rule-based check applied → Rule CF = {result['rule_cf']:.2f}",
            f"MYCIN CF Formula: CF = {result['base_cf']} + {result['rule_cf']} × (1 − {result['base_cf']}) = **{combine_cf(result['base_cf'], result['rule_cf']):.2f}**",
            f"Sentiment detected: {result['sentiment']} → small CF boost applied if urgent/angry",
            f"Final Combined CF = **{result['combined_cf']:.2f}** → Confidence: **{result['conf_label']}**",
            f"Priority = **{result['priority']}** · SLA = {result['sla']} · Escalation = {'⚠️ YES' if result['escalate'] else '✅ NO'}",
        ]
        for i, step in enumerate(steps, 1):
            st.markdown(f"""<div class="step-box"><span class="step-num">Step {i}:</span> {step}</div>""",
                        unsafe_allow_html=True)

        if result["escalate"]:
            st.markdown(f"""<div class="escalation-alert">⚠️ <b>ESCALATION REQUIRED</b><br>
                Reason: {result['esc_reason']}<br>Assign to: {result['escalate_to']}</div>""",
                        unsafe_allow_html=True)
        else:
            st.markdown(f"""<div class="escalation-ok">✅ <b>No Escalation Needed</b> — Automated resolution is sufficient.<br>
                Team: {result['escalate_to']}</div>""", unsafe_allow_html=True)

    with tab2:
        st.markdown(f"#### ✅ Resolution Path — {result['icon']} {result['category']}")
        for step in result["resolution"]:
            st.markdown(f"""<div class="resolution-step">▶ {step}</div>""", unsafe_allow_html=True)
        st.info(f"**Escalate To:** {result['escalate_to']}  |  **SLA:** {result['sla']}")

    with tab3:
        st.markdown(f"#### 📋 Session Log — {len(st.session_state.log)} complaint(s) analysed")
        for i, r in enumerate(reversed(st.session_state.log), 1):
            with st.expander(f"#{len(st.session_state.log) - i + 1} — {r['icon']} {r['category']} · CF: {r['combined_cf']:.2f}"):
                st.markdown(f"- **Priority:** {r['priority']}")
                st.markdown(f"- **Sentiment:** {r['sentiment']}")
                st.markdown(f"- **Confidence:** {r['conf_label']}")
                st.markdown(f"- **Escalated:** {'Yes ⚠️' if r['escalate'] else 'No ✅'}")
                st.markdown(f"- **Resolution:** {r['resolution'][0]}")


# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    "<div style='text-align:center; color:#555; font-size:0.8rem;'>"
    "B.Tech Project · Intelligent Automated Helpdesk Reasoner · "
    "Rule-Based AI · NLP · MYCIN Certainty Factor Reasoning"
    "</div>",
    unsafe_allow_html=True
)
