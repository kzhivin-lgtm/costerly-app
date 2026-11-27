from __future__ import annotations

import streamlit as st


def apply_projects_css() -> None:
    st.markdown(
        """
        <style>
        .projects-screen-active { display: none; }
        .stApp:has(.projects-screen-active) .costerly-app-header { display: none !important; }
        .stApp:has(.projects-screen-active) .block-container {
            width: min(1180px, calc(100vw - 48px));
            max-width: 1180px;
            padding-top: 42px !important;
            padding-bottom: 80px;
        }
        .projects-title {
            margin: 0 0 30px;
            color: var(--color-text-strong);
            font-family: var(--font-sans);
            font-size: clamp(34px, 4vw, 48px);
            line-height: 1.05;
            letter-spacing: -0.04em;
        }
        .st-key-costerly_screen_header { margin-bottom: 30px; }
        .projects-table-card {
            background: var(--color-surface);
            border: 1px solid rgba(42, 31, 44, 0.14);
            border-radius: 16px;
            overflow: hidden;
        }
        .projects-partner + .projects-partner {
            border-top: 1px solid rgba(42, 31, 44, 0.12);
        }
        .projects-partner > summary {
            min-height: 64px;
            display: flex;
            align-items: center;
            gap: 14px;
            padding: 0 22px;
            cursor: pointer;
            list-style: none;
            color: var(--color-text-strong);
        }
        .projects-partner > summary::-webkit-details-marker { display: none; }
        .projects-partner > summary::before {
            content: "›";
            width: 18px;
            font-size: 26px;
            line-height: 1;
            color: rgba(42, 31, 44, 0.52);
            transform: rotate(0deg);
            transition: transform 120ms ease;
        }
        .projects-partner[open] > summary::before { transform: rotate(90deg); }
        .projects-partner-name { font-size: 17px; font-weight: 750; }
        .projects-partner-count {
            margin-left: auto;
            color: rgba(42, 31, 44, 0.52);
            font-size: 13px;
            font-weight: 650;
        }
        .projects-projects-body {
            border-top: 1px solid rgba(42, 31, 44, 0.12);
            background: rgba(248, 246, 248, 0.72);
        }
        .projects-project-head,
        .projects-project-row {
            display: grid;
            grid-template-columns: minmax(180px, 2fr) minmax(150px, 1.5fr) minmax(155px, 1.25fr) minmax(90px, 0.8fr) 64px;
            align-items: center;
            column-gap: 18px;
            padding: 0 22px 0 54px;
        }
        .projects-project-head {
            min-height: 42px;
            color: rgba(42, 31, 44, 0.52);
            font-size: 12px;
            font-weight: 750;
            letter-spacing: 0.06em;
            text-transform: uppercase;
        }
        .projects-project-row {
            min-height: 58px;
            border-top: 1px solid rgba(42, 31, 44, 0.09);
            color: rgba(42, 31, 44, 0.76);
            font-size: 14px;
        }
        .projects-project-row > div {
            min-height: 58px;
            display: flex;
            align-items: center;
        }
        .projects-project-name { color: var(--color-text-strong); font-weight: 700; }
        .projects-total { color: var(--color-text-strong); font-weight: 700; }
        .projects-pdf-link { color: var(--color-primary); font-weight: 750; text-decoration: none; }
        .projects-pdf-link:hover { text-decoration: underline; }
        .projects-pdf-empty { color: rgba(42, 31, 44, 0.38); }
        .projects-partner-empty {
            min-height: 58px;
            display: flex;
            align-items: center;
            padding: 0 54px;
            color: rgba(42, 31, 44, 0.52);
            border-top: 1px solid rgba(42, 31, 44, 0.09);
        }
        .projects-empty {
            padding: 54px 28px;
            text-align: center;
            color: rgba(42, 31, 44, 0.58);
            background: var(--color-surface);
            border: 1px solid rgba(42, 31, 44, 0.14);
            border-radius: 16px;
        }
        .projects-project > summary { list-style: none; cursor: pointer; }
        .projects-project > summary::-webkit-details-marker { display:none; }
        .projects-project-name::before { content:"›"; margin-right:10px; font-size:22px; }
        .projects-project[open] > summary .projects-project-name::before { content:"⌄"; }
        .projects-history { padding:0 22px 14px 54px; }
        .projects-file,.projects-calculation,.projects-version { border-top:1px solid rgba(42,31,44,.1); }
        .projects-file > summary,.projects-calculation > summary,.projects-version > summary {
            min-height:48px; display:flex; align-items:center; gap:16px; cursor:pointer;
            list-style:none; overflow-wrap:anywhere; font-size:14px; color:var(--color-text-strong);
        }
        .projects-file > summary::-webkit-details-marker,.projects-calculation > summary::-webkit-details-marker,
        .projects-version > summary::-webkit-details-marker { display:none; }
        .projects-file > summary::before,.projects-calculation > summary::before,.projects-version > summary::before {
            content:"›"; flex:none; font-size:22px; color:rgba(42,31,44,.52);
        }
        .projects-file[open] > summary::before,.projects-calculation[open] > summary::before,
        .projects-version[open] > summary::before { content:"⌄"; }
        .projects-calculations,.projects-version-list { margin-left:20px; }
        .projects-version > summary > .projects-total { margin-left:auto; }
        .projects-version > summary > .projects-pdf-link,.projects-version > summary > .projects-pdf-empty { width:40px; text-align:right; }
        .projects-objects { width:100%; border-collapse:collapse; font-size:13px; margin-bottom:14px; }
        .projects-objects th,.projects-objects td { padding:10px; text-align:right; border-top:1px solid rgba(42,31,44,.08); }
        .projects-objects th:first-child,.projects-objects td:first-child { text-align:left; }
        .projects-objects th { color:rgba(42,31,44,.52); font-weight:600; }
        .projects-objects small { display:block; color:rgba(42,31,44,.52); margin-top:3px; }
        @media (max-width: 820px) {
            .projects-projects-body { overflow-x: auto; }
            .projects-project-head,
            .projects-project-row { min-width: 760px; }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
