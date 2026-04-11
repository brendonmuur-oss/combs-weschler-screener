import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
import os

st.set_page_config(page_title="Combs-Weschler Screener", layout="wide")

# ── Load Data ──
@st.cache_data(ttl=3600)
def load_data():
    paths = ['data/screener_results.csv', '/Users/brendonmuur/Desktop/data/screener_results.csv']
    for p in paths:
        if os.path.exists(p):
            return pd.read_csv(p, index_col=0)
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

def render_deep_dive(selected, show_back_button=False):
    """Render full deep dive for a ticker. Reusable across pages."""
    if selected not in df.index:
        st.error(f"{selected} not found")
        return

    r = df.loc[selected]
    cs, ws, cb = r['combs_score'], r['weschler_score'], r['combined_score']
    wq = r.get('weschler_quality', 0)
    v_label, v_desc = verdict(cs, ws, cb, wq)

    if show_back_button:
        if st.button("← Back to Rankings", key="back_btn"):
            st.session_state.navigate_to_deep_dive = False
            st.rerun()

    st.markdown(f"# 🎯 {selected} — {r.get('company', '')}")
    st.markdown(f"**{r.get('sector', '')}** · Market Cap: ${r['market_cap']/1e9:.1f}B" if not pd.isna(r['market_cap']) else "")

    desc = r.get('description', '')
    if isinstance(desc, str) and len(desc) > 10:
        with st.expander("Business Description"):
            st.write(desc)

    if "HIGH CONVICTION" in v_label:
        st.success(f"**{v_label}** — {v_desc}")
    elif "RESEARCH" in v_label:
        st.warning(f"**{v_label}** — {v_desc}")
    elif "MONITOR" in v_label:
        st.info(f"**{v_label}** — {v_desc}")
    else:
        st.error(f"**{v_label}** — {v_desc}")

    col1, col2, col3 = st.columns(3)
    col1.metric("Combs Score", f"{cs:.1f}/100", delta=f"{signal(cs,65,45)}")
    col2.metric("Weschler Score", f"{ws:.1f}/100", delta=f"{signal(ws,60,40)}")
    col3.metric("Combined Score", f"{cb:.1f}/100", delta=f"{signal(cb,60,50)}")

    st.markdown("---")

    left, right = st.columns(2)
    with left:
        st.markdown("### 🎯 Combs — *Great business?*")
        for name, val, mx, g, y in [("Unit Economics", r['combs_unit_economics'], 25, 18, 12), ("Frictionless Ops", r['combs_frictionless'], 25, 18, 12), ("Capital Allocation", r['combs_capital_allocation'], 25, 18, 12), ("Moat Strength", r['combs_moat'], 25, 18, 12)]:
            st.markdown(f"{signal(val, g, y)} **{name}**: {val:.1f}/{mx}")
        st.markdown("**Key Metrics:**")
        for name, val, is_pct in [("★ ROIC", r.get('roic'), True), ("★ Gross Margin", r.get('gross_margin'), True), ("★ Op Margin", r.get('operating_margin'), True), ("ROE", r.get('roe'), True), ("FCF Yield", r.get('fcf_yield'), True), ("★ Rev CAGR 3y", r.get('revenue_cagr_3y'), True)]:
            if not pd.isna(val):
                st.markdown(f"- {name}: `{fmt_pct(val) if is_pct else f'{val:.4f}'}`")

    with right:
        st.markdown("### 🔍 Weschler — *Mispriced?*")
        for name, val, mx, g, y in [("Variant Perception", r['weschler_variant'], 20, 14, 8), ("Complexity Discount", r['weschler_complexity'], 20, 14, 8), ("Distressed Value", r['weschler_distressed'], 20, 14, 8), ("Business Quality", r['weschler_quality'], 20, 14, 8), ("LT Compounding", r['weschler_compounding'], 20, 14, 8)]:
            extra = " ← quality concern" if name == "Business Quality" and val < 10 else ""
            st.markdown(f"{signal(val, g, y)} **{name}**: {val:.1f}/{mx}{extra}")
        st.markdown("**Key Metrics:**")
        for name, val, is_pct in [("★ 52w Drawdown", r.get('drawdown_52w'), True), ("vs 200d MA", r.get('price_vs_200ma'), True), ("★ PE", r.get('trailing_pe'), False), ("Short Interest", r.get('short_percent'), True), ("★ Earn CAGR 5y", r.get('earnings_cagr_5y'), True), ("★ Rev CAGR 5y", r.get('revenue_cagr_5y'), True)]:
            if not pd.isna(val):
                st.markdown(f"- {name}: `{fmt_pct(val) if is_pct else f'{val:.2f}'}`")

    sector = r.get('sector')
    if sector and not pd.isna(sector):
        peers = df[df['sector'] == sector]
        cr = int((peers['combs_score'] >= cs).sum())
        wr = int((peers['weschler_score'] >= ws).sum())
        st.markdown(f"**Sector Rank** ({sector}, {len(peers)} peers): Combs #{cr} · Weschler #{wr}")

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
    st.markdown("★ = highest-weighted metric in sub-score")

