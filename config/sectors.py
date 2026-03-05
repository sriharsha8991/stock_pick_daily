"""
Sector index mappings and F&O stock universe.
"""

# ──────────────────────────────────────────────
# SECTOR INDEX → YAHOO FINANCE TICKER MAPPING
# ──────────────────────────────────────────────
SECTOR_INDEX_MAP = {
    "BANKING":       {"yf_ticker": "^NSEBANK",    "nse_name": "NIFTY BANK"},
    "IT":            {"yf_ticker": "^CNXIT",       "nse_name": "NIFTY IT"},
    "PHARMA":        {"yf_ticker": "^CNXPHARMA",   "nse_name": "NIFTY PHARMA"},
    "AUTO":          {"yf_ticker": "^CNXAUTO",     "nse_name": "NIFTY AUTO"},
    "METAL":         {"yf_ticker": "^CNXMETAL",    "nse_name": "NIFTY METAL"},
    "REALTY":        {"yf_ticker": "^CNXREALTY",    "nse_name": "NIFTY REALTY"},
    "ENERGY":        {"yf_ticker": "^CNXENERGY",   "nse_name": "NIFTY ENERGY"},
    "FMCG":          {"yf_ticker": "^CNXFMCG",     "nse_name": "NIFTY FMCG"},
    "FINANCIAL":     {"yf_ticker": "^CNXFIN",      "nse_name": "NIFTY FIN SERVICE"},
    "PSU_BANK":      {"yf_ticker": "^CNXPSUBANK",  "nse_name": "NIFTY PSU BANK"},
    "MEDIA":         {"yf_ticker": "^CNXMEDIA",    "nse_name": "NIFTY MEDIA"},
    "PRIVATE_BANK":  {"yf_ticker": "^CNXPVTBANK",  "nse_name": "NIFTY PRIVATE BANK"},
}

# ──────────────────────────────────────────────
# SECTOR → STOCK MAPPING (F&O Stocks Only)
# ──────────────────────────────────────────────
SECTOR_STOCKS = {
    "BANKING": [
        "HDFCBANK", "ICICIBANK", "KOTAKBANK", "AXISBANK", "SBIN",
        "INDUSINDBK", "BANKBARODA", "PNB", "CANBK", "FEDERALBNK",
        "IDFCFIRSTB", "BANDHANBNK", "AUBANK", "RBLBANK", "INDIANB",
        "BANKINDIA", "UNIONBANK", "YESBANK",
    ],
    "IT": [
        "TCS", "INFY", "HCLTECH", "WIPRO", "TECHM", "LTM",
        "MPHASIS", "COFORGE", "PERSISTENT", "KPITTECH", "TATAELXSI",
        "OFSS",
    ],
    "PHARMA": [
        "SUNPHARMA", "DRREDDY", "CIPLA", "DIVISLAB", "LUPIN",
        "AUROPHARMA", "BIOCON", "TORNTPHARM", "GLENMARK", "MANKIND",
        "ZYDUSLIFE", "LAURUSLABS", "SYNGENE", "PPLPHARMA",
    ],
    "AUTO": [
        "MARUTI", "M&M", "TATAMOTORS", "BAJAJ-AUTO", "HEROMOTOCO",
        "EICHERMOT", "ASHOKLEY", "TVSMOTOR", "BHARATFORG", "MOTHERSON",
        "SONACOMS", "UNOMINDA", "EXIDEIND",
    ],
    "METAL": [
        "TATASTEEL", "JSWSTEEL", "HINDALCO", "VEDL", "JINDALSTEL",
        "SAIL", "NMDC", "NATIONALUM", "HINDZINC",
    ],
    "ENERGY": [
        "RELIANCE", "ONGC", "BPCL", "IOC", "GAIL", "HINDPETRO",
        "OIL", "PETRONET", "NTPC", "POWERGRID", "TATAPOWER",
        "NHPC", "PFC", "RECLTD", "COALINDIA", "ADANIENT",
        "ADANIGREEN", "ADANIPORTS", "ADANIENSOL",
    ],
    "FMCG": [
        "HINDUNILVR", "ITC", "NESTLEIND", "BRITANNIA", "DABUR",
        "MARICO", "COLPAL", "GODREJCP", "TATACONSUM", "VBL",
        "UNITDSPR", "PATANJALI",
    ],
    "FINANCIAL": [
        "BAJFINANCE", "BAJAJFINSV", "HDFCLIFE", "SBILIFE", "ICICIPRULI",
        "ICICIGI", "HDFCAMC", "CHOLAFIN", "SHRIRAMFIN", "MUTHOOTFIN",
        "MANAPPURAM", "LICHSGFIN", "LTF", "SBICARD", "ABCAPITAL",
        "MFSL", "JIOFIN", "SAMMAANCAP", "PNBHOUSING", "ANGELONE",
        "NUVAMA", "KFINTECH", "CAMS", "CDSL", "360ONE",
    ],
    "REALTY": [
        "DLF", "GODREJPROP", "OBEROIRLTY", "PRESTIGE", "PHOENIXLTD",
        "LODHA",
    ],
}

# ──────────────────────────────────────────────
# ALL F&O STOCKS (flat list for quick lookup)
# ──────────────────────────────────────────────
ALL_FNO_STOCKS = sorted(set(
    stock for stocks in SECTOR_STOCKS.values() for stock in stocks
))
