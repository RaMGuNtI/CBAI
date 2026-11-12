import streamlit as st
from typing import Any


def apply_saas_theme():
    st.markdown("""
        <style>
        /* Import clean Inter font */
        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* Top Header Styling */
        .main-header {
            font-size: 28px;
            font-weight: 700;
            color: #111827;
            margin-bottom: 4px;
            display: flex;
            align-items: center;
            gap: 10px;
        }
        .main-sub {
            font-size: 15px;
            color: #6B7280;
            margin-bottom: 24px;
        }

        /* Metric Cards */
        .metric-card {
            background-color: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 20px;
            box-shadow: 0 1px 3px 0 rgba(0, 0, 0, 0.05);
            transition: transform 0.15s ease, box-shadow 0.15s ease;
        }
        .metric-card:hover {
            transform: translateY(-2px);
            box-shadow: 0 4px 6px -1px rgba(0, 0, 0, 0.08);
        }
        .metric-val {
            font-size: 30px;
            font-weight: 700;
            color: #1F2937;
            margin-top: 6px;
        }
        .metric-label {
            font-size: 13px;
            font-weight: 600;
            text-transform: uppercase;
            letter-spacing: 0.05em;
            color: #6B7280;
        }

        /* Chatbot list cards */
        .bot-card {
            background: #FFFFFF;
            border: 1px solid #E5E7EB;
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 16px;
            box-shadow: 0 1px 2px rgba(0,0,0,0.04);
        }
        .bot-badge-pub {
            background: #DEF7EC;
            color: #03543F;
            font-size: 12px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 6px;
        }
        .bot-badge-priv {
            background: #F3F4F6;
            color: #4B5563;
            font-size: 12px;
            font-weight: 600;
            padding: 3px 8px;
            border-radius: 6px;
        }

        /* Step wizard navigation pill */
        .wizard-step {
            padding: 8px 16px;
            border-radius: 8px;
            font-weight: 600;
            font-size: 13px;
            display: inline-block;
            margin-right: 8px;
            margin-bottom: 12px;
        }
        .wizard-step-active {
            background: #4F46E5;
            color: white !important;
        }
        .wizard-step-done {
            background: #EEF2FF;
            color: #4338CA;
        }

        /* Callout Box */
        .callout-box {
            background-color: #F8FAFC;
            border-left: 4px solid #4F46E5;
            padding: 14px 18px;
            border-radius: 4px;
            margin: 16px 0;
            font-size: 14px;
            color: #334155;
        }

        /* Source citation tag */
        .source-pill {
            display: inline-block;
            background: #EEF2FF;
            color: #4338CA;
            font-size: 12px;
            padding: 3px 10px;
            border-radius: 12px;
            margin: 4px 4px 4px 0;
            font-weight: 500;
        }
        </style>
    """, unsafe_allow_html=True)


def render_metric_card(label: str, value: Any, icon: str = "📈"):
    st.markdown(f"""
        <div class="metric-card">
            <div class="metric-label">{icon} {label}</div>
            <div class="metric-val">{value}</div>
        </div>
    """, unsafe_allow_html=True)

