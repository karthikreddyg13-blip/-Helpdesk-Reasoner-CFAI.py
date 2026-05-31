"""
================================================================================
   INTELLIGENT AUTOMATED HELPDESK REASONER
   For Explainable Complaint Resolution
================================================================================
   Project   : B.Tech Final Year Project
   Language  : Python 3.x
   Concept   : Rule-Based AI + NLP + Certainty Factor Reasoning
   Run       : python helpdesk_reasoner.py
================================================================================
"""

import re
import datetime

# ================================================================================
#  STEP 1 — KNOWLEDGE BASE
#  All complaint categories, keywords, rules, and resolution steps are stored here.
#  This is the "brain" of the system — the more rules we add, the smarter it gets.
# ================================================================================

CATEGORIES = {
    "Payment Issue": {
        "keywords": ["payment", "charged", "refund", "billing", "invoice",
                     "money", "deducted", "transaction", "fee", "overcharged",
                     "double charged", "failed payment", "card", "amount"],
        "priority": "HIGH",
        "icon": "[PAYMENT]"
    },
    "Technical Error": {
        "keywords": ["error", "not working", "crash", "bug", "broken", "fail",
                     "unable", "cannot", "login", "password", "otp", "app",
                     "website", "slow", "freeze", "blank", "server", "down"],
        "priority": "HIGH",
        "icon": "[TECHNICAL]"
    },
    "Account Issue": {
        "keywords": ["account", "locked", "blocked", "suspended", "username",
                     "verify", "hacked", "unauthorized", "access denied",
                     "reset", "delete account", "deactivate", "profile"],
        "priority": "MEDIUM",
        "icon": "[ACCOUNT]"
    },
    "Delivery Delay": {
        "keywords": ["delay", "late", "not delivered", "shipment", "order",
                     "delivery", "tracking", "pending", "stuck", "dispatch",
                     "lost", "missing", "where is my", "not arrived"],
        "priority": "MEDIUM",
        "icon": "[DELIVERY]"
    },
    "Product Quality": {
        "keywords": ["damaged", "broken", "defective", "wrong item", "different",
                     "quality", "replace", "return", "exchange", "warranty",
                     "torn", "scratched", "missing parts", "poor quality"],
        "priority": "MEDIUM",
        "icon": "[PRODUCT]"
    },
    "General Enquiry": {
        "keywords": ["how", "what", "when", "where", "help", "information",
                     "guide", "steps", "policy", "terms", "question", "explain"],
        "priority": "LOW",
        "icon": "[ENQUIRY]"
    }
}


RESOLUTION_STEPS = {
    "Payment Issue": [
        "1. Verify the transaction ID and purchase details from the system",
        "2. Check if payment was debited from customer's account",
        "3. Raise a refund/correction request in the billing system",
        "4. Send confirmation email to customer with expected timeline",
        "5. Follow up within 3-5 business days to confirm resolution"
    ],
    "Technical Error": [
        "1. Collect details: device type, OS version, app version",
        "2. Ask customer to clear cache and restart the application",
        "3. Check server/system status from the admin dashboard",
        "4. If login issue: send password reset link to registered email",
        "5. If issue persists: escalate to the technical team with logs"
    ],
    "Account Issue": [
        "1. Verify customer identity using registered email or phone",
        "2. Check account status in the admin panel",
        "3. If hacked: immediately freeze account and alert security team",
        "4. If locked: unlock after successful identity verification",
        "5. Send confirmation to customer once account is restored"
    ],
    "Delivery Delay": [
        "1. Retrieve order number and check real-time tracking status",
        "2. Contact the logistics/courier partner for update",
        "3. Provide customer with expected delivery date",
        "4. If significantly delayed: offer partial refund or priority re-dispatch",
        "5. Close ticket only after customer confirms delivery"
    ],
    "Product Quality": [
        "1. Ask customer to share photo/video evidence of the issue",
        "2. Verify purchase date and check warranty period",
        "3. Approve replacement order or full refund",
        "4. Arrange free pickup of the defective product",
        "5. Dispatch replacement within 2 business days"
    ],
    "General Enquiry": [
        "1. Identify the exact topic the customer needs help with",
        "2. Provide clear, step-by-step instructions",
        "3. Share a help article or FAQ link if available",
        "4. Confirm whether the response answered the query",
        "5. Log query for FAQ update if asked frequently"
    ]
}