# ── Main Content ──
# 1) Remove bar chart emoji from title
st.title("Combs-Weschler S&P 500 Screener")

last_modified = ""
for p in ['data/screener_results.csv', '/Users/brendonmuur/Desktop/data/screener_results.csv']:
    if os.path.exists(p):
        import datetime
        mtime = os.path.getmtime(p)
        last_modified = datetime.datetime.fromtimestamp(mtime).strftime('%Y-%m-%d %H:%M')
        break
st.caption(f"Last updated: {last_modified} · {len(df)} stocks analysed")

# ── Session State ──
if 'selected_ticker' not in st.session_state:
    st.session_state.selected_ticker = 'AAPL'
if 'navigate_to_deep_dive' not in st.session_state:
    st.session_state.navigate_to_deep_dive = False
if 'scatter_selected' not in st.session_state:
    st.session_state.scatter_selected = None

# 2) Deep dive from Rankings: show full page WITH tabs still visible
if st.session_state.navigate_to_deep_dive:
    render_deep_dive(st.session_state.selected_ticker, show_back_button=True)
    st.markdown("---")

# Tabs always visible
tab1, tab2, tab3, tab4, tab5 = st.tabs(["🏆 Rankings", "🎯 Deep Dive", "📈 Scatter Plot", "🔥 Conviction", "📊 Sector Heatmap"])

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

    for i, (ticker, row) in enumerate(ranking.iterrows(), 1):
        cs, ws, cb = row['combs_score'], row['weschler_score'], row['combined_score']
        c_col = _score_color_str(cs, 65, 45)
        w_col = _score_color_str(ws, 60, 40)
        cb_col = _score_color_str(cb, 60, 50)
        roic = fmt_pct(row.get('roic'))
        fy = fmt_pct(row.get('fcf_yield'))
        dd = fmt_pct(row.get('drawdown_52w'))
        pe = f"{row['trailing_pe']:.0f}" if not pd.isna(row['trailing_pe']) else "—"

        with st.container():
            col_btn, col_info = st.columns([1, 4])
            with col_btn:
                if st.button(f"#{i}\n**{ticker}**", key=f"rank_{ticker}", use_container_width=True):
                    st.session_state.selected_ticker = ticker
                    st.session_state.navigate_to_deep_dive = True
                    st.rerun()
            with col_info:
                st.markdown(f"**{str(row.get('company',''))[:35]}** · {str(row.get('sector',''))[:20]}")
                st.markdown(
                    f"<span style='color:{c_col};font-weight:700;margin-right:12px;'>C: {cs:.0f}</span>"
                    f"<span style='color:{w_col};font-weight:700;margin-right:12px;'>W: {ws:.0f}</span>"
                    f"<span style='color:{cb_col};font-weight:800;'>Comb: {cb:.1f}</span>"
                    f"&nbsp;&nbsp;<span style='color:#666;font-size:0.85em;'>PE:{pe} · ROIC:{roic} · FCF:{fy} · Draw:{dd}</span>",
                    unsafe_allow_html=True
                )

