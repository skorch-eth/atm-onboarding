#!/usr/bin/env python3
"""
LLC Filing Guide Generator
Generates a state-specific PDF guide for filing an LLC.
Called from merchant_onboarding.py or directly:
    python generate_llc_guide.py merchant_data.json output.pdf
"""

import json
import sys
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER

# ── Colors ─────────────────────────────────────────────────────────────────
DARK_BLUE   = colors.HexColor('#1A3C5E')
MID_BLUE    = colors.HexColor('#2C5F8A')
LIGHT_BLUE  = colors.HexColor('#EAF1F8')
ORANGE      = colors.HexColor('#E67E22')
LIGHT_ORANGE= colors.HexColor('#FEF9E7')
GRAY        = colors.HexColor('#666666')
LIGHT_GRAY  = colors.HexColor('#F7F7F7')
RULE_COLOR  = colors.HexColor('#BBCFE0')
BLACK       = colors.black
WHITE       = colors.white

# ── State-specific step-by-step instructions ───────────────────────────────
STATE_STEPS = {
    "AL": [
        "Go to <b>sos.alabama.gov</b> and click \"Business Services\" → \"Online Filing\"",
        "Select \"Domestic LLC\" and click \"File Certificate of Formation\"",
        "Enter your LLC name — it must include \"LLC\" or \"Limited Liability Company\"",
        "Enter your registered agent's name and Alabama street address (no P.O. Boxes)",
        "Enter the name and address of each organizer",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $200 filing fee by credit card",
        "Download and save your Certificate of Formation once approved (typically 3–5 business days)",
    ],
    "AK": [
        "Go to <b>commerce.alaska.gov</b> and click \"Corporations, Business & Professional Licensing\"",
        "Select \"File a New Business\" → \"Limited Liability Company\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Provide your registered agent's name and Alaska physical address",
        "List the names and addresses of all members or managers",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $250 filing fee online",
        "Save your filed Articles of Organization — approval is typically 10–15 business days",
    ],
    "AZ": [
        "Go to <b>azcc.gov</b> and click \"eCorp\" to access the online filing portal",
        "Select \"Form a New Arizona Company\" → \"LLC\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Co.\"",
        "Enter your statutory agent's name and Arizona physical address",
        "Choose member-managed or manager-managed",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $50 filing fee online",
        "<b>Important:</b> Arizona requires you to publish a notice of LLC formation in a local newspaper for 3 consecutive weeks — the portal will provide instructions",
        "Save your filed Articles of Organization",
    ],
    "CA": [
        "Go to <b>bizfileonline.sos.ca.gov</b> and create an account",
        "Click \"File\" → \"Limited Liability Company\" → \"Articles of Organization (LLC-1)\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent — you can use an individual or a registered agent service",
        "Enter the LLC's principal office address (must be a California address)",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $70 filing fee online",
        "Note: California also charges an $800 annual minimum franchise tax starting the second year",
        "Save your filed Articles of Organization — approval is typically 3–5 business days",
    ],
    "CO": [
        "Go to <b>sos.state.co.us</b> and click \"Business\" → \"File a Document\"",
        "Select \"Limited Liability Company\" → \"Articles of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Colorado address",
        "Enter the principal office address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $50 filing fee online",
        "Download your filed Articles of Organization — approval is typically 1–3 business days",
    ],
    "CT": [
        "Go to <b>business.ct.gov</b> and click \"Start a Business\"",
        "Select \"Domestic Limited Liability Company\" and begin the Certificate of Organization",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Connecticut address",
        "List the name and address of at least one organizer",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $120 filing fee online",
        "Download your Certificate of Organization — approval is typically 1–3 business days",
    ],
    "DE": [
        "Go to <b>icis.corp.delaware.gov</b> and click \"File Online\"",
        "Select \"Limited Liability Company\" → \"Certificate of Formation\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Provide a registered agent with a Delaware address (many use a registered agent service)",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $110 filing fee online",
        "Download your Certificate of Formation — approval is typically 1–2 business days",
        "Note: Delaware is popular for business formation due to its flexible laws",
    ],
    "FL": [
        "Go to <b>dos.myflorida.com/sunbiz</b> and click \"File\" → \"Limited Liability Company\"",
        "Select \"Florida Limited Liability Company\" and click \"File Articles of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Florida street address — they must sign the filing",
        "Enter the principal place of business address",
        "List the names and addresses of all managers or managing members",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $125 filing fee by credit card",
        "Download your Articles of Organization — approval is typically 1–3 business days",
    ],
    "GA": [
        "Go to <b>sos.ga.gov</b> and click \"Corporations Division\" → \"eFilings\"",
        "Select \"Create a New Georgia LLC\" and begin Articles of Organization",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Georgia address",
        "List the name and address of each organizer",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $100 filing fee online",
        "Download your Articles of Organization — approval is typically 5–7 business days",
    ],
    "HI": [
        "Go to <b>cca.hawaii.gov/breg</b> and click \"File Online\"",
        "Select \"Domestic Limited Liability Company\" → \"Articles of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Hawaii address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $50 filing fee online",
        "Download your Articles of Organization — approval is typically 5–10 business days",
    ],
    "ID": [
        "Go to <b>sos.idaho.gov</b> and click \"Business\" → \"Online Filing\"",
        "Select \"Domestic Limited Liability Company\" → \"Certificate of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Idaho address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $100 filing fee online",
        "Download your Certificate of Organization — approval is typically 3–5 business days",
    ],
    "IL": [
        "Go to <b>ilsos.gov</b> and click \"Business Services\" → \"File Online\"",
        "Select \"Domestic LLC\" → \"Articles of Organization (LLC-5.5)\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Illinois address",
        "List the names and addresses of all organizers",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $150 filing fee online",
        "Download your Articles of Organization — approval is typically 10–15 business days",
    ],
    "IN": [
        "Go to <b>inbiz.in.gov</b> and create an account or log in",
        "Click \"Start a New Business\" → \"Domestic Limited Liability Company\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Indiana address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $98 filing fee online",
        "Download your Articles of Organization — approval is typically 1–3 business days",
    ],
    "IA": [
        "Go to <b>sos.iowa.gov</b> and click \"Business Services\" → \"File Online\"",
        "Select \"Domestic LLC\" → \"Certificate of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Iowa address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $50 filing fee online",
        "Download your Certificate of Organization — approval is typically 3–5 business days",
    ],
    "KS": [
        "Go to <b>sos.ks.gov</b> and click \"Business Filing Center\"",
        "Select \"Domestic Limited Liability Company\" → \"Articles of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Kansas address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $165 filing fee online",
        "Download your Articles of Organization — approval is typically 3–5 business days",
    ],
    "KY": [
        "Go to <b>sos.ky.gov</b> and click \"Business Filings\" → \"Online Filing\"",
        "Select \"Domestic Limited Liability Company\" → \"Articles of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Kentucky address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $90 filing fee online",
        "Download your Articles of Organization — approval is typically 3–5 business days",
    ],
    "LA": [
        "Go to <b>sos.la.gov</b> and click \"Commercial Division\" → \"geauxBIZ\"",
        "Select \"Domestic LLC\" → \"Articles of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Louisiana address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $100 filing fee online",
        "Download your Articles of Organization — approval is typically 3–5 business days",
    ],
    "MD": [
        "Go to <b>dat.maryland.gov</b> and click \"Business\" → \"Maryland Business Express\"",
        "Select \"Create a New Business\" → \"Limited Liability Company\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your resident agent's name and Maryland address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $100 filing fee online",
        "Download your Articles of Organization — approval is typically 7–10 business days",
    ],
    "MA": [
        "Go to <b>corp.sec.state.ma.us</b> and click \"File Online\"",
        "Select \"Domestic Limited Liability Company\" → \"Certificate of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Massachusetts address",
        "List the name and address of each manager or member",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $500 filing fee online (Massachusetts has one of the higher filing fees)",
        "Download your Certificate of Organization — approval is typically 3–5 business days",
    ],
    "MI": [
        "Go to <b>michigan.gov/lara</b> and click \"Business\" → \"Online Filing\"",
        "Select \"Domestic Limited Liability Company\" → \"Articles of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Michigan address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $50 filing fee online",
        "Download your Articles of Organization — approval is typically 5–10 business days",
    ],
    "MN": [
        "Go to <b>sos.state.mn.us</b> and click \"Business & Liens\" → \"Business Filings Online\"",
        "Select \"Domestic Limited Liability Company\" → \"Articles of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Minnesota address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $135 filing fee online",
        "Download your Articles of Organization — approval is typically 3–5 business days",
    ],
    "MO": [
        "Go to <b>sos.mo.gov/business</b> and click \"Online Business Filing\"",
        "Select \"Domestic Limited Liability Company\" → \"Articles of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Missouri address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $50 filing fee online",
        "Download your Articles of Organization — approval is typically 3–5 business days",
    ],
    "MT": [
        "Go to <b>sosmt.gov</b> and click \"Business Services\" → \"Online Filing\"",
        "Select \"Domestic Limited Liability Company\" → \"Articles of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Montana address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $70 filing fee online",
        "Download your Articles of Organization — approval is typically 3–5 business days",
    ],
    "NE": [
        "Go to <b>sos.nebraska.gov</b> and click \"Business Services\" → \"Online Filing\"",
        "Select \"Domestic Limited Liability Company\" → \"Certificate of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Nebraska address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $110 filing fee online",
        "Download your Certificate of Organization — approval is typically 3–5 business days",
    ],
    "NV": [
        "Go to <b>esos.nv.gov</b> and click \"New Filing\" → \"Limited Liability Company\"",
        "Select \"Domestic Limited Liability Company\" → \"Articles of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Nevada address",
        "List the names of all managers or managing members",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $425 filing fee online (includes initial list and state business license)",
        "Download your Articles of Organization — approval is typically 1–3 business days",
    ],
    "NJ": [
        "Go to <b>njportal.com/dor/businessformation</b> and begin a new filing",
        "Select \"Domestic Limited Liability Company\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and New Jersey address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $125 filing fee online",
        "Download your Public Records Filing — approval is typically 1–3 business days",
    ],
    "NY": [
        "Go to <b>dos.ny.gov/corps</b> and click \"File\" → \"Limited Liability Company\"",
        "Select \"Domestic Limited Liability Company\" → \"Articles of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and New York address",
        "Enter the county where the principal office is located",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $200 filing fee online",
        "<b>Important:</b> New York requires you to publish a notice of LLC formation in two local newspapers for 6 consecutive weeks within 120 days of filing",
        "Download your Articles of Organization — approval is typically 3–5 business days",
    ],
    "NC": [
        "Go to <b>sosnc.gov</b> and click \"Business Registration\" → \"Online Filing\"",
        "Select \"Domestic Limited Liability Company\" → \"Articles of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and North Carolina address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $125 filing fee online",
        "Download your Articles of Organization — approval is typically 3–5 business days",
    ],
    "OH": [
        "Go to <b>ohiosos.gov</b> and click \"Business Filings\" → \"File Online\"",
        "Select \"Domestic Limited Liability Company\" → \"Articles of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your statutory agent's name and Ohio address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $99 filing fee online",
        "Download your Articles of Organization — approval is typically 3–5 business days",
    ],
    "PA": [
        "Go to <b>dos.pa.gov/business</b> and click \"Bureau of Corporations\" → \"Online Filing\"",
        "Select \"Domestic Limited Liability Company\" → \"Certificate of Organization\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Pennsylvania address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $125 filing fee online",
        "Download your Certificate of Organization — approval is typically 3–7 business days",
    ],
    "TX": [
        "Go to <b>sos.state.tx.us</b> and click \"SOSDirect\" to access the online filing system",
        "Select \"Domestic Limited Liability Company\" → \"Certificate of Formation (Form 205)\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Texas address",
        "Designate a governing authority (member-managed or manager-managed)",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $300 filing fee online",
        "Download your Certificate of Formation — approval is typically 3–5 business days",
    ],
    "WA": [
        "Go to <b>ccfs.sos.wa.gov</b> and click \"New Filing\" → \"Limited Liability Company\"",
        "Select \"Domestic Limited Liability Company\" → \"Certificate of Formation\"",
        "Enter your LLC name — must include \"LLC\", \"L.L.C.\", or \"Limited Liability Company\"",
        "Enter your registered agent's name and Washington address",
        "When asked for business purpose, enter <b>'any lawful business purpose'</b> or <b>'general retail business'</b>",
        "Pay the $200 filing fee online",
        "Download your Certificate of Formation — approval is typically 2–5 business days",
    ],
}

