import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Combs-Weschler Screener", page_icon="📊", layout="wide")

# ── Load Data ──
@st.cache_data(ttl=3600)
def load_data():
    paths = ['data/screener_results.csv', '/Users/brendonmuur/Desktop/data/screener_results.csv']
    for p in paths:
        if os.path.exists(p):
            df = pd.read_csv(p, index_col=0)
            return df
    st.error("No data found. Run the notebook first to generate data/screener_results.csv")
    st.stop()

df = load_data()

# ── Helper Functions ──
def signal(val, green, yellow):
    if pd.isna(val): return "⚪"
    if val >= green: return "🟢"
    if val >= yellow: return "🟡"
    return "🔴"

def verdict(combs, weschler, combined, quality):
    if combined >= 60 and quality >= 14:
        return "✅ HIGH CONVICTION", "Quality business at attractive valuation"
    elif combined >= 55 or (combs >= 65 and quality >= 12):
        return "⚠️ RESEARCH FURTHER", "Promising but needs deeper due diligence"
    elif combined >= 50 and quality >= 10:
        return "🟡 MONITOR", "Decent on one lens, watch for catalyst"
    elif quality < 10 and weschler > combs:
        return "❌ VALUE TRAP RISK", "Low quality + distressed price = caution"
    else:
        return "❌ NOT COMPELLING", "Neither lens strongly favours this stock"

def fmt_pct(val):
    return f"{val*100:.1f}%" if not pd.isna(val) else "—"

def _score_color_str(val, green, yellow):
    if pd.isna(val): return '#999'
    if val >= green: return '#2e7d32'
    if val >= yellow: return '#f57f17'
    return '#c62828'

def fmt_score(val, max_val):
    return f"{val:.1f}/{max_val}" if not pd.isna(val) else "—"

# ── Sidebar: Cheat Sheet ──
with st.sidebar:
    st.markdown("## 📖 Score Cheat Sheet")

    st.markdown("### Combs Score (0–100)")
    st.markdown("*Is this a great business?*")
    cheat_combs = pd.DataFrame({
        'Sub-Score': ['Unit Economics', 'Frictionless Ops', 'Capital Allocation', 'Moat Strength', '**TOTAL**'],
        'Max': ['/25', '/25', '/25', '/25', '**/100**'],
        '🟢': ['>18', '>18', '>18', '>18', '**>65**'],
        '🟡': ['12–18', '12–18', '12–18', '12–18', '**45–65**'],
        '🔴': ['<12', '<12', '<12', '<12', '**<45**'],
    })
    st.dataframe(cheat_combs, hide_index=True, use_container_width=True)

    st.markdown("### Weschler Score (0–100)")
    st.markdown("*Is this mispriced?*")
    cheat_weschler = pd.DataFrame({
        'Sub-Score': ['Variant Perception', 'Complexity Discount', 'Distressed Value', 'Business Quality', 'LT Compounding', '**TOTAL**'],
        'Max': ['/20', '/20', '/20', '/20', '/20', '**/100**'],
        '🟢': ['>14', '>14', '>14', '>14', '>14', '**>60**'],
        '🟡': ['8–14', '8–14', '8–14', '8–14', '8–14', '**40–60**'],
        '🔴': ['<8', '<8', '<8', '<8', '<8', '**<40**'],
    })
    st.dataframe(cheat_weschler, hide_index=True, use_container_width=True)

    st.markdown("### Verdicts")
    st.markdown("""
    - ✅ **HIGH CONVICTION** — Combined >60 + Quality >14
    - ⚠️ **RESEARCH FURTHER** — Promising, needs work
    - 🟡 **MONITOR** — Watch for catalyst
    - ❌ **VALUE TRAP** — Low quality + distress
    - ❌ **NOT COMPELLING** — Neither lens favours
    """)

    st.markdown("---")
    st.markdown("### ★ = Highest Weight")
    st.markdown("""
    **Combs key metrics:**
    - ★ ROIC (35% of Cap Alloc)
    - ★ Gross/Op Margin (30% each of Unit Econ)
    - ★ Rev CAGR (40% of Frictionless)

    **Weschler key metrics:**
    - ★ 52w Drawdown (30% of Distressed)
    - ★ PE Gap/Sector (35% each of Variant)
    - ★ ROIC (30% of Quality)
    - ★ Earn/Rev CAGR 5y (30% each of Compounding)
    """)