# ══════════════════════════════════════════════
# TAB 2: Deep Dive
# ══════════════════════════════════════════════
with tab2:
    ticker_options = sorted(df.index.tolist())
    default_ticker = st.session_state.get('selected_ticker', 'AAPL')
    default_idx = ticker_options.index(default_ticker) if default_ticker in ticker_options else 0
    selected = st.selectbox("Select ticker:", ticker_options, index=default_idx, key="deep_dive_ticker")
    st.session_state.selected_ticker = selected
    render_deep_dive(selected)

# ══════════════════════════════════════════════
# TAB 3: Scatter Plot (mobile-friendly touch)
# ══════════════════════════════════════════════
with tab3:
    st.markdown("### Combs vs Weschler — Quadrant Analysis")
    st.markdown("*Tap a dot for info. Tap again to deep dive. Pinch to zoom, drag to pan.*")

    plot_df = df.dropna(subset=['combs_score','weschler_score','market_cap']).copy()
    plot_df['log_mcap'] = np.log10(plot_df['market_cap'].clip(lower=1e8))
    plot_df['size'] = ((plot_df['log_mcap'] - plot_df['log_mcap'].min()) / (plot_df['log_mcap'].max() - plot_df['log_mcap'].min())) * 30 + 3
    plot_df['ticker'] = plot_df.index
    plot_df['hover_text'] = plot_df.apply(
        lambda x: f"<b>{x.name}</b><br>{x.get('company','')}<br>C:{x['combs_score']:.0f} W:{x['weschler_score']:.0f} Comb:{x['combined_score']:.0f}<br>ROIC:{fmt_pct(x.get('roic'))} FCF:{fmt_pct(x.get('fcf_yield'))}", axis=1)

    fig = px.scatter(
        plot_df, x='combs_score', y='weschler_score', color='sector',
        size='size', custom_data=['ticker'],
        hover_name='ticker', size_max=25, opacity=0.7,
        labels={'combs_score': 'Combs Score', 'weschler_score': 'Weschler Score'},
    )

    # Quadrant lines and labels
    med_c = plot_df['combs_score'].median()
    med_w = plot_df['weschler_score'].median()
    fig.add_vline(x=med_c, line_dash="dash", line_color="grey", opacity=0.5)
    fig.add_hline(y=med_w, line_dash="dash", line_color="grey", opacity=0.5)
    fig.add_annotation(x=plot_df['combs_score'].max()-2, y=plot_df['weschler_score'].max()-1, text="BOTH AGREE", showarrow=False, font=dict(color="darkgreen", size=11))
    fig.add_annotation(x=plot_df['combs_score'].min()+2, y=plot_df['weschler_score'].max()-1, text="WESCHLER<br>FAVS", showarrow=False, font=dict(color="darkblue", size=11))
    fig.add_annotation(x=plot_df['combs_score'].max()-2, y=plot_df['weschler_score'].min()+1, text="COMBS<br>FAVS", showarrow=False, font=dict(color="darkorange", size=11))
    fig.add_annotation(x=plot_df['combs_score'].min()+2, y=plot_df['weschler_score'].min()+1, text="NEITHER", showarrow=False, font=dict(color="darkred", size=11))

    for t, row in plot_df.nlargest(10, 'combined_score').iterrows():
        fig.add_annotation(x=row['combs_score'], y=row['weschler_score'], text=t, showarrow=True, arrowhead=0, ax=15, ay=-15, font=dict(size=10, color="black"))

    # 3) Render as raw HTML for native mobile touch (pinch-zoom, pan)
    import plotly.io as pio
    chart_html = pio.to_html(
        fig,
        full_html=False,
        include_plotlyjs='cdn',
        config={
            "scrollZoom": True,
            "displayModeBar": True,
            "modeBarButtonsToRemove": ["select2d", "lasso2d"],
            "displaylogo": False,
        }
    )
    # Wrap in responsive container with touch-action CSS
    full_html = f"""
    <div style="width:100%; overflow:hidden; touch-action:none;">
        {chart_html}
    </div>
    """
    import streamlit.components.v1 as components
    components.html(full_html, height=720, scrolling=False)

    # Manual ticker selection for deep dive (works on mobile)
    st.markdown("---")
    scatter_ticker = st.selectbox(
        "Select a stock from the chart to deep dive:",
        ["— Select —"] + sorted(plot_df.index.tolist()),
        key="scatter_select"
    )
    if scatter_ticker != "— Select —" and scatter_ticker in df.index:
        r = df.loc[scatter_ticker]
        cs, ws, cb = r['combs_score'], r['weschler_score'], r['combined_score']

        st.markdown(f"### {scatter_ticker} — {r.get('company','')}")
        c1, c2, c3 = st.columns(3)
        c1.metric("Combs", f"{cs:.1f}")
        c2.metric("Weschler", f"{ws:.1f}")
        c3.metric("Combined", f"{cb:.1f}")
        st.markdown(f"ROIC: {fmt_pct(r.get('roic'))} · FCF: {fmt_pct(r.get('fcf_yield'))} · Draw: {fmt_pct(r.get('drawdown_52w'))}")

        if st.button(f"🎯 Deep Dive into {scatter_ticker}", key=f"scatter_dd_{scatter_ticker}"):
            st.session_state.selected_ticker = scatter_ticker
            st.session_state.navigate_to_deep_dive = True
            st.rerun()

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
                if st.button(f"🎯 Deep Dive into {t}", key=f"conv_dd_{t}"):
                    st.session_state.selected_ticker = t
                    st.session_state.navigate_to_deep_dive = True
                    st.rerun()
    else:
        st.warning("No stocks currently meet both thresholds (Combs ≥60 AND Weschler ≥60)")