STATE_NAMES = {
    "AL": "Alabama", "AK": "Alaska", "AZ": "Arizona", "CA": "California",
    "CO": "Colorado", "CT": "Connecticut", "DE": "Delaware", "FL": "Florida",
    "GA": "Georgia", "HI": "Hawaii", "ID": "Idaho", "IL": "Illinois",
    "IN": "Indiana", "IA": "Iowa", "KS": "Kansas", "KY": "Kentucky",
    "LA": "Louisiana", "MD": "Maryland", "MA": "Massachusetts", "MI": "Michigan",
    "MN": "Minnesota", "MO": "Missouri", "MT": "Montana", "NE": "Nebraska",
    "NV": "Nevada", "NJ": "New Jersey", "NY": "New York", "NC": "North Carolina",
    "OH": "Ohio", "PA": "Pennsylvania", "TX": "Texas", "WA": "Washington",
}

STATE_LLC_DB = {
    "AL": {"agency": "Alabama Secretary of State", "url": "https://www.sos.alabama.gov", "fee": "$200", "form": "Certificate of Formation"},
    "AK": {"agency": "Alaska Division of Corporations", "url": "https://www.commerce.alaska.gov", "fee": "$250", "form": "Articles of Organization"},
    "AZ": {"agency": "Arizona Corporation Commission", "url": "https://azcc.gov", "fee": "$50", "form": "Articles of Organization"},
    "CA": {"agency": "California Secretary of State", "url": "https://bizfileonline.sos.ca.gov", "fee": "$70", "form": "Articles of Organization (LLC-1)"},
    "CO": {"agency": "Colorado Secretary of State", "url": "https://www.sos.state.co.us", "fee": "$50", "form": "Articles of Organization"},
    "CT": {"agency": "Connecticut Secretary of State", "url": "https://business.ct.gov", "fee": "$120", "form": "Certificate of Organization"},
    "DE": {"agency": "Delaware Division of Corporations", "url": "https://icis.corp.delaware.gov", "fee": "$110", "form": "Certificate of Formation"},
    "FL": {"agency": "Florida Division of Corporations", "url": "https://dos.myflorida.com/sunbiz", "fee": "$125", "form": "Articles of Organization"},
    "GA": {"agency": "Georgia Secretary of State", "url": "https://sos.ga.gov", "fee": "$100", "form": "Articles of Organization"},
    "HI": {"agency": "Hawaii Department of Commerce", "url": "https://cca.hawaii.gov/breg", "fee": "$50", "form": "Articles of Organization"},
    "ID": {"agency": "Idaho Secretary of State", "url": "https://sos.idaho.gov", "fee": "$100", "form": "Certificate of Organization"},
    "IL": {"agency": "Illinois Secretary of State", "url": "https://www.ilsos.gov", "fee": "$150", "form": "Articles of Organization (LLC-5.5)"},
    "IN": {"agency": "Indiana Secretary of State", "url": "https://inbiz.in.gov", "fee": "$98", "form": "Articles of Organization"},
    "IA": {"agency": "Iowa Secretary of State", "url": "https://sos.iowa.gov", "fee": "$50", "form": "Certificate of Organization"},
    "KS": {"agency": "Kansas Secretary of State", "url": "https://sos.ks.gov", "fee": "$165", "form": "Articles of Organization"},
    "KY": {"agency": "Kentucky Secretary of State", "url": "https://sos.ky.gov", "fee": "$90", "form": "Articles of Organization"},
    "LA": {"agency": "Louisiana Secretary of State", "url": "https://www.sos.la.gov", "fee": "$100", "form": "Articles of Organization"},
    "MD": {"agency": "Maryland SDAT", "url": "https://dat.maryland.gov", "fee": "$100", "form": "Articles of Organization"},
    "MA": {"agency": "Massachusetts Secretary of State", "url": "https://corp.sec.state.ma.us", "fee": "$500", "form": "Certificate of Organization"},
    "MI": {"agency": "Michigan LARA", "url": "https://www.michigan.gov/lara", "fee": "$50", "form": "Articles of Organization"},
    "MN": {"agency": "Minnesota Secretary of State", "url": "https://www.sos.state.mn.us", "fee": "$135", "form": "Articles of Organization"},
    "MO": {"agency": "Missouri Secretary of State", "url": "https://www.sos.mo.gov/business", "fee": "$50", "form": "Articles of Organization"},
    "MT": {"agency": "Montana Secretary of State", "url": "https://sosmt.gov", "fee": "$70", "form": "Articles of Organization"},
    "NE": {"agency": "Nebraska Secretary of State", "url": "https://sos.nebraska.gov", "fee": "$110", "form": "Certificate of Organization"},
    "NV": {"agency": "Nevada Secretary of State", "url": "https://esos.nv.gov", "fee": "$425", "form": "Articles of Organization"},
    "NJ": {"agency": "New Jersey Division of Revenue", "url": "https://www.njportal.com/dor/businessformation", "fee": "$125", "form": "Public Records Filing"},
    "NY": {"agency": "New York Department of State", "url": "https://www.dos.ny.gov/corps", "fee": "$200", "form": "Articles of Organization"},
    "NC": {"agency": "North Carolina Secretary of State", "url": "https://www.sosnc.gov", "fee": "$125", "form": "Articles of Organization"},
    "OH": {"agency": "Ohio Secretary of State", "url": "https://www.ohiosos.gov", "fee": "$99", "form": "Articles of Organization"},
    "PA": {"agency": "Pennsylvania Department of State", "url": "https://www.dos.pa.gov/business", "fee": "$125", "form": "Certificate of Organization"},
    "TX": {"agency": "Texas Secretary of State", "url": "https://www.sos.state.tx.us", "fee": "$300", "form": "Certificate of Formation (Form 205)"},
    "WA": {"agency": "Washington Secretary of State", "url": "https://ccfs.sos.wa.gov", "fee": "$200", "form": "Certificate of Formation"},
}

