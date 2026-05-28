"""
keywords.py
===========
All bullish and bearish keywords used to score 8-K filings.
Edit this file to add / remove keywords anytime.
"""

BULLISH = {
    # Strategic deals
    "securities purchase agreement" : 10,
    "purchase agreement"            : 7,
    "strategic investment"          : 8,
    "strategic partnership"         : 8,
    "design win"                    : 9,
    "multi-year"                    : 6,
    "long-term supply"              : 7,
    "supply agreement"              : 6,
    "exclusive agreement"           : 7,
    "joint venture"                 : 6,
    "convertible preferred"         : 7,
    "co-development"                : 7,

    # Revenue & growth
    "record revenue"                : 10,
    "exceeded expectations"         : 9,
    "raised guidance"               : 9,
    "raised full year"              : 9,
    "beat estimates"                : 8,
    "outperformed"                  : 7,
    "strong demand"                 : 6,
    "accelerating growth"           : 7,
    "revenue growth"                : 6,

    # Contracts & customers
    "new customer"                  : 6,
    "major contract"                : 7,
    "contract awarded"              : 7,
    "expanded agreement"            : 6,
    "volume commitment"             : 6,
    "preferred supplier"            : 7,

    # Products
    "product launch"                : 7,
    "commercial launch"             : 7,
    "fda approval"                  : 10,
    "patent granted"                : 6,
    "breakthrough"                  : 6,
    "next generation"               : 5,
    "mass production"               : 6,
    "custom asic"                   : 7,
    "custom xpu"                    : 7,
    "silicon photonics"             : 7,

    # Financial strength
    "share buyback"                 : 8,
    "stock repurchase"              : 8,
    "increased dividend"            : 7,
    "debt reduction"                : 6,
    "debt repayment"                : 5,
    "strong cash flow"              : 6,
    "acquisition completed"         : 6,
    "definitive agreement"          : 6,
}

BEARISH = {
    # Financial distress
    "going concern"                 : -10,
    "material weakness"             : -9,
    "restatement"                   : -9,
    "missed estimates"              : -8,
    "lowered guidance"              : -9,
    "impairment charge"             : -7,
    "write-down"                    : -7,
    "write-off"                     : -6,
    "goodwill impairment"           : -8,
    "net loss"                      : -5,

    # Legal & regulatory
    "sec investigation"             : -10,
    "doj subpoena"                  : -10,
    "class action"                  : -8,
    "regulatory violation"          : -8,
    "consent order"                 : -7,
    "cease and desist"              : -8,
    "grand jury"                    : -9,
    "government investigation"      : -8,
    "non-compliance"                : -6,
    "sanctions"                     : -7,

    # Operations
    "plant closure"                 : -7,
    "facility shutdown"             : -7,
    "layoffs"                       : -6,
    "workforce reduction"           : -6,
    "restructuring charge"          : -6,
    "supply chain disruption"       : -7,
    "contract termination"          : -7,
    "delayed launch"                : -6,
    "production halt"               : -7,
    "recall"                        : -7,

    # Debt & dilution
    "secondary offering"            : -6,
    "equity offering"               : -5,
    "covenant breach"               : -8,
    "default"                       : -9,
    "bankruptcy"                    : -10,
    "chapter 11"                    : -10,
    "forbearance"                   : -8,

    # Leadership
    "ceo resigned"                  : -7,
    "cfo resigned"                  : -7,
    "ceo departure"                 : -7,
    "terminated without cause"      : -6,
    "interim ceo"                   : -5,
}

# 8-K item numbers and their meaning (for display)
ITEM_LABELS = {
    "1.01" : "Major agreement",
    "1.02" : "Agreement terminated",
    "2.01" : "Acquisition / disposal",
    "2.02" : "Earnings results",
    "2.04" : "Debt default",
    "3.01" : "Exchange delisting",
    "4.01" : "Auditor change",
    "4.02" : "Financial restatement",
    "5.02" : "CEO / CFO change",
    "5.03" : "Bylaws change",
    "7.01" : "Press release",
    "8.01" : "Other events",
    "9.01" : "Financial statements",
}
