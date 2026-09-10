import streamlit as st
import pandas as pd
import numpy as np
import requests
from io import StringIO, BytesIO
from datetime import date, datetime, timedelta
import time

# ─────────────────────────────────────────────────────────
# PAGE CONFIG & CUSTOM CSS
# ─────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Invesco NAV Simulation Engine",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

    /* Global */
    .stApp { font-family: 'Inter', sans-serif; }

    /* Header banner */
    .hero-banner {
        background: linear-gradient(135deg, #0f2027 0%, #203a43 50%, #2c5364 100%);
        padding: 2rem 2.5rem;
        border-radius: 16px;
        margin-bottom: 1.5rem;
        color: white;
    }
    .hero-banner h1 {
        font-size: 2rem;
        font-weight: 700;
        margin: 0 0 0.3rem 0;
        letter-spacing: -0.5px;
    }
    .hero-banner p {
        font-size: 0.95rem;
        opacity: 0.8;
        margin: 0;
    }

    /* Metric cards */
    .metric-card {
        background: #f8fafc;
        border: 1px solid #e2e8f0;
        border-radius: 12px;
        padding: 1.2rem 1.5rem;
        text-align: center;
    }
    .metric-card .label {
        font-size: 0.75rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 1px;
        color: #64748b;
        margin-bottom: 0.3rem;
    }
    .metric-card .value {
        font-size: 1.6rem;
        font-weight: 700;
        color: #0f172a;
    }

    /* Step indicator */
    .step-badge {
        display: inline-block;
        background: #2c5364;
        color: white;
        font-size: 0.7rem;
        font-weight: 700;
        padding: 0.25rem 0.7rem;
        border-radius: 20px;
        letter-spacing: 1px;
        text-transform: uppercase;
        margin-bottom: 0.5rem;
    }

    /* Progress section */
    .sim-progress {
        background: #fffbeb;
        border: 1px solid #fde68a;
        border-radius: 10px;
        padding: 1rem 1.5rem;
        margin: 0.5rem 0;
    }

    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}

    /* Sidebar styling */
    section[data-testid="stSidebar"] {
        background: #f1f5f9;
    }
    section[data-testid="stSidebar"] .stMarkdown h2 {
        color: #0f172a;
        font-size: 1.1rem;
        font-weight: 600;
        border-bottom: 2px solid #2c5364;
        padding-bottom: 0.5rem;
    }