ESCALATION_TEAM = {
    "Payment Issue"   : "Finance & Billing Department",
    "Technical Error" : "IT Support Team (Level 2)",
    "Account Issue"   : "Account Security Team",
    "Delivery Delay"  : "Logistics & Fulfilment Team",
    "Product Quality" : "Quality Assurance Team",
    "General Enquiry" : "Customer Support Team"
}

SLA = {
    "HIGH"   : "Response within 2 hours",
    "MEDIUM" : "Response within 24 hours",
    "LOW"    : "Response within 72 hours"
}


# ================================================================================
#  STEP 2 — NLP MODULE
#  Processes the raw complaint text and calculates how closely it matches
#  each category using keyword scoring.
# ================================================================================

STOP_WORDS = {
    "i", "me", "my", "we", "you", "your", "he", "she", "it", "they",
    "is", "are", "was", "were", "am", "be", "been", "have", "has", "had",
    "do", "does", "did", "a", "an", "the", "and", "but", "or", "so",
    "at", "by", "for", "in", "of", "on", "to", "up", "with", "from",
    "this", "that", "these", "very", "just", "also", "still", "get",
    "hi", "hello", "dear", "sir", "madam", "please", "kindly", "thank"
}

def clean_text(text):
    """Lowercase and remove punctuation from the complaint."""
    text = text.lower()
    text = re.sub(r"[^\w\s]", " ", text)
    text = re.sub(r"\s+", " ", text).strip()
    return text

def tokenize(text):
    """Split text into individual words."""
    return text.split()

def remove_stopwords(tokens):
    """Remove common words that don't carry meaning."""
    return [word for word in tokens if word not in STOP_WORDS]

def score_categories(complaint_text):
    """
    Score each category based on how many of its keywords
    appear in the complaint. Higher score = better match.
    """
    cleaned   = clean_text(complaint_text)
    tokens    = tokenize(cleaned)
    filtered  = remove_stopwords(tokens)
    token_set = set(filtered)

    scores = {}
    matched_keywords = {}

    for category, data in CATEGORIES.items():
        hits = []
        score = 0

        for keyword in data["keywords"]:
            # Check both single words and phrases
            if keyword in cleaned:
                hits.append(keyword)
                score += 2 if " " in keyword else 1   # phrases score higher

        scores[category]          = score
        matched_keywords[category] = hits

    return scores, matched_keywords, filtered

def extract_entities(text):
    """Extract useful information like order IDs and amounts from the complaint."""
    found = {}

    order = re.findall(r'\b(?:order|ord|ref)[:\-#]?\s*\d{4,12}\b', text, re.IGNORECASE)
    if order:
        found["Order ID"] = order

    amount = re.findall(r'(?:rs\.?|rupees?|inr|₹)\s*[\d,]+|\b\d+\s*rupees?\b', text, re.IGNORECASE)
    if amount:
        found["Amount"] = amount

    email = re.findall(r'\b[\w.+-]+@[\w-]+\.[a-z]{2,}\b', text)
    if email:
        found["Email"] = email

    phone = re.findall(r'\b[6-9]\d{9}\b', text)
    if phone:
        found["Phone"] = phone

    return found


# ================================================================================
#  STEP 3 — CERTAINTY FACTOR (CF) REASONING ENGINE
#  Based on the MYCIN expert system approach.
#  CF value ranges from 0.0 (no confidence) to 1.0 (fully confident).
#  Formula: CF_combined = CF1 + CF2 * (1 - CF1)
# ================================================================================

def calculate_cf(score, max_score):
    """Convert a raw keyword score into a Certainty Factor (0.0 to 1.0)."""
    if max_score == 0:
        return 0.0
    base_cf = score / max_score
    return round(min(base_cf, 1.0), 2)

