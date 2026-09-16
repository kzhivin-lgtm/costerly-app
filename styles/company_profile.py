from __future__ import annotations

import streamlit as st


def apply_company_profile_css() -> None:
    """Keep Company Profile on the same light Costerly canvas in every OS theme."""
    st.markdown(
        """
        <style>
        .stApp:has(.company-profile-active),
        .stApp:has(.company-profile-active) [data-testid="stAppViewContainer"] {
            color-scheme: light !important;
            background: #F1EFEF !important;
            color: #17191C !important;
        }

        .stApp:has(.company-profile-active) h1,
        .stApp:has(.company-profile-active) h2,
        .stApp:has(.company-profile-active) h3,
        .stApp:has(.company-profile-active) p,
        .stApp:has(.company-profile-active) label,
        .stApp:has(.company-profile-active) [data-testid="stWidgetLabel"] p {
            color: #2A1F2C !important;
        }

        .stApp:has(.company-profile-active) div[data-testid="stForm"],
        .stApp:has(.company-profile-active) [data-testid="stCode"] {
            background: #FFFFFF !important;
            color: #17191C !important;
            border-color: #D9DCE0 !important;
        }

        .stApp:has(.company-profile-active) div[data-baseweb="input"],
        .stApp:has(.company-profile-active) div[data-baseweb="input"] > div,
        .stApp:has(.company-profile-active) input,
        .stApp:has(.company-profile-active) textarea {
            color-scheme: light !important;
            background: #FFFFFF !important;
            color: #17191C !important;
            -webkit-text-fill-color: #17191C !important;
        }

        .stApp:has(.company-profile-active) div[data-baseweb="input"] {
            border-color: rgba(42, 31, 44, 0.18) !important;
        }

        .stApp:has(.company-profile-active) div[data-baseweb="input"]:focus-within {
            border-color: #8049C6 !important;
            box-shadow: 0 0 0 3px rgba(128, 73, 198, 0.14) !important;
        }

        .stApp:has(.company-profile-active) [data-testid="stNotification"] {
            color-scheme: light !important;
        }

        .stApp:has(.company-profile-active) [data-testid="stNotification"],
        .stApp:has(.company-profile-active) [data-testid="stAlert"] {
            background: #FFFFFF !important;
            color: #2A1F2C !important;
            border-color: #D9DCE0 !important;
        }

        .stApp:has(.company-profile-active) pre,
        .stApp:has(.company-profile-active) code {
            color-scheme: light !important;
            background: #FFFFFF !important;
            color: #17191C !important;
        }

        .company-profile-users {
            width: 100%;
            overflow: hidden;
            border: 1px solid #D9DCE0;
            border-radius: 10px;
            background: #FFFFFF;
        }

        .company-profile-users table {
            width: 100%;
            border-collapse: collapse;
            color: #17191C;
            font-family: var(--font-sans);
            font-size: 15px;
        }

        .company-profile-users th,
        .company-profile-users td {
            padding: 13px 16px;
            border-bottom: 1px solid #E8EAED;
            text-align: left;
        }

        .company-profile-users th {
            background: #FAF8FC;
            color: #2A1F2C;
            font-weight: 700;
        }

        .company-profile-users tr:last-child td {
            border-bottom: 0;
        }

        .stApp:has(.company-profile-active) hr {
            border-color: #D9DCE0 !important;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