</style>
""", unsafe_allow_html=True)


# ─────────────────────────────────────────────────────────
# HARDCODED SCHEME MAPPING
# ─────────────────────────────────────────────────────────
SCHEME_DATA = {
    "Original Names on web (AMFI)": [
        "Invesco India Banking and PSU Fund - Direct Plan -  Growth Option",
        "Invesco India Contra Fund - Direct Plan - Growth",
        "Invesco India Corporate Bond Fund - Direct Plan - Growth",
        "Invesco India Gilt Fund - Direct  Plan - Growth",
        "Invesco India Large & Mid Cap Fund - Direct Plan - Growth",
        "Invesco India Largecap Fund - Direct Plan - Growth",
        "Invesco India Midcap Fund - Direct Plan - Growth Option",
        "Invesco India Short Duration Fund - Direct Plan - Growth",
        "Invesco India Smallcap Fund - Direct Plan - Growth",
        "Invesco India Low Duration Fund - Direct Plan - Growth",
        "Invesco India Multicap Fund - Direct Plan - Growth Option",
        "Invesco India Contra Fund - Direct Plan - Growth",
        "Invesco India Midcap Fund - Direct Plan - Growth Option",
        "Invesco India Large & Mid Cap Fund - Direct Plan - Growth",
        "Invesco India Focused Fund - Direct Plan - Growth",
        "Invesco India ELSS Tax Saver Fund - Direct Plan - Growth",
        "Invesco India PSU Equity Fund - Direct Plan - Growth",
        "Invesco India Financial Services Fund - Direct Plan - Growth",
        "Invesco India Aggressive Hybrid Fund - Direct Plan - Growth",
        "Invesco India Equity Savings Fund - Direct Plan - Growth",
        "Invesco India Infrastructure Fund - Direct Plan - Growth Option",
        "Invesco India Money Market Fund - Direct Plan - Growth",
        "Invesco India Ultra Short Duration Fund - Direct Plan - Growth",
        "Invesco India Arbitrage Fund - Direct Plan - Growth Option",
        "Invesco India Balanced Advantage Fund - Direct Plan - Growth",
        "Invesco India ESG Integration Strategy Fund - Direct Plan - Growth",
        "Invesco India Flexi Cap Fund - Direct Plan - Growth",
        "Invesco India Medium Duration Fund - Direct - Growth",
        "Invesco India Overnight Fund - Direct Plan - Growth",
        "Invesco India Liquid Fund - Direct Plan - Growth",
        "Invesco India Credit Risk Fund - Direct Plan - Growth",
    ],
    "ISIN Div Payout/ISIN Growth": [
        "INF205K01KT4", "INF205K01LE4", "INF205K01RF8", "INF205K01SN0", "INF205K01MA0",
        "INF205K01LB0", "INF205K01MV6", "INF205K01UH8", "INF205K013T3", "INF205K01NY8",
        "INF205K01MS2", "INF205K01LE4", "INF205K01MV6", "INF205K01MA0", "INF205KA1213",
        "INF205K01NT8", "INF205K01NG5", "INF205K01KY4", "INF205K014Q7", "INF205KA1049",
        "INF205K01MD4", "INF205K01RY9", "INF205K01TH0", "INF205K01KR8", "INF205K01LN5",
        "INF205KA1338", "INF205KA1494", "INF205KA1429", "INF205KA1163", "INF205K01MF9",
        "INF205K01I83",
    ],
}


# ─────────────────────────────────────────────────────────
# HELPER FUNCTIONS
# ─────────────────────────────────────────────────────────

@st.cache_data(show_spinner=False)
def download_nav_data(from_date_str, to_date_str):
    """Download NAV data from AMFI India portal."""
    url = (
        f"https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx"
        f"?mf=42&frmdt={from_date_str}&todt={to_date_str}"
    )
    response = requests.get(url, timeout=60)
    content = response.content.decode("utf-8")
    lines = content.splitlines()

    header_index = 0
    for i, line in enumerate(lines):
        if line.startswith("Scheme Code"):
            header_index = i
            break

    data_str = "\n".join(lines[header_index:])
    df = pd.read_csv(StringIO(data_str), sep=";")
    return df, url


def compute_results(df, summary_df, valuation_date, future_dates, num_simulations, num_days, progress_bar, status_text):
    """Run the full simulation pipeline for all ISINs."""

    # Clean data
    df["Date"] = pd.to_datetime(df["Date"], format="%d-%b-%Y", errors="coerce")
    df["Net Asset Value"] = pd.to_numeric(df["Net Asset Value"], errors="coerce")

    # ── Step A: Build results_df with log-return stats ──
    results_df = summary_df.copy()
    results_df["NAV on Valuation Date"] = np.nan
    results_df["Mean Log Return"] = np.nan
    results_df["Std Dev Log Return"] = np.nan
    results_df["Average Trading Days (2020+)"] = np.nan

    for idx, row in summary_df.iterrows():
        isin = row["ISIN Div Payout/ISIN Growth"]
        filtered_df = df[df["ISIN Div Payout/ISIN Growth"] == isin].copy()
        filtered_df.drop(
            columns=["Scheme Code", "ISIN Div Reinvestment", "Repurchase Price", "Sale Price"],
            inplace=True, errors="ignore",
        )
        if filtered_df.empty:
            continue

        filtered_df.sort_values("Date", inplace=True)
        val_date = filtered_df["Date"].max()
        nav_val = filtered_df[filtered_df["Date"] == val_date]["Net Asset Value"].iloc[0]

        filtered_df["log_returns"] = np.log(
            filtered_df["Net Asset Value"] / filtered_df["Net Asset Value"].shift(1)
        )
        mean_lr = filtered_df["log_returns"].mean()
        std_lr = filtered_df["log_returns"].std()

        filtered_df["Year"] = filtered_df["Date"].dt.year
        trading_days = filtered_df.groupby("Year").size().reset_index(name="Trading_Days")
        recent_years = trading_days[trading_days["Year"] >= 2020]
        avg_td = recent_years["Trading_Days"].mean()

        results_df.at[idx, "NAV on Valuation Date"] = nav_val
        results_df.at[idx, "Mean Log Return"] = mean_lr
        results_df.at[idx, "Std Dev Log Return"] = std_lr
        results_df.at[idx, "Average Trading Days (2020+)"] = (
            round(avg_td, 2) if not np.isnan(avg_td) else 0
        )

    # ── Step B: Build summary_table with future trading-day indices ──
    summary_table = pd.DataFrame()
    summary_table["ISIN Div Payout/ISIN Growth"] = results_df["ISIN Div Payout/ISIN Growth"]
    summary_table["Average Trading Days (2020+)"] = results_df["Average Trading Days (2020+)"]

    future_date_cols = {}
    for date_str, future_dt in future_dates.items():
        day_diff = (future_dt - valuation_date).days
        col_vals = summary_table["Average Trading Days (2020+)"].apply(
            lambda x: round((x / 365) * day_diff) if not pd.isna(x) else np.nan
        )
        summary_table[date_str] = col_vals
        future_date_cols[date_str] = col_vals

    # ── Step C: Prepare output columns ──
    date_keys = list(future_dates.keys())
    for d in date_keys:
        results_df[f"Average Expected Future NAV - {d}"] = np.nan
        results_df[f"Median Expected Future NAV - {d}"] = np.nan
        results_df[f"CAGR basis - Average Expected Future NAV - {d}"] = np.nan
        results_df[f"CAGR basis - Median Expected Future NAV - {d}"] = np.nan
    results_df["Average CAGR (avg NAV)"] = np.nan
    results_df["Average CAGR (median NAV)"] = np.nan

    # ── Step D: Monte Carlo Simulation per ISIN ──
    total_isins = len(summary_table)

    for loop_idx, (idx, row) in enumerate(summary_table.iterrows()):
        isin = row["ISIN Div Payout/ISIN Growth"]
        scheme_name = summary_df.loc[idx, "Original Names on web (AMFI)"]
        pct = (loop_idx + 1) / total_isins
        progress_bar.progress(pct, text=f"Simulating {loop_idx+1}/{total_isins}")
        status_text.text(f"Running: {scheme_name[:60]}...")

        df_isin = df[df["ISIN Div Payout/ISIN Growth"] == isin].copy()
        if df_isin.empty:
            continue

        base_value = df_isin["Net Asset Value"].iloc[-1]
        if pd.isna(base_value):
            continue

        if "log_returns" not in df_isin.columns:
            df_isin["log_returns"] = np.log(
                df_isin["Net Asset Value"] / df_isin["Net Asset Value"].shift(1)
            )
        mean_lr = df_isin["log_returns"].mean()
        std_lr = df_isin["log_returns"].std()

        dt = 1

        # --- Vectorized simulation (much faster than row-by-row loop) ---
        sim_matrix = np.zeros((num_days, num_simulations))
        sim_matrix[0, :] = base_value

        for t in range(1, num_days):
            u1 = np.random.rand(num_simulations)
            u2 = np.random.rand(num_simulations)
            z = np.sqrt(-2 * np.log(u1)) * np.cos(2 * np.pi * u2)
            sim_matrix[t, :] = sim_matrix[t - 1, :] * np.exp(
                mean_lr * dt + std_lr * np.sqrt(dt) * z
            )

        sim_mean = sim_matrix.mean(axis=1)
        sim_median = np.median(sim_matrix, axis=1)

        # ── Extract NAV & CAGR at each future date ──
        avg_trading_days = float(row["Average Trading Days (2020+)"])
        cagr_avgs = []
        cagr_meds = []

        for d in date_keys:
            day_idx = int(row[d]) if not pd.isna(row[d]) else 0
            # Clamp index to valid range (fix the original bug with negative indices)
            day_idx = max(0, min(day_idx, num_days - 1))

            m_val = sim_mean[day_idx]
            med_val = sim_median[day_idx]

            results_df.loc[
                results_df["ISIN Div Payout/ISIN Growth"] == isin,
                f"Average Expected Future NAV - {d}",
            ] = m_val
            results_df.loc[
                results_df["ISIN Div Payout/ISIN Growth"] == isin,
                f"Median Expected Future NAV - {d}",
            ] = med_val

            # CAGR calculation (guard division by zero)
            years_fraction = day_idx / avg_trading_days if avg_trading_days else 1
            if years_fraction > 0 and base_value > 0 and m_val > 0:
                cagr_avg = (m_val / base_value) ** (1 / years_fraction) - 1
                cagr_med = (med_val / base_value) ** (1 / years_fraction) - 1
            else:
                cagr_avg = np.nan
                cagr_med = np.nan

            results_df.loc[
                results_df["ISIN Div Payout/ISIN Growth"] == isin,
                f"CAGR basis - Average Expected Future NAV - {d}",
            ] = cagr_avg
            results_df.loc[
                results_df["ISIN Div Payout/ISIN Growth"] == isin,
                f"CAGR basis - Median Expected Future NAV - {d}",
            ] = cagr_med

            cagr_avgs.append(cagr_avg)
            cagr_meds.append(cagr_med)

        # Average CAGR across all future dates
        valid_avgs = [x for x in cagr_avgs if not np.isnan(x)]
        valid_meds = [x for x in cagr_meds if not np.isnan(x)]
        results_df.loc[
            results_df["ISIN Div Payout/ISIN Growth"] == isin, "Average CAGR (avg NAV)"
        ] = (np.mean(valid_avgs) if valid_avgs else np.nan)
        results_df.loc[
            results_df["ISIN Div Payout/ISIN Growth"] == isin, "Average CAGR (median NAV)"
        ] = (np.mean(valid_meds) if valid_meds else np.nan)

    return results_df, summary_table


def generate_excel(results_df):
    """Generate an Excel file with results sheet + NAV verification sheet."""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
        # Sheet 1: Full simulation results
        results_df.to_excel(writer, sheet_name="Simulation Results", index=False)

        workbook = writer.book
        worksheet = writer.sheets["Simulation Results"]
        header_fmt = workbook.add_format({
            "bold": True, "bg_color": "#2c5364", "font_color": "white",
            "border": 1, "text_wrap": True, "valign": "vcenter",
        })
        for col_num, col_name in enumerate(results_df.columns):
            worksheet.write(0, col_num, col_name, header_fmt)
            worksheet.set_column(col_num, col_num, 22)

        # Sheet 2: NAV Verification (fund name + NAV on valuation date)
        verify_df = results_df[["Original Names on web (AMFI)", "ISIN Div Payout/ISIN Growth", "NAV on Valuation Date"]].copy()
        verify_df.to_excel(writer, sheet_name="NAV Verification", index=False)

        ws2 = writer.sheets["NAV Verification"]
        for col_num, col_name in enumerate(verify_df.columns):
            ws2.write(0, col_num, col_name, header_fmt)
        ws2.set_column(0, 0, 55)  # Fund name column wide
        ws2.set_column(1, 1, 28)  # ISIN
        ws2.set_column(2, 2, 22)  # NAV

    output.seek(0)
    return output


# ─────────────────────────────────────────────────────────
# SIDEBAR CONTROLS
# ─────────────────────────────────────────────────────────
with st.sidebar:
    st.markdown("## ⚙️ Configuration")

    st.markdown("---")
    st.markdown("**NAV Data Date Range**")
    st.caption("This builds the AMFI download URL automatically.")

    from_date = st.date_input(
        "From Date", value=date(2025, 11, 1),
        min_value=date(2020, 1, 1), max_value=date(2026, 12, 31),
        help="Start date for NAV history download",
    )
    to_date = st.date_input(
        "To Date (Valuation Date)", value=date(2026, 3, 31),
        min_value=date(2020, 1, 1), max_value=date(2026, 12, 31),
        help="End date — also used as the valuation date for simulation",
    )

    # Show the constructed URL
    from_date_str = from_date.strftime("%d-%b-%Y")
    to_date_str = to_date.strftime("%d-%b-%Y")
    constructed_url = (
        f"https://portal.amfiindia.com/DownloadNAVHistoryReport_Po.aspx"
        f"?mf=42&frmdt={from_date_str}&todt={to_date_str}"
    )
    st.code(constructed_url, language=None)

    st.markdown("---")
    st.markdown("**Future Target Dates**")
    st.caption("Dates for which expected NAVs and CAGR will be projected.")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
        fd1 = st.date_input("Target 1", value=date(2026, 2, 28))
        fd2 = st.date_input("Target 2", value=date(2027, 2, 28))
    with col_f2:
        fd3 = st.date_input("Target 3", value=date(2028, 2, 28))
        fd4 = st.date_input("Target 4", value=date(2029, 2, 28))

    st.markdown("---")
    st.markdown("**Simulation Parameters**")
    num_simulations = st.slider("Number of Paths", 100, 2000, 1000, step=100)
    num_days = st.slider("Simulation Horizon (days)", 500, 2000, 1600, step=100)

    st.markdown("---")
    run_btn = st.button("🚀 Run Simulation", use_container_width=True, type="primary")


# ─────────────────────────────────────────────────────────
# MAIN CONTENT
# ─────────────────────────────────────────────────────────

# Hero banner
st.markdown("""
<div class="hero-banner">
    <h1>📈 Invesco NAV Simulation Engine</h1>
    <p>Monte Carlo simulation on Invesco India mutual fund NAVs &nbsp;·&nbsp; Geometric Brownian Motion &nbsp;·&nbsp; Box-Muller sampling</p>