def detect_sentiment(text):
    """Detect the emotional tone of the complaint."""
    text_lower = text.lower()

    angry_words  = ["angry", "frustrated", "ridiculous", "unacceptable",
                    "worst", "terrible", "cheated", "fraud", "scam", "horrible"]
    urgent_words = ["urgent", "immediately", "asap", "emergency", "right now",
                    "cannot wait", "critical", "serious"]

    for word in angry_words:
        if word in text_lower:
            return "ANGRY", +0.05

    for word in urgent_words:
        if word in text_lower:
            return "URGENT", +0.03

    return "NEUTRAL", 0.0

def combine_cf(cf1, cf2):
    """MYCIN CF combination formula for two independent pieces of evidence."""
    return round(cf1 + cf2 * (1 - cf1), 2)

def get_confidence_label(cf):
    """Convert CF number to a human-readable label."""
    if cf >= 0.85:
        return "VERY HIGH"
    elif cf >= 0.65:
        return "HIGH"
    elif cf >= 0.45:
        return "MODERATE"
    elif cf >= 0.25:
        return "LOW"
    else:
        return "VERY LOW — Human Agent Needed"

def needs_escalation(cf, priority, sentiment):
    """Decide if this complaint needs immediate human escalation."""
    if cf < 0.40:
        return True, "Low confidence — system is unsure, human review needed"
    if sentiment == "ANGRY" and priority == "HIGH":
        return True, "Angry customer with high-priority issue — human empathy needed"
    if priority == "HIGH" and cf < 0.60:
        return True, "High-priority but moderate confidence — verify with agent"
    return False, "Automated resolution is sufficient"


# ================================================================================
#  STEP 4 — REASONING ENGINE
#  Combines all the above modules to produce the final analysis and decision.
# ================================================================================

def analyse_complaint(complaint_text):
    """
    Main function — runs the full AI pipeline on a complaint.
    Returns a structured result dictionary.
    """

    # --- NLP Analysis ---
    scores, matched_kw, filtered_tokens = score_categories(complaint_text)
    entities = extract_entities(complaint_text)
    sentiment, sentiment_boost = detect_sentiment(complaint_text)

    # --- Find Best Category ---
    max_score = max(scores.values()) if scores else 0

    if max_score == 0:
        best_category = "General Enquiry"
        base_cf       = 0.20
    else:
        best_category = max(scores, key=scores.get)
        base_cf       = calculate_cf(scores[best_category], max_score)

    # --- Apply Certainty Factor Reasoning ---
    rule_cf     = 0.85 if scores[best_category] >= 3 else 0.65 if scores[best_category] >= 1 else 0.30
    combined_cf = combine_cf(base_cf, rule_cf)
    combined_cf = min(round(combined_cf + sentiment_boost, 2), 1.0)

    # --- Priority & Escalation ---
    priority   = CATEGORIES[best_category]["priority"]
    escalate, escalation_reason = needs_escalation(combined_cf, priority, sentiment)

    return {
        "complaint"        : complaint_text,
        "word_count"       : len(complaint_text.split()),
        "tokens"           : filtered_tokens,
        "category"         : best_category,
        "icon"             : CATEGORIES[best_category]["icon"],
        "priority"         : priority,
        "sentiment"        : sentiment,
        "all_scores"       : scores,
        "matched_keywords" : matched_kw[best_category],
        "base_cf"          : base_cf,
        "rule_cf"          : rule_cf,
        "combined_cf"      : combined_cf,
        "confidence"       : get_confidence_label(combined_cf),
        "resolution_steps" : RESOLUTION_STEPS[best_category],
        "escalate_to"      : ESCALATION_TEAM[best_category],
        "sla"              : SLA[priority],
        "needs_escalation" : escalate,
        "escalation_reason": escalation_reason,
        "entities"         : entities,
    }


# ================================================================================
#  STEP 5 — REPORT PRINTER
#  Formats and prints the final result in a readable way.
# ================================================================================