# ══════════════════════════════════════════════
# TAB 5: Sector Heatmap (mobile-friendly touch)
# ══════════════════════════════════════════════
with tab5:
    st.markdown("### Sector Score Heatmap")
    st.markdown("*Pinch to zoom, drag to pan. Select a sector below for macro analysis.*")

    sector_agg = df.groupby('sector').agg({
        'combs_score': 'mean', 'weschler_score': 'mean', 'combined_score': 'mean',
        'combs_unit_economics': 'mean', 'combs_frictionless': 'mean',
        'combs_capital_allocation': 'mean', 'combs_moat': 'mean',
        'weschler_variant': 'mean', 'weschler_complexity': 'mean',
        'weschler_distressed': 'mean', 'weschler_quality': 'mean',
        'weschler_compounding': 'mean',
    }).round(1).sort_values('combined_score', ascending=False)

    # Shorten sector names for mobile
    short_names = {
        'Information Technology': 'Info Tech',
        'Consumer Discretionary': 'Cons Disc',
        'Communication Services': 'Comm Svcs',
        'Consumer Staples': 'Cons Stap',
        'Real Estate': 'Real Est',
        'Health Care': 'Health',
        'Financials': 'Finance',
        'Industrials': 'Indust',
        'Materials': 'Mater',
        'Utilities': 'Util',
        'Energy': 'Energy',
    }
    sector_labels = [short_names.get(s, s) for s in sector_agg.index]

    fig_heat = go.Figure(data=go.Heatmap(
        z=sector_agg[['combs_score','weschler_score','combined_score']].values,
        x=['Combs', 'Weschler', 'Combined'],
        y=sector_labels,
        text=sector_agg[['combs_score','weschler_score','combined_score']].values.round(1),
        texttemplate="%{text}",
        textfont=dict(size=12),
        colorscale='RdYlGn', zmin=35, zmax=65,
    ))
    fig_heat.update_layout(
        height=450,
        title="Average Scores by Sector",
        margin=dict(l=80, r=10, t=40, b=10),
        xaxis=dict(side='top'),
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    sub_cols = ['combs_unit_economics','combs_frictionless','combs_capital_allocation','combs_moat',
                'weschler_variant','weschler_complexity','weschler_distressed','weschler_quality','weschler_compounding']
    sub_labels = ['UE','Fric','Cap','Moat','Var','Comp','Dist','Qual','Cmpd']

    fig_sub = go.Figure(data=go.Heatmap(
        z=sector_agg[sub_cols].values,
        x=sub_labels,
        y=sector_labels,
        text=sector_agg[sub_cols].values.round(1),
        texttemplate="%{text}",
        textfont=dict(size=11),
        colorscale='RdYlGn',
    ))
    fig_sub.update_layout(
        height=450,
        title="Sub-Score Breakdown",
        margin=dict(l=80, r=10, t=40, b=10),
        xaxis=dict(side='top'),
    )
    st.plotly_chart(fig_sub, use_container_width=True)

    # 4) Sector macro analysis
    st.markdown("---")
    st.markdown("### 🌍 Sector Macro Analysis")

    selected_sector = st.selectbox("Select sector for macro analysis:", sorted(df['sector'].dropna().unique()), key="sector_macro")

    if selected_sector:
        sector_stocks = df[df['sector'] == selected_sector].sort_values('combined_score', ascending=False)
        avg_draw = sector_stocks['drawdown_52w'].mean()
        avg_pe = sector_stocks['trailing_pe'].mean()
        avg_combs = sector_stocks['combs_score'].mean()
        avg_weschler = sector_stocks['weschler_score'].mean()

        c1, c2, c3, c4 = st.columns(4)
        c1.metric("Stocks", len(sector_stocks))
        c2.metric("Avg Drawdown", fmt_pct(avg_draw))
        c3.metric("Avg PE", f"{avg_pe:.1f}" if not pd.isna(avg_pe) else "—")
        c4.metric("Avg Combined", f"{(avg_combs+avg_weschler)/2:.1f}")

        # Macro sentiment analysis based on quantitative signals
        st.markdown("#### 📊 Quantitative Macro Signals")

        signals = []
        if avg_draw < -0.25:
            signals.append(("🔴 **Significant sector drawdown**", f"Average 52-week drawdown of {avg_draw*100:.0f}% suggests broad selling pressure. Could indicate macro headwinds or sector rotation.", "Short-term"))
        elif avg_draw < -0.15:
            signals.append(("🟡 **Moderate sector weakness**", f"Average 52-week drawdown of {avg_draw*100:.0f}%. Some stocks may be oversold.", "Short-term"))
        else:
            signals.append(("🟢 **Sector holding up**", f"Average 52-week drawdown of {avg_draw*100:.0f}%. No broad distress signal.", "Short-term"))

        high_short = sector_stocks[sector_stocks['short_percent'] > 0.05] if 'short_percent' in sector_stocks.columns else pd.DataFrame()
        if len(high_short) > 3:
            signals.append(("🔴 **Elevated short interest**", f"{len(high_short)} stocks with >5% short interest — bears are active in this sector.", "Short-term"))

        avg_rev_cagr = sector_stocks['revenue_cagr_3y'].mean()
        if not pd.isna(avg_rev_cagr):
            if avg_rev_cagr > 0.10:
                signals.append(("🟢 **Strong revenue growth**", f"Average 3-year revenue CAGR of {avg_rev_cagr*100:.1f}%. Structural tailwinds.", "Medium-term"))
            elif avg_rev_cagr < 0:
                signals.append(("🔴 **Revenue decline**", f"Average 3-year revenue CAGR of {avg_rev_cagr*100:.1f}%. Secular headwinds or cyclical downturn.", "Medium-term"))

        avg_roic = sector_stocks['roic'].mean()
        if not pd.isna(avg_roic):
            if avg_roic > 0.20:
                signals.append(("🟢 **High returns on capital**", f"Average ROIC of {avg_roic*100:.0f}% — businesses generate strong returns.", "Long-term"))
            elif avg_roic < 0.08:
                signals.append(("🔴 **Low returns on capital**", f"Average ROIC of {avg_roic*100:.0f}% — capital-intensive or competitive sector.", "Long-term"))

        avg_margin_stability = sector_stocks['margin_stability'].mean() if 'margin_stability' in sector_stocks.columns else np.nan
        if not pd.isna(avg_margin_stability):
            if avg_margin_stability < 0.03:
                signals.append(("🟢 **Stable margins**", "Low margin volatility — predictable earnings power.", "Long-term"))
            elif avg_margin_stability > 0.08:
                signals.append(("🟡 **Volatile margins**", "High margin volatility — earnings less predictable.", "Long-term"))

        grey_zone = sector_stocks[(sector_stocks['altman_z'] >= 1.0) & (sector_stocks['altman_z'] <= 3.0)] if 'altman_z' in sector_stocks.columns else pd.DataFrame()
        if len(grey_zone) > len(sector_stocks) * 0.3:
            signals.append(("🟡 **Financial stress signals**", f"{len(grey_zone)} stocks ({len(grey_zone)/len(sector_stocks)*100:.0f}%) in Altman Z grey zone.", "Medium-term"))

        for emoji_label, desc, horizon in signals:
            st.markdown(f"**[{horizon}]** {emoji_label}")
            st.caption(desc)

        # ── News: Yahoo Finance headlines for sector's top movers ──
        st.markdown("#### 📰 Recent News (Top Movers in Sector)")
        st.caption("Headlines from Yahoo Finance for the sector's most notable stocks")

        import yfinance as yf

        # Keyword-based sentiment classifier (no external API needed)
        BULLISH_WORDS = {'upgrade','beat','beats','exceeds','raises','surge','surges','soars','rally','rallies',
                         'bullish','outperform','buy','strong','growth','record','profit','gains','boost',
                         'positive','optimistic','upside','momentum','breakout','highs','recovery','rebound',
                         'accelerat','expand','dividend','overweight','top-pick','above','jumps','improved'}
        BEARISH_WORDS = {'downgrade','miss','misses','cut','cuts','decline','declines','drop','drops','fall',
                         'falls','bearish','underperform','sell','weak','loss','losses','warning','risk',
                         'negative','pessimistic','downside','slowdown','crash','lows','recession','layoff',
                         'underweight','below','slump','plunge','concern','fears','lawsuit','fraud','probe',
                         'investigation','debt','default','bankruptcy','restructur','tariff','headwind'}

        def classify_sentiment(title, summary=''):
            """Classify headline sentiment as bullish/bearish/neutral using keywords."""
            text = (title + ' ' + summary).lower()
            bull_count = sum(1 for w in BULLISH_WORDS if w in text)
            bear_count = sum(1 for w in BEARISH_WORDS if w in text)
            if bull_count > bear_count:
                return '🟢 Bullish', bull_count - bear_count
            elif bear_count > bull_count:
                return '🔴 Bearish', bear_count - bull_count
            else:
                return '⚪ Neutral', 0

        @st.cache_data(ttl=3600, show_spinner="Fetching news...")
        def fetch_sector_news(tickers, max_per_ticker=3):
            """Fetch recent news from Yahoo Finance with sentiment classification."""
            all_news = []
            for t in tickers:
                try:
                    ticker_obj = yf.Ticker(t)
                    news = ticker_obj.news or []
                    for article in news[:max_per_ticker]:
                        content = article.get('content', {})
                        if not content:
                            continue
                        title = content.get('title', '')
                        link = content.get('canonicalUrl', {}).get('url', '') or content.get('clickThroughUrl', {}).get('url', '')
                        pub_date = content.get('pubDate', '')
                        provider = content.get('provider', {}).get('displayName', '')
                        summary = content.get('summary', '')
                        if title:
                            sentiment, strength = classify_sentiment(title, summary)
                            all_news.append({
                                'ticker': t,
                                'title': title,
                                'link': link,
                                'date': pub_date[:10] if pub_date else '',
                                'source': provider,
                                'summary': summary[:200] if summary else '',
                                'sentiment': sentiment,
                                'strength': strength,
                            })
                except Exception:
                    pass
            return all_news

        # Fetch news for top 5 and bottom 5 stocks in sector (biggest movers)
        top_tickers = sector_stocks.head(3).index.tolist()
        bottom_tickers = sector_stocks.tail(2).index.tolist()
        most_distressed = sector_stocks.nsmallest(2, 'drawdown_52w').index.tolist() if 'drawdown_52w' in sector_stocks.columns else []
        news_tickers = list(dict.fromkeys(top_tickers + most_distressed + bottom_tickers))[:6]

        news_items = fetch_sector_news(news_tickers)

        if news_items:
            # Sentiment summary
            bull_count = sum(1 for n in news_items if 'Bullish' in n['sentiment'])
            bear_count = sum(1 for n in news_items if 'Bearish' in n['sentiment'])
            neutral_count = sum(1 for n in news_items if 'Neutral' in n['sentiment'])

            sc1, sc2, sc3 = st.columns(3)
            sc1.metric("🟢 Bullish", bull_count)
            sc2.metric("🔴 Bearish", bear_count)
            sc3.metric("⚪ Neutral", neutral_count)

            # Overall sentiment
            if bull_count > bear_count * 1.5:
                st.success(f"**Overall sentiment: Bullish** — {bull_count} positive vs {bear_count} negative headlines")
            elif bear_count > bull_count * 1.5:
                st.error(f"**Overall sentiment: Bearish** — {bear_count} negative vs {bull_count} positive headlines")
            else:
                st.info(f"**Overall sentiment: Mixed** — {bull_count} positive, {bear_count} negative, {neutral_count} neutral")

            # Filter controls
            sent_filter = st.radio("Filter:", ["All", "🟢 Bullish", "🔴 Bearish", "⚪ Neutral"], horizontal=True, key="news_filter")

            filtered_news = news_items if sent_filter == "All" else [n for n in news_items if sent_filter in n['sentiment']]

            for item in filtered_news[:15]:
                sent_badge = item['sentiment']
                st.markdown(f"{sent_badge} **{item['ticker']}** · {item['date']} · _{item['source']}_")
                st.markdown(f"[{item['title']}]({item['link']})" if item['link'] else item['title'])
                if item['summary']:
                    st.caption(item['summary'])
                st.markdown("")

            # Sector-level alert thresholds
            if len(news_items) >= 3:
                bear_pct = bear_count / len(news_items) * 100
                bull_pct = bull_count / len(news_items) * 100

                st.markdown("#### ⚠️ Sector Alert Thresholds")
                if bear_pct >= 70:
                    st.error(f"🚨 **CRITICAL: {bear_pct:.0f}% bearish headlines** — Extreme negative sentiment. Potential sector-wide sell-off or major macro event. Review positions immediately.")
                elif bear_pct >= 50:
                    st.warning(f"⚠️ **WARNING: {bear_pct:.0f}% bearish headlines** — Majority negative sentiment. Monitor for contagion risk. May create buying opportunities for contrarian Weschler-style picks if fundamentals hold.")
                elif bull_pct >= 70:
                    st.success(f"🟢 **BULLISH: {bull_pct:.0f}% positive headlines** — Strong positive sentiment. Combs-style quality names likely leading. Watch for overvaluation risk.")
                elif bull_pct >= 50:
                    st.info(f"📈 **LEANING BULLISH: {bull_pct:.0f}% positive headlines** — Moderately positive sentiment. Sector fundamentals likely intact.")
                else:
                    st.info(f"📊 **MIXED SENTIMENT: {bull_pct:.0f}% bullish / {bear_pct:.0f}% bearish** — No clear directional signal. Stock-specific analysis more important than sector-level view.")
        else:
            st.info("No recent news found for this sector's key stocks.")

        # Top/bottom movers in sector
        st.markdown("#### 🏆 Top 5 in Sector (Combined Score)")
        for i, (t, r) in enumerate(sector_stocks.head(5).iterrows(), 1):
            if st.button(f"#{i} {t} — {r.get('company','')[:25]} (C:{r['combs_score']:.0f} W:{r['weschler_score']:.0f})", key=f"sector_{t}"):
                st.session_state.selected_ticker = t
                st.session_state.navigate_to_deep_dive = True
                st.rerun()

# ── Footer ──
st.markdown("---")
st.markdown("*Combs-Weschler Screener · Data from Yahoo Finance via yfinance · This tool identifies candidates for research, not buy signals.*")