</div>
""", unsafe_allow_html=True)

# Metric cards for current config
mc1, mc2, mc3, mc4 = st.columns(4)
with mc1:
    st.markdown(f"""<div class="metric-card">
        <div class="label">Valuation Date</div>
        <div class="value">{to_date.strftime('%d %b %Y')}</div>
    </div>""", unsafe_allow_html=True)
with mc2:
    st.markdown(f"""<div class="metric-card">
        <div class="label">Simulation Paths</div>
        <div class="value">{num_simulations:,}</div>
    </div>""", unsafe_allow_html=True)
with mc3:
    st.markdown(f"""<div class="metric-card">
        <div class="label">Horizon</div>
        <div class="value">{num_days:,} days</div>
    </div>""", unsafe_allow_html=True)
with mc4:
    st.markdown(f"""<div class="metric-card">
        <div class="label">Schemes</div>
        <div class="value">31</div>
    </div>""", unsafe_allow_html=True)

st.markdown("")

# ─────────────────────────────────────────────────────────
# EXECUTION
# ─────────────────────────────────────────────────────────
if run_btn:
    summary_df = pd.DataFrame(SCHEME_DATA)

    valuation_date = pd.to_datetime(to_date)
    future_dates = {
        fd.strftime("%d-%m-%Y"): pd.to_datetime(fd)
        for fd in [fd1, fd2, fd3, fd4]
    }

    # ── STEP 1: Download ──
    st.markdown('<div class="step-badge">Step 1 of 3</div>', unsafe_allow_html=True)
    st.subheader("Downloading NAV Data from AMFI India")

    with st.spinner("Fetching data from AMFI portal..."):
        try:
            df_raw, url_used = download_nav_data(from_date_str, to_date_str)
        except Exception as e:
            st.error(f"Failed to download data. Check your internet connection.\n\nError: {e}")
            st.stop()

    total_rows = len(df_raw)
    st.success(f"Downloaded **{total_rows:,}** rows from AMFI portal.")

    with st.expander("Preview raw NAV data", expanded=False):
        st.dataframe(df_raw.head(20), use_container_width=True, height=300)

    # ── STEP 2: Simulation ──
    st.markdown("---")
    st.markdown('<div class="step-badge">Step 2 of 3</div>', unsafe_allow_html=True)
    st.subheader("Running Monte Carlo Simulations")

    progress_bar = st.progress(0, text="Preparing...")
    status_text = st.empty()

    start_time = time.time()
    results_df, summary_table = compute_results(
        df_raw.copy(), summary_df, valuation_date, future_dates,
        num_simulations, num_days, progress_bar, status_text,
    )
    elapsed = time.time() - start_time

    progress_bar.progress(1.0, text="All simulations complete!")
    status_text.text(f"Finished in {elapsed:.1f} seconds.")

    # ── STEP 3: Results ──
    st.markdown("---")
    st.markdown('<div class="step-badge">Step 3 of 3</div>', unsafe_allow_html=True)
    st.subheader("Simulation Results")

    # Show key output columns
    display_cols = [
        "Original Names on web (AMFI)",
        "ISIN Div Payout/ISIN Growth",
        "NAV on Valuation Date",
        "Mean Log Return",
        "Std Dev Log Return",
        "Average Trading Days (2020+)",
    ]
    date_keys = list(future_dates.keys())
    for d in date_keys:
        display_cols.append(f"Average Expected Future NAV - {d}")
        display_cols.append(f"Median Expected Future NAV - {d}")
    for d in date_keys:
        display_cols.append(f"CAGR basis - Average Expected Future NAV - {d}")
        display_cols.append(f"CAGR basis - Median Expected Future NAV - {d}")
    display_cols += ["Average CAGR (avg NAV)", "Average CAGR (median NAV)"]

    # Filter to existing columns
    display_cols = [c for c in display_cols if c in results_df.columns]

    # Show tabs: Summary, NAV Projections, CAGR, Trading Days
    tab_summary, tab_nav, tab_cagr, tab_td = st.tabs([
        "📋 Full Results", "💰 NAV Projections", "📊 CAGR Analysis", "📅 Trading Days Map"
    ])

    with tab_summary:
        st.dataframe(
            results_df[display_cols],
            use_container_width=True,
            height=500,
        )

    with tab_nav:
        nav_cols = ["Original Names on web (AMFI)", "NAV on Valuation Date"]
        for d in date_keys:
            nav_cols += [f"Average Expected Future NAV - {d}", f"Median Expected Future NAV - {d}"]
        nav_cols = [c for c in nav_cols if c in results_df.columns]
        st.dataframe(results_df[nav_cols], use_container_width=True, height=500)

    with tab_cagr:
        cagr_cols = ["Original Names on web (AMFI)"]
        for d in date_keys:
            cagr_cols += [
                f"CAGR basis - Average Expected Future NAV - {d}",
                f"CAGR basis - Median Expected Future NAV - {d}",
            ]
        cagr_cols += ["Average CAGR (avg NAV)", "Average CAGR (median NAV)"]
        cagr_cols = [c for c in cagr_cols if c in results_df.columns]

        styled_cagr = results_df[cagr_cols].copy()
        # Format CAGR columns as percentages for display
        for c in cagr_cols[1:]:
            styled_cagr[c] = styled_cagr[c].apply(
                lambda x: f"{x:.2%}" if pd.notna(x) else "N/A"
            )
        st.dataframe(styled_cagr, use_container_width=True, height=500)

    with tab_td:
        st.dataframe(summary_table, use_container_width=True, height=500)

    # ── Excel Download ──
    st.markdown("---")
    st.subheader("📥 Export Results")

    col_dl1, col_dl2 = st.columns(2)

    with col_dl1:
        excel_data = generate_excel(results_df)
        st.download_button(
            label="⬇️  Download Excel Report",
            data=excel_data,
            file_name=f"Invesco_Simulation_{to_date.strftime('%d-%m-%Y')}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True,
            type="primary",
        )
        st.caption("Sheet 1: Simulation Results  ·  Sheet 2: NAV Verification (fund name + NAV)")

    with col_dl2:
        csv_data = results_df.to_csv(index=False).encode("utf-8")
        st.download_button(
            label="⬇️  Download CSV Summary",
            data=csv_data,
            file_name=f"Invesco_Simulation_{to_date.strftime('%d-%m-%Y')}.csv",
            mime="text/csv",
            use_container_width=True,
        )
        st.caption("Flat CSV of the results table")

else:
    # Landing state — show instructions
    st.info(
        "👈 **Configure the dates and parameters in the sidebar, then press Run Simulation.** "
        "The app will download NAV data from AMFI India, run Monte Carlo simulations for all 31 "
        "Invesco schemes, and let you download the results as Excel.",
        icon="ℹ️",
    )

    with st.expander("How this simulation works", expanded=True):
        st.markdown("""
**Pipeline overview:**

1. **NAV Download** — Fetches historical NAV data for Invesco Mutual Fund (mf=42) from the AMFI India portal between your chosen dates.

2. **Log-Return Statistics** — For each of the 31 tracked schemes, computes the mean and standard deviation of daily log-returns from the downloaded NAV history.

3. **Trading Days Estimation** — Calculates average trading days per quarter/year from 2020 onwards, then maps each future target date to a simulation day-index.

4. **Monte Carlo Simulation** — For each scheme, runs N simulation paths (default 1,000) over M days (default 1,600) using Geometric Brownian Motion with Box-Muller normal sampling.

5. **Expected NAV & CAGR** — Extracts the mean and median simulated NAV at each future target date, then computes annualized CAGR for both.

6. **Export** — Packages everything into a downloadable Excel file with a summary sheet and per-ISIN simulation data.
        """)

    with st.expander("Tracked Invesco schemes (31)", expanded=False):
        st.dataframe(
            pd.DataFrame(SCHEME_DATA),
            use_container_width=True,
            height=400,
        )
