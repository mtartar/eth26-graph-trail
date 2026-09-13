"""Graph Trail — Streamlit frontend.

Talks to the FastAPI backend exclusively over HTTP (httpx); never imports
backend/ or touches a data source directly, so backend changes can't break
this file and vice versa.
"""

import os
from html import escape

import httpx
import pandas as pd
import streamlit as st

BACKEND_URL = os.environ.get("BACKEND_URL", "http://127.0.0.1:8010")
_TIMEOUT = 30.0

_EXAMPLE_QUESTIONS = [
    "USDC transfers over $1M in the last week",
    "USDT transfers over $2M",
    "Show me all recent PYUSD transfers",
]

_TRUST_STATEMENT = (
    "Every number here links to its canonical onchain source — subgraph query -> "
    "transaction hash -> block explorer — so nothing is asserted without a "
    "traceable origin you can click through to yourself."
)

_TABLE_COLUMNS = [
    "timestamp",
    "token",
    "amount_usd",
    "from_address",
    "to_address",
    "chain",
    "source",
    "explorer_url",
]


def get_transfers(token: str | None = None, min_amount_usd: float | None = None) -> dict:
    """Call GET /transfers on the backend."""
    params = {k: v for k, v in {"token": token, "min_amount_usd": min_amount_usd}.items() if v}
    response = httpx.get(f"{BACKEND_URL}/transfers", params=params, timeout=_TIMEOUT)
    response.raise_for_status()
    return response.json()


def run_query(question: str) -> dict:
    """Call POST /query on the backend."""
    response = httpx.post(f"{BACKEND_URL}/query", json={"question": question}, timeout=_TIMEOUT)
    response.raise_for_status()
    return response.json()


def run_summary(transfers: list[dict]) -> str:
    """Call POST /summary on the backend."""
    response = httpx.post(f"{BACKEND_URL}/summary", json={"transfers": transfers}, timeout=_TIMEOUT)
    response.raise_for_status()
    return response.json()["summary"]