def print_report(result):
    """Print the full analysis report to the console."""
    LINE  = "=" * 65
    DASH  = "-" * 65
    now   = datetime.datetime.now().strftime("%d %b %Y  %H:%M:%S")

    print("\n" + LINE)
    print("   INTELLIGENT AUTOMATED HELPDESK REASONER")
    print("   AI-Powered Complaint Analysis Report")
    print(LINE)
    print(f"   Timestamp : {now}")
    print(DASH)

    # Complaint
    print("\n COMPLAINT SUBMITTED:")
    print(f'   "{result["complaint"]}"')
    print(f"   Word Count : {result['word_count']}")
    print(DASH)

    # NLP Output
    print("\n NLP ANALYSIS:")
    print(f"   Sentiment Detected : {result['sentiment']}")
    print(f"   Key Words Found    : {', '.join(result['matched_keywords']) if result['matched_keywords'] else 'None'}")

    if result["entities"]:
        print("   Extracted Details  :")
        for key, values in result["entities"].items():
            print(f"      {key} : {', '.join(values)}")

    print(DASH)

    # Category Scores
    print("\n CATEGORY MATCH SCORES (Certainty Factors):")
    max_score = max(result["all_scores"].values()) if result["all_scores"] else 1

    for cat, score in sorted(result["all_scores"].items(), key=lambda x: x[1], reverse=True):
        bar_len = int((score / max(max_score, 1)) * 20)
        bar     = "#" * bar_len + "-" * (20 - bar_len)
        cf_val  = calculate_cf(score, max(max_score, 1))
        marker  = "  <-- SELECTED" if cat == result["category"] else ""
        print(f"   {cat:<20} [{bar}]  CF: {cf_val:.2f}{marker}")

    print(DASH)

    # Final Classification
    print("\n CLASSIFICATION RESULT:")
    print(f"   Category   :  {result['icon']}  {result['category']}")
    print(f"   Priority   :  {result['priority']}")
    print(f"   SLA Target :  {result['sla']}")
    print(DASH)

    # Reasoning Chain
    print("\n REASONING CHAIN (How the AI decided):")
    print(f"   Step 1 : Complaint received — {result['word_count']} words analysed.")
    print(f"   Step 2 : NLP matched '{result['category']}' with base CF = {result['base_cf']:.2f}")
    print(f"   Step 3 : Rule-based check applied — Rule CF = {result['rule_cf']:.2f}")
    print(f"   Step 4 : MYCIN Formula applied:")
    print(f"            CF = {result['base_cf']} + {result['rule_cf']} x (1 - {result['base_cf']})")
    print(f"            CF = {result['combined_cf']:.2f}")
    print(f"   Step 5 : Sentiment = {result['sentiment']} (small CF boost applied if urgent/angry)")
    print(f"   Step 6 : Final Combined CF = {result['combined_cf']:.2f}  -->  {result['confidence']} CONFIDENCE")
    print(f"   Step 7 : Priority set to {result['priority']} — SLA: {result['sla']}")
    print(f"   Step 8 : Escalation check: {'YES — Human Agent Required' if result['needs_escalation'] else 'NO — Automated Resolution'}")
    print(DASH)

    # Resolution Steps
    print(f"\n RESOLUTION PATH — {result['category'].upper()}")
    for step in result["resolution_steps"]:
        print(f"   {step}")

    print()
    print(f"   Escalate To       :  {result['escalate_to']}")
    print(f"   Expected Timeline :  {result['sla']}")
    print(DASH)

    # Escalation Box
    if result["needs_escalation"]:
        print("\n *** ESCALATION ALERT ***")
        print(f"   Reason  : {result['escalation_reason']}")
        print(f"   Team    : {result['escalate_to']}")
        print(f"   Action  : Assign to human agent immediately")
    else:
        print("\n   Automated Resolution — No Escalation Needed")

    print(DASH)
    print(f"   Combined CF     : {result['combined_cf']:.2f}")
    print(f"   Confidence Level: {result['confidence']}")
    print(LINE)
    print("   END OF REPORT")
    print(LINE + "\n")


