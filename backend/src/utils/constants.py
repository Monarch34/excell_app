"""
Application constants for styling, colors, and cell positions.
"""

import os

# Excel Color Scheme
COLORS = {
    # Title and headers
    "TITLE_BLUE": "2F5597",
    "SEPARATOR_GREEN": "145A32",
    "HEADER_GRAY": "D9D9D9",
    "UNIT_GRAY": "F2F2F2",
    "HIGHLIGHT_ORANGE": "FFCC99",
}

# Separator column width (position is now dynamic)
SEPARATOR_WIDTH = 3

# Chart configuration
CHART_CONFIG = {
    "FIGSIZE": (8, 5),  # Match report embedding ratio for crisp export charts
    "DPI": 180,
    "DEFAULT_LINE_COLOR": "#2F5597",
    "DEFAULT_FILL_COLOR": "#D5F5E3",
    "DEFAULT_FILL_ALPHA": 0.4,
    "LINE_WIDTH": 2.0,
    "GRID_ALPHA": 0.3,
    "ROW_INCREMENT": 36,  # Rows between charts in XLSX chart sheet
}

# Last zero fallback configuration
LAST_ZERO_SEARCH_PERCENT = 0.10  # Search first 10% of data for fallback
LAST_ZERO_MIN_SEARCH_ROWS = 10  # Minimum rows to search

# Minimum lines for a valid CSV file (header + at least one data row)
MIN_CSV_LINES = 2

# Upload Configuration — MAX_FILE_SIZE_MB tunable via environment variable
UPLOAD_CONFIG = {
    "MAX_FILE_SIZE_MB": int(os.getenv("MAX_FILE_SIZE_MB", "50")),
    "ALLOWED_EXTENSIONS": {".csv"},
}

# In-memory store tunables — override in production to suit your workload
STORE_TTL_SECONDS = int(os.getenv("STORE_TTL_SECONDS", "3600"))
STORE_MAX_ENTRIES = int(os.getenv("STORE_MAX_ENTRIES", "30"))