# ── Main Content ──
st.title("📊 Combs-Weschler S&P 500 Screener")

last_modified = ""
for p in ['data/screener_results.csv', '/Users/brendonmuur/Desktop/data/screener_results.csv']:
    if os.path.exists(p):
        import datetime
        mtime = os.path.getmtime(p)
        last_modified = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
        break
st.caption(f"Last updated: {last_modified} · {len(df)} stocks analysed")

# ── Tab Layout ──
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏆 Rankings", "🎯 Deep Dive", "📈 Scatter Plot", "🔥 Conviction", "📊 Sector Heatmap"])

# Shared state for cross-tab navigation
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = 'AAPL'

# ══════════════════════════════════════════════
# TAB 1: Rankings
# ══════════════════════════════════════════════
with tab1:
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Top Combined", f"{df['combined_score'].idxmax()} ({df['combined_score'].max():.1f})")
    with col2:
        st.metric("Top Combs", f"{df['combs_score'].idxmax()} ({df['combs_score'].max():.1f})")
    with col3:
        st.metric("Top Weschler", f"{df['weschler_score'].idxmax()} ({df['weschler_score'].max():.1f})")

    st.markdown("---")

    ranking_type = st.selectbox("Rank by:", ["Combined Score", "Combs Score (Best Businesses)", "Weschler Score (Mispriced/Contrarian)"])
    sector_filter = st.multiselect("Filter by sector:", sorted(df['sector'].dropna().unique()), default=[])

    filtered = df.copy()
    if sector_filter:
        filtered = filtered[filtered['sector'].isin(sector_filter)]

    score_col = {'Combined Score': 'combined_score', 'Combs Score (Best Businesses)': 'combs_score', 'Weschler Score (Mispriced/Contrarian)': 'weschler_score'}[ranking_type]

    top_n = st.slider("Show top N:", 10, 50, 20)
    ranking = filtered.nlargest(top_n, score_col)[['company','sector','combs_score','weschler_score','combined_score','trailing_pe','roic','fcf_yield','operating_margin','drawdown_52w','revenue_cagr_3y']].copy()

    # Render as interactive table with clickable tickers
    st.markdown("*Click any ticker to open its Deep Dive*")

    # Table header
    header_cols = st.columns([1, 2.5, 1.5, 0.8, 0.8, 0.8, 0.7, 0.8, 0.8, 0.8, 0.8, 0.9])
    headers = ['#', 'Company', 'Sector', 'Combs', 'Wesch', 'Comb', 'PE', 'ROIC', 'FCF%', 'OpMar', '52wDr', 'RevGr']
    for col, h in zip(header_cols, headers):
        col.markdown(f"**{h}**")

    st.markdown("---")

    for i, (ticker, row) in enumerate(ranking.iterrows(), 1):
        cols = st.columns([1, 2.5, 1.5, 0.8, 0.8, 0.8, 0.7, 0.8, 0.8, 0.8, 0.8, 0.9])

        # Ticker button — clicking sets the selected ticker and user can switch to Deep Dive tab
        if cols[0].button(f"**{ticker}**", key=f"rank_{ticker}", help=f"Deep dive {ticker}"):
            st.session_state.selected_ticker = ticker
            st.toast(f"🎯 {ticker} selected — switch to Deep Dive tab", icon="🎯")

        cols[1].caption(str(row.get('company', ''))[:25])
        cols[2].caption(str(row.get('sector', ''))[:15])

        # Colour-coded scores
        cs, ws, cb = row['combs_score'], row['weschler_score'], row['combined_score']
        cols[3].markdown(f"<span style='color:{_score_color_str(cs, 65, 45)};font-weight:700'>{cs:.0f}</span>", unsafe_allow_html=True)
        cols[4].markdown(f"<span style='color:{_score_color_str(ws, 60, 40)};font-weight:700'>{ws:.0f}</span>", unsafe_allow_html=True)
        cols[5].markdown(f"<span style='color:{_score_color_str(cb, 60, 50)};font-weight:700'>{cb:.1f}</span>", unsafe_allow_html=True)

        cols[6].caption(f"{row['trailing_pe']:.0f}" if not pd.isna(row['trailing_pe']) else "—")
        cols[7].caption(fmt_pct(row.get('roic')))
        cols[8].caption(fmt_pct(row.get('fcf_yield')))
        cols[9].caption(fmt_pct(row.get('operating_margin')))
        cols[10].caption(fmt_pct(row.get('drawdown_52w')))
        cols[11].caption(fmt_pct(row.get('revenue_cagr_3y')))

