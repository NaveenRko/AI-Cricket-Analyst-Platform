import os

import streamlit as st

from dotenv import load_dotenv
from supabase import create_client

load_dotenv()

# ---------------------------------------
# Try Streamlit Secrets
# ---------------------------------------

try:

    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]

# ---------------------------------------
# Fallback to .env
# ---------------------------------------

except Exception:

    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")

if not url or not key:

    raise ValueError(
        "SUPABASE_URL or SUPABASE_KEY not found."
    )

supabase = create_client(url, key)