# ── What to have ready (universal) ────────────────────────────────────────
WHAT_YOU_NEED = [
    "Your desired LLC name (must include \"LLC\" or \"Limited Liability Company\")",
    "Your registered agent's full name and physical street address in the state",
    "Your principal business address",
    "Names and addresses of all members or managers",
    "A credit or debit card to pay the filing fee",
    "An email address to receive confirmation",
    "<b>Business Purpose:</b> When asked, enter <b>\"any lawful business purpose\"</b> or <b>\"general retail business\"</b>",
]

# ── What happens after filing ──────────────────────────────────────────────
AFTER_FILING = [
    "You will receive an email confirmation with your filing details",
    "Download and save your formation document (Articles/Certificate of Organization) immediately",
    "Your LLC is now a legal entity — keep this document in a safe place",
    "You can now apply for your EIN using the EIN Application Answer Sheet in this packet",
    "Once you have your EIN, open your business bank account",
    "After your bank account is open, complete and submit the processing forms in this packet",
]


def generate_llc_guide(data: dict, output_path: str):
    state = data["merchant"]["company_state"]
    company_name = data["merchant"]["company_name"]
    today = data.get("date", "")

    if state not in STATE_LLC_DB:
        print(f"  ⚠ State {state} not in database — skipping LLC guide")
        return

    db = STATE_LLC_DB[state]
    state_name = STATE_NAMES.get(state, state)
    steps = STATE_STEPS.get(state, [])

    # ── Styles ─────────────────────────────────────────────────────────────
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle('Title',
        fontName='Helvetica-Bold', fontSize=18,
        textColor=WHITE, leading=22, spaceAfter=0)

    subtitle_style = ParagraphStyle('Subtitle',
        fontName='Helvetica', fontSize=11,
        textColor=colors.HexColor('#BDD7EE'), leading=14, spaceAfter=0)

    section_style = ParagraphStyle('Section',
        fontName='Helvetica-Bold', fontSize=11,
        textColor=MID_BLUE, leading=14,
        spaceBefore=14, spaceAfter=4,
        borderPadding=(0, 0, 2, 0))

    body_style = ParagraphStyle('Body',
        fontName='Helvetica', fontSize=10,
        textColor=colors.HexColor('#222222'), leading=14, spaceAfter=4)

    step_style = ParagraphStyle('Step',
        fontName='Helvetica', fontSize=10,
        textColor=colors.HexColor('#222222'), leading=14,
        leftIndent=20, spaceAfter=5)

    note_style = ParagraphStyle('Note',
        fontName='Helvetica-Oblique', fontSize=9,
        textColor=colors.HexColor('#555555'), leading=12, spaceAfter=4)

    bullet_style = ParagraphStyle('Bullet',
        fontName='Helvetica', fontSize=10,
        textColor=colors.HexColor('#222222'), leading=14,
        leftIndent=16, spaceAfter=4)

    # ── Document setup ─────────────────────────────────────────────────────
    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=0.75*inch, rightMargin=0.75*inch,
        topMargin=0.75*inch, bottomMargin=0.75*inch,
        title=f"LLC Filing Guide — {state_name}",
    )

    story = []
    W = 7.0 * inch  # content width

    # ── Header table ───────────────────────────────────────────────────────
    header_data = [[
        Paragraph(f"LLC FILING GUIDE", title_style),
        Paragraph(f"{state_name} ({state})", title_style),
    ]]
    header_table = Table(header_data, colWidths=[W * 0.6, W * 0.4])
    header_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DARK_BLUE),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(header_table)

    # Sub-header with merchant name
    sub_data = [[
        Paragraph(f"Prepared for: <b>{company_name}</b>", ParagraphStyle('sub',
            fontName='Helvetica', fontSize=9, textColor=GRAY, leading=12)),
        Paragraph(f"Date: {today}", ParagraphStyle('sub2',
            fontName='Helvetica', fontSize=9, textColor=GRAY, leading=12)),
    ]]
    sub_table = Table(sub_data, colWidths=[W * 0.6, W * 0.4])
    sub_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GRAY),
        ('ALIGN', (0, 0), (0, 0), 'LEFT'),
        ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LINEBELOW', (0, 0), (-1, -1), 0.5, RULE_COLOR),
    ]))
    story.append(sub_table)
    story.append(Spacer(1, 14))

    # ── Filing info table ──────────────────────────────────────────────────
    story.append(Paragraph("FILING INFORMATION", section_style))
    story.append(HRFlowable(width=W, thickness=1, color=RULE_COLOR, spaceAfter=8))

    info_rows = [
        ["Filing Agency", db["agency"]],
        ["Online Portal", Paragraph(f'<a href="{db["url"]}" color="#1A3C5E"><u>{db["url"]}</u></a>',
            ParagraphStyle('link', fontName='Helvetica', fontSize=10, leading=14))],
        ["Form Name", db["form"]],
        ["Filing Fee", db["fee"]],
        ["Filing Method", "Online"],
    ]
    info_table = Table(info_rows, colWidths=[1.6*inch, W - 1.6*inch])
    info_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 10),
        ('TEXTCOLOR', (0, 0), (0, -1), MID_BLUE),
        ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#222222')),
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_BLUE),
        ('BACKGROUND', (0, 1), (-1, 1), WHITE),
        ('BACKGROUND', (0, 3), (-1, 3), WHITE),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [LIGHT_BLUE, WHITE]),
        ('GRID', (0, 0), (-1, -1), 0.5, RULE_COLOR),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 14))

    # ── What to have ready ─────────────────────────────────────────────────
    have_ready_block = [
        Paragraph("WHAT TO HAVE READY BEFORE YOU START", section_style),
        HRFlowable(width=W, thickness=1, color=RULE_COLOR, spaceAfter=8),
    ]
    for item in WHAT_YOU_NEED:
        have_ready_block.append(Paragraph(f"&#x2022;  {item}", bullet_style))
    story.append(KeepTogether(have_ready_block))
    story.append(Spacer(1, 14))

    # ── Step-by-step ───────────────────────────────────────────────────────
    steps_block = [
        Paragraph(f"STEP-BY-STEP FILING INSTRUCTIONS — {state_name.upper()}", section_style),
        HRFlowable(width=W, thickness=1, color=RULE_COLOR, spaceAfter=8),
    ]

    step_rows = []
    for i, step in enumerate(steps, 1):
        step_rows.append([
            Paragraph(f"<b>{i}</b>", ParagraphStyle('num',
                fontName='Helvetica-Bold', fontSize=10,
                textColor=WHITE, alignment=TA_CENTER, leading=13)),
            Paragraph(step, ParagraphStyle('steptext',
                fontName='Helvetica', fontSize=10,
                textColor=colors.HexColor('#222222'), leading=14)),
        ])

    step_table = Table(step_rows, colWidths=[0.35*inch, W - 0.35*inch])
    step_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (0, -1), DARK_BLUE),
        ('ROWBACKGROUNDS', (1, 0), (1, -1), [LIGHT_BLUE, WHITE]),
        ('GRID', (0, 0), (-1, -1), 0.5, RULE_COLOR),
        ('ALIGN', (0, 0), (0, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('LEFTPADDING', (0, 0), (0, -1), 6),
        ('LEFTPADDING', (1, 0), (1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
        ('TOPPADDING', (0, 0), (-1, -1), 7),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 7),
    ]))
    steps_block.append(step_table)
    story.append(KeepTogether(steps_block))
    story.append(Spacer(1, 14))

    # ── After filing ───────────────────────────────────────────────────────
    after_block = [
        Paragraph("AFTER YOUR LLC IS APPROVED", section_style),
        HRFlowable(width=W, thickness=1, color=RULE_COLOR, spaceAfter=8),
    ]
    for item in AFTER_FILING:
        after_block.append(Paragraph(f"&#x2022;  {item}", bullet_style))
    story.append(KeepTogether(after_block))
    story.append(Spacer(1, 14))

    # ── Important note box ─────────────────────────────────────────────────
    note_data = [[
        Paragraph(
            "<b>Important:</b> This guide is provided for informational purposes. "
            "State filing requirements change periodically. Always verify current fees and "
            "procedures on the state's official website before filing. If you have questions, "
            "consult a business attorney or registered agent service.",
            ParagraphStyle('notebox', fontName='Helvetica', fontSize=9,
                textColor=colors.HexColor('#5D4037'), leading=13)
        )
    ]]
    note_table = Table(note_data, colWidths=[W])
    note_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor('#FFF8E1')),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor('#F9A825')),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(note_table)

    # ── Build ──────────────────────────────────────────────────────────────
    doc.build(story)
    print(f"  ✓ LLC Filing Guide → {output_path}")


if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Usage: python generate_llc_guide.py merchant_data.json output.pdf")
        sys.exit(1)
    with open(sys.argv[1]) as f:
        data = json.load(f)
    generate_llc_guide(data, sys.argv[2])