# ══════════════════════════════════════════════
# TAB 2: Deep Dive
# ══════════════════════════════════════════════
with tab2:
    ticker_options = sorted(df.index.tolist())
    # Use session state ticker if set from Rankings tab
    default_ticker = st.session_state.get('selected_ticker', 'AAPL')
    default_idx = ticker_options.index(default_ticker) if default_ticker in ticker_options else 0
    selected = st.selectbox("Select ticker:", ticker_options, index=default_idx, key="deep_dive_ticker")
    # Sync back to session state
    st.session_state.selected_ticker = selected

    if selected and selected in df.index:
        r = df.loc[selected]
        cs, ws, cb = r['combs_score'], r['weschler_score'], r['combined_score']
        wq = r.get('weschler_quality', 0)
        v_label, v_desc = verdict(cs, ws, cb, wq)

        # Header
        st.markdown(f"# {selected} — {r.get('company', '')}")
        st.markdown(f"**{r.get('sector', '')}** · Market Cap: ${r['market_cap']/1e9:.1f}B" if not pd.isna(r['market_cap']) else "")

        desc = r.get('description', '')
        if isinstance(desc, str) and len(desc) > 10:
            with st.expander("Business Description"):
                st.write(desc)

        # Verdict banner
        if "HIGH CONVICTION" in v_label:
            st.success(f"**{v_label}** — {v_desc}")
        elif "RESEARCH" in v_label:
            st.warning(f"**{v_label}** — {v_desc}")
        elif "MONITOR" in v_label:
            st.info(f"**{v_label}** — {v_desc}")
        else:
            st.error(f"**{v_label}** — {v_desc}")

        # Scores
        col1, col2, col3 = st.columns(3)
        col1.metric("Combs Score", f"{cs:.1f}/100", delta=f"{signal(cs,65,45)}")
        col2.metric("Weschler Score", f"{ws:.1f}/100", delta=f"{signal(ws,60,40)}")
        col3.metric("Combined Score", f"{cb:.1f}/100", delta=f"{signal(cb,60,50)}")

        st.markdown("---")

        # Combs Breakdown
        left, right = st.columns(2)
        with left:
            st.markdown("### 🎯 Combs — *Is this a great business?*")

            combs_data = [
                ("Unit Economics", r['combs_unit_economics'], 25, 18, 12),
                ("Frictionless Ops", r['combs_frictionless'], 25, 18, 12),
                ("Capital Allocation", r['combs_capital_allocation'], 25, 18, 12),
                ("Moat Strength", r['combs_moat'], 25, 18, 12),
            ]
            for name, val, mx, g, y in combs_data:
                st.markdown(f"{signal(val, g, y)} **{name}**: {val:.1f}/{mx}")

            st.markdown("**Key Metrics:**")
            metrics_c = [
                ("★ ROIC", r.get('roic'), True), ("★ Gross Margin", r.get('gross_margin'), True),
                ("★ Op Margin", r.get('operating_margin'), True), ("ROE", r.get('roe'), True),
                ("FCF Yield", r.get('fcf_yield'), True), ("★ Rev CAGR 3y", r.get('revenue_cagr_3y'), True),
                ("Margin Stability", r.get('margin_stability'), False),
            ]
            for name, val, is_pct in metrics_c:
                if not pd.isna(val):
                    display = fmt_pct(val) if is_pct else f"{val:.4f}"
                    st.markdown(f"- {name}: `{display}`")

        # Weschler Breakdown
        with right:
            st.markdown("### 🔍 Weschler — *Is this mispriced?*")

            weschler_data = [
                ("Variant Perception", r['weschler_variant'], 20, 14, 8),
                ("Complexity Discount", r['weschler_complexity'], 20, 14, 8),
                ("Distressed Value", r['weschler_distressed'], 20, 14, 8),
                ("Business Quality", r['weschler_quality'], 20, 14, 8),
                ("LT Compounding", r['weschler_compounding'], 20, 14, 8),
            ]
            for name, val, mx, g, y in weschler_data:
                extra = " ← quality concern" if name == "Business Quality" and val < 10 else ""
                st.markdown(f"{signal(val, g, y)} **{name}**: {val:.1f}/{mx}{extra}")

            st.markdown("**Key Metrics:**")
            metrics_w = [
                ("★ 52w Drawdown", r.get('drawdown_52w'), True), ("vs 200d MA", r.get('price_vs_200ma'), True),
                ("★ PE", r.get('trailing_pe'), False), ("Fwd PE", r.get('forward_pe'), False),
                ("Short Interest", r.get('short_percent'), True), ("Earn Consistency", r.get('earnings_consistency'), False),
                ("★ Earn CAGR 5y", r.get('earnings_cagr_5y'), True), ("★ Rev CAGR 5y", r.get('revenue_cagr_5y'), True),
            ]
            for name, val, is_pct in metrics_w:
                if not pd.isna(val):
                    display = fmt_pct(val) if is_pct else f"{val:.2f}"
                    st.markdown(f"- {name}: `{display}`")

        # Sector rank
        sector = r.get('sector')
        if sector and not pd.isna(sector):
            peers = df[df['sector'] == sector]
            cr = int((peers['combs_score'] >= cs).sum())
            wr = int((peers['weschler_score'] >= ws).sum())
            st.markdown(f"**Sector Rank** ({sector}, {len(peers)} peers): Combs #{cr} · Weschler #{wr}")