def inject_style() -> None:
    """Inject custom CSS. Developer-authored strings only — never LLM output goes through this."""
    st.markdown(
        """
        <style>
        .gt-header { padding: 0.25rem 0 1rem 0; }
        .gt-title { font-size: 2.1rem; font-weight: 700; color: #0F172A; }
        .gt-subtitle { color: #64748B; font-size: 1.02rem; margin-top: 0.15rem; }
        .gt-chip {
            display: inline-block; background: #F8FAFC; border: 1px solid #E2E8F0;
            color: #0F172A; border-radius: 999px; padding: 0.25rem 0.85rem;
            margin: 0 0.4rem 0.4rem 0; font-size: 0.85rem; font-weight: 500;
        }
        .gt-summary {
            line-height: 1.6; color: #1E293B; font-size: 0.95rem;
            margin: 0.5rem 0; padding: 0;
        }
        .gt-footer {
            color: #64748B; font-size: 0.85rem; margin-top: 2rem;
            border-top: 1px solid #E2E8F0; padding-top: 0.75rem;
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def render_header() -> None:
    """Render the page title and tagline."""
    st.markdown(
        '<div class="gt-header">'
        '<div class="gt-title">🧭 Graph Trail</div>'
        '<div class="gt-subtitle">Ask about large stablecoin transfers — '
        "every number traces back to its onchain source.</div>"
        "</div>",
        unsafe_allow_html=True,
    )


def render_filter_chips(resolved_filter: dict | None) -> None:
    """Render pill-style chips summarizing the currently applied filter."""
    chips = []
    if resolved_filter:
        if resolved_filter.get("token"):
            chips.append(f"Token: {escape(str(resolved_filter['token']))}")
        if resolved_filter.get("min_amount_usd"):
            chips.append(f"Min: ${resolved_filter['min_amount_usd']:,.0f}")
        if resolved_filter.get("since"):
            chips.append(f"Since: {escape(str(resolved_filter['since'])[:10])}")
    if not chips:
        chips = ["Showing everything — no filters applied"]
    html = "".join(f'<span class="gt-chip">{chip}</span>' for chip in chips)
    st.markdown(html, unsafe_allow_html=True)


def render_metrics(transfers: list[dict]) -> None:
    """Render the count / total volume / average summary metrics."""
    count = len(transfers)
    total = sum(t["amount_usd"] for t in transfers)
    average = total / count if count else 0
    col1, col2, col3 = st.columns(3)
    col1.metric("Transfers", count)
    col2.metric("Total volume", f"${total:,.0f}")
    col3.metric("Average", f"${average:,.0f}")


def render_summary_card(summary: str | None) -> None:
    """Render the AI narrative summary.

    Plain st.markdown only, never unsafe_allow_html — this text comes from the
    LLM, not the developer, so it must never be interpreted as raw HTML.
    """
    if not summary:
        return
    with st.container(border=True):
        st.markdown("🤖 **AI summary**")
        st.markdown(f'<div class="gt-summary">{escape(summary)}</div>', unsafe_allow_html=True)


def render_detail_panel(transfer: dict) -> None:
    """Render the drill-down detail panel for a selected transfer."""
    with st.container(border=True):
        st.markdown("#### 🔎 Transfer detail")
        left, right = st.columns(2)
        with left:
            st.metric("Amount", f"${transfer['amount_usd']:,.2f}")
            st.write("**Token**", transfer["token"])
            st.write("**Chain**", transfer["chain"])
            st.write("**Timestamp**", transfer["timestamp"])
            st.write("**Source**", transfer["source"])
        with right:
            st.write("**From**")
            st.code(transfer["from_address"], language=None)
            st.write("**To**")
            st.code(transfer["to_address"], language=None)
            st.write("**Transaction hash**")
            st.code(transfer["tx_hash"], language=None)
        st.link_button("🔗 View on block explorer", transfer["explorer_url"])


def render_table(transfers: list[dict]) -> None:
    """Render the main transfers grid with a clickable proof column and row selection."""
    if not transfers:
        st.info("No transfers match the current filters.")
        return

    frame = pd.DataFrame(transfers)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    display_frame = frame[_TABLE_COLUMNS]

    event = st.dataframe(
        display_frame,
        column_config={
            "timestamp": st.column_config.DatetimeColumn("Date", format="YYYY-MM-DD HH:mm"),
            "token": st.column_config.TextColumn("Token"),
            "amount_usd": st.column_config.NumberColumn("Amount", format="dollar"),
            "from_address": st.column_config.TextColumn("From"),
            "to_address": st.column_config.TextColumn("To"),
            "chain": st.column_config.TextColumn("Chain"),
            "source": st.column_config.TextColumn("Source"),
            "explorer_url": st.column_config.LinkColumn("Proof", display_text="View ↗"),
        },
        hide_index=True,
        use_container_width=True,
        on_select="rerun",
        selection_mode="single-row",
        key="transfers_table",
    )

    selected_rows = event.selection.rows
    if selected_rows:
        render_detail_panel(transfers[selected_rows[0]])
    else:
        st.caption("Select a row above to drill down into its proof.")


def fetch_summary_cached(transfers: list[dict]) -> str | None:
    """Fetch (and cache in session_state) the narrative summary for the given transfer set.

    Keyed by tx hashes so re-selecting a row (which reruns the script) doesn't
    re-trigger an LLM call for data that hasn't actually changed.
    """
    transfer_ids = tuple(t["tx_hash"] for t in transfers)
    if st.session_state.get("summary_ids") != transfer_ids:
        try:
            with st.spinner("Generating summary..."):
                st.session_state["summary_text"] = run_summary(transfers) if transfers else None
        except (httpx.HTTPStatusError, httpx.ConnectError):
            st.session_state["summary_text"] = None
        st.session_state["summary_ids"] = transfer_ids
    return st.session_state.get("summary_text")


def handle_backend_error(error: Exception) -> None:
    """Show a clear, actionable error message for a failed backend call."""
    if isinstance(error, httpx.ConnectError):
        st.error(
            f"Can't reach the backend at {BACKEND_URL}. Is it running? "
            "`uvicorn backend.main:app --reload --port 8010`"
        )
    elif isinstance(error, httpx.HTTPStatusError):
        st.error(
            f"Backend returned {error.response.status_code}. If this was a question or "
            "summary request, check ANTHROPIC_API_KEY is set in the backend's .env "
            "(see docs/anthropic-api-key.md)."
        )
    else:
        st.error(f"Unexpected error talking to the backend: {error}")


def main() -> None:
    """Render the full Graph Trail page."""
    st.set_page_config(page_title="Graph Trail", page_icon="🧭", layout="wide")
    inject_style()
    render_header()

    st.markdown("**Try:**")
    chip_cols = st.columns(len(_EXAMPLE_QUESTIONS))
    for col, example in zip(chip_cols, _EXAMPLE_QUESTIONS, strict=True):
        if col.button(example, key=f"example_{example}", use_container_width=True):
            st.session_state["question_input"] = example

    with st.form("query_form"):
        question = st.text_input(
            "Question",
            key="question_input",
            placeholder="e.g. USDC transfers over $1M in the last week",
            label_visibility="collapsed",
        )
        asked = st.form_submit_button("🔍 Ask", type="primary")

    with st.expander("Or browse directly (no AI needed)"):
        left, right = st.columns(2)
        token_choice = left.selectbox("Token", ["Any", "USDC", "USDT", "PYUSD"])
        min_amount = right.number_input("Min amount (USD)", min_value=0, value=0, step=100_000)
        browse = st.button("Browse")

    if "current_result" not in st.session_state:
        try:
            st.session_state["current_result"] = get_transfers()
            st.session_state["current_filter"] = None
        except (httpx.HTTPStatusError, httpx.ConnectError) as error:
            handle_backend_error(error)
            st.stop()

    if asked and question:
        try:
            with st.spinner("Asking..."):
                response = run_query(question)
            st.session_state["current_result"] = response["result"]
            st.session_state["current_filter"] = response["resolved_filter"]
        except (httpx.HTTPStatusError, httpx.ConnectError) as error:
            handle_backend_error(error)

    if browse:
        try:
            token_filter = None if token_choice == "Any" else token_choice
            with st.spinner("Searching..."):
                result = get_transfers(token=token_filter, min_amount_usd=min_amount or None)
            st.session_state["current_result"] = result
            st.session_state["current_filter"] = {
                "token": token_filter,
                "min_amount_usd": min_amount or None,
                "since": None,
            }
        except (httpx.HTTPStatusError, httpx.ConnectError) as error:
            handle_backend_error(error)

    result = st.session_state["current_result"]
    transfers = result["transfers"]

    st.divider()
    render_filter_chips(st.session_state.get("current_filter"))
    render_metrics(transfers)
    render_summary_card(fetch_summary_cached(transfers))
    render_table(transfers)

    st.markdown(f'<div class="gt-footer">{escape(_TRUST_STATEMENT)}</div>', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