# ================================================================================
#  STEP 6 — INTERACTIVE MENU
#  Simple menu-driven interface for the user.
# ================================================================================

session_log = []

def show_session_stats():
    """Show summary of all complaints analysed in this session."""
    if not session_log:
        print("\n   No complaints analysed yet.\n")
        return

    LINE = "=" * 65
    print("\n" + LINE)
    print("   SESSION SUMMARY")
    print(LINE)
    print(f"   Total Complaints : {len(session_log)}")

    avg_cf = sum(r["combined_cf"] for r in session_log) / len(session_log)
    print(f"   Average CF       : {avg_cf:.2f}")

    escalated = sum(1 for r in session_log if r["needs_escalation"])
    print(f"   Escalated Cases  : {escalated} out of {len(session_log)}")

    print("\n   Category Breakdown:")
    cat_count = {}
    for r in session_log:
        cat_count[r["category"]] = cat_count.get(r["category"], 0) + 1
    for cat, count in sorted(cat_count.items(), key=lambda x: x[1], reverse=True):
        print(f"      {cat:<22} : {count} complaint(s)")

    print("\n   Priority Breakdown:")
    for priority in ["HIGH", "MEDIUM", "LOW"]:
        count = sum(1 for r in session_log if r["priority"] == priority)
        print(f"      {priority:<10} : {count}")

    print(LINE + "\n")


def run_demo():
    """Run 5 pre-loaded sample complaints automatically."""
    samples = [
        "I was charged twice for order ORD-7821. Please refund Rs. 1500 immediately.",
        "The app keeps crashing every time I try to login. Very frustrated!",
        "My account has been hacked and there are suspicious transactions I did not make.",
        "My delivery is 3 weeks late. Order ORD-984521 still shows pending status.",
        "I received a completely damaged and wrong product in the box.",
    ]

    print("\n" + "=" * 65)
    print("   DEMO MODE — Running 5 Sample Complaints")
    print("=" * 65)

    for i, complaint in enumerate(samples, 1):
        print(f"\n[{i}/5] Analysing: \"{complaint[:55]}...\"")
        result = analyse_complaint(complaint)
        session_log.append(result)

        print(f"      Category   : {result['icon']} {result['category']}")
        print(f"      Priority   : {result['priority']}")
        print(f"      CF Score   : {result['combined_cf']:.2f} ({result['confidence']} CONFIDENCE)")
        print(f"      Escalate   : {'YES' if result['needs_escalation'] else 'NO'}")
        print(f"      Resolution : {result['resolution_steps'][0]}")

    show_session_stats()


def run_single_complaint():
    """Let the user type one complaint and see full analysis."""
    print("\n   Enter your complaint below (press Enter twice when done):")
    print("   " + "-" * 55)
    complaint = input("   >>> ").strip()

    if not complaint:
        print("   No complaint entered. Returning to menu.\n")
        return

    print("\n   Analysing complaint...")
    result = analyse_complaint(complaint)
    session_log.append(result)
    print_report(result)


def main():
    """Main menu loop."""
    print("\n" + "=" * 65)
    print("   INTELLIGENT AUTOMATED HELPDESK REASONER")
    print("   B.Tech Project — AI & Expert Systems")
    print("=" * 65)

    while True:
        print("\n   MAIN MENU")
        print("   ---------")
        print("   1. Analyse a Complaint (type your own)")
        print("   2. Run Demo (5 pre-loaded sample complaints)")
        print("   3. View Session Statistics")
        print("   4. Exit")
        print()

        choice = input("   Enter choice (1/2/3/4): ").strip()

        if choice == "1":
            run_single_complaint()
        elif choice == "2":
            run_demo()
        elif choice == "3":
            show_session_stats()
        elif choice == "4":
            print("\n   Thank you! Exiting the Helpdesk Reasoner.\n")
            break
        else:
            print("   Invalid choice. Please enter 1, 2, 3, or 4.")


# ================================================================================
if __name__ == "__main__":
    main()