# ══════════════════════════════════════════════
# TAB 3: Scatter Plot
# ══════════════════════════════════════════════
with tab3:
    st.markdown("### Combs vs Weschler — Quadrant Analysis")
    st.markdown("Dots sized by market cap. Top 10 combined picks labelled.")

    plot_df = df.dropna(subset=['combs_score','weschler_score','market_cap']).copy()
    plot_df['log_mcap'] = np.log10(plot_df['market_cap'].clip(lower=1e8))
    plot_df['size'] = ((plot_df['log_mcap'] - plot_df['log_mcap'].min()) / (plot_df['log_mcap'].max() - plot_df['log_mcap'].min())) * 30 + 3
    plot_df['label'] = plot_df.index
    plot_df['hover'] = plot_df.apply(lambda x: f"{x.name}: {x.get('company','')} | C:{x['combs_score']:.0f} W:{x['weschler_score']:.0f} Comb:{x['combined_score']:.0f}", axis=1)

    fig = px.scatter(
        plot_df, x='combs_score', y='weschler_score', color='sector',
        size='size', hover_name='hover', size_max=25, opacity=0.7,
        labels={'combs_score': 'Combs Score (Business Quality)', 'weschler_score': 'Weschler Score (Mispricing)'},
    )

    med_c = plot_df['combs_score'].median()
    med_w = plot_df['weschler_score'].median()
    fig.add_vline(x=med_c, line_dash="dash", line_color="grey", opacity=0.5)
    fig.add_hline(y=med_w, line_dash="dash", line_color="grey", opacity=0.5)

    fig.add_annotation(x=plot_df['combs_score'].max()-2, y=plot_df['weschler_score'].max()-1, text="BOTH AGREE<br>(Highest Conviction)", showarrow=False, font=dict(color="darkgreen", size=11))
    fig.add_annotation(x=plot_df['combs_score'].min()+2, y=plot_df['weschler_score'].max()-1, text="WESCHLER<br>FAVOURITES", showarrow=False, font=dict(color="darkblue", size=11))
    fig.add_annotation(x=plot_df['combs_score'].max()-2, y=plot_df['weschler_score'].min()+1, text="COMBS<br>FAVOURITES", showarrow=False, font=dict(color="darkorange", size=11))
    fig.add_annotation(x=plot_df['combs_score'].min()+2, y=plot_df['weschler_score'].min()+1, text="NEITHER<br>FAVOURS", showarrow=False, font=dict(color="darkred", size=11))

    for t, row in plot_df.nlargest(10, 'combined_score').iterrows():
        fig.add_annotation(x=row['combs_score'], y=row['weschler_score'], text=t, showarrow=True, arrowhead=0, ax=15, ay=-15, font=dict(size=10, color="black"))

    fig.update_layout(height=700, legend=dict(orientation="h", yanchor="bottom", y=-0.2))
    st.plotly_chart(fig, use_container_width=True)

# ══════════════════════════════════════════════
# TAB 4: Conviction
# ══════════════════════════════════════════════
with tab4:
    st.markdown("### 🔥 Highest Conviction — Combs ≥60 AND Weschler ≥60")
    st.markdown("*Both lenses agree: quality business at attractive price*")

    conviction = df[(df['combs_score'] >= 60) & (df['weschler_score'] >= 60)].sort_values('combined_score', ascending=False).copy()

    if len(conviction) > 0:
        st.metric("Conviction Stocks", len(conviction))

        display_conv = conviction[['company','sector','combs_score','weschler_score','combined_score','roic','fcf_yield','drawdown_52w','trailing_pe']].copy()
        display_conv['roic'] = display_conv['roic'].apply(fmt_pct)
        display_conv['fcf_yield'] = display_conv['fcf_yield'].apply(fmt_pct)
        display_conv['drawdown_52w'] = display_conv['drawdown_52w'].apply(fmt_pct)
        display_conv['trailing_pe'] = display_conv['trailing_pe'].apply(lambda x: f"{x:.1f}" if not pd.isna(x) else "—")
        display_conv.columns = ['Company','Sector','Combs','Weschler','Combined','ROIC','FCF Yield','52w Draw','PE']

        st.dataframe(
            display_conv.style.background_gradient(subset=['Combs','Weschler','Combined'], cmap='RdYlGn', vmin=50, vmax=75),
            use_container_width=True
        )

        for t, r in conviction.head(5).iterrows():
            wq = r.get('weschler_quality', 0)
            v_label, v_desc = verdict(r['combs_score'], r['weschler_score'], r['combined_score'], wq)
            with st.expander(f"{t} — {r.get('company','')} ({r['combined_score']:.1f})"):
                c1, c2, c3 = st.columns(3)
                c1.metric("Combs", f"{r['combs_score']:.1f}")
                c2.metric("Weschler", f"{r['weschler_score']:.1f}")
                c3.metric("Combined", f"{r['combined_score']:.1f}")
                st.markdown(f"**{v_label}** — {v_desc}")
                st.markdown(f"ROIC: {fmt_pct(r.get('roic'))} · FCF Yield: {fmt_pct(r.get('fcf_yield'))} · 52w Draw: {fmt_pct(r.get('drawdown_52w'))} · PE: {r.get('trailing_pe','—'):.1f}" if not pd.isna(r.get('trailing_pe')) else "")
    else:
        st.warning("No stocks currently meet both thresholds (Combs ≥60 AND Weschler ≥60)")

# ══════════════════════════════════════════════
# TAB 5: Sector Heatmap
# ══════════════════════════════════════════════
with tab5:
    st.markdown("### Sector Score Heatmap")

    sector_agg = df.groupby('sector').agg({
        'combs_score': 'mean', 'weschler_score': 'mean', 'combined_score': 'mean',
        'combs_unit_economics': 'mean', 'combs_frictionless': 'mean',
        'combs_capital_allocation': 'mean', 'combs_moat': 'mean',
        'weschler_variant': 'mean', 'weschler_complexity': 'mean',
        'weschler_distressed': 'mean', 'weschler_quality': 'mean',
        'weschler_compounding': 'mean',
    }).round(1).sort_values('combined_score', ascending=False)

    fig_heat = go.Figure(data=go.Heatmap(
        z=sector_agg[['combs_score','weschler_score','combined_score']].values,
        x=['Combs Mean', 'Weschler Mean', 'Combined Mean'],
        y=sector_agg.index.tolist(),
        text=sector_agg[['combs_score','weschler_score','combined_score']].values.round(1),
        texttemplate="%{text}",
        colorscale='RdYlGn', zmin=35, zmax=65,
    ))
    fig_heat.update_layout(height=500, title="Average Scores by Sector")
    st.plotly_chart(fig_heat, use_container_width=True)

    sub_cols = ['combs_unit_economics','combs_frictionless','combs_capital_allocation','combs_moat',
                'weschler_variant','weschler_complexity','weschler_distressed','weschler_quality','weschler_compounding']
    sub_labels = ['Unit Econ','Frictionless','Cap Alloc','Moat','Variant','Complexity','Distressed','Quality','Compounding']

    fig_sub = go.Figure(data=go.Heatmap(
        z=sector_agg[sub_cols].values,
        x=sub_labels,
        y=sector_agg.index.tolist(),
        text=sector_agg[sub_cols].values.round(1),
        texttemplate="%{text}",
        colorscale='RdYlGn',
    ))
    fig_sub.update_layout(height=500, title="Sub-Score Breakdown by Sector")
    st.plotly_chart(fig_sub, use_container_width=True)

# ── Footer ──
st.markdown("---")
st.markdown("*Combs-Weschler Screener · Data from Yahoo Finance via yfinance · This tool identifies candidates for research, not buy signals.*")
