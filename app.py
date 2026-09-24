"""
CDC Provisional Natality Explorer (2025)
All-in-one Streamlit Application
"""

from pathlib import Path
import streamlit as st
import pandas as pd
import plotly.express as px

# ---------------------------------------------------------
# Page Configuration
# ---------------------------------------------------------
st.set_page_config(
    page_title="CDC Provisional Natality Dashboard",
    page_icon="👶",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ---------------------------------------------------------
# Constants & Mappings
# ---------------------------------------------------------
MONTH_ORDER = [
    "January", "February", "March", "April", "May", "June",
    "July", "August", "September", "October", "November", "December"
]

USPS_STATE_MAP = {
    "Alabama": "AL", "Alaska": "AK", "Arizona": "AZ", "Arkansas": "AR",
    "California": "CA", "Colorado": "CO", "Connecticut": "CT", "Delaware": "DE",
    "District of Columbia": "DC", "Florida": "FL", "Georgia": "GA", "Hawaii": "HI",
    "Idaho": "ID", "Illinois": "IL", "Indiana": "IN", "Iowa": "IA",
    "Kansas": "KS", "Kentucky": "KY", "Louisiana": "LA", "Maine": "ME",
    "Maryland": "MD", "Massachusetts": "MA", "Michigan": "MI", "Minnesota": "MN",
    "Mississippi": "MS", "Missouri": "MO", "Montana": "MT", "Nebraska": "NE",
    "Nevada": "NV", "New Hampshire": "NH", "New Jersey": "NJ", "New Mexico": "NM",
    "New York": "NY", "North Carolina": "NC", "North Dakota": "ND", "Ohio": "OH",
    "Oklahoma": "OK", "Oregon": "OR", "Pennsylvania": "PA", "Rhode Island": "RI",
    "South Carolina": "SC", "South Dakota": "SD", "Tennessee": "TN", "Texas": "TX",
    "Utah": "UT", "Vermont": "VT", "Virginia": "VA", "Washington": "WA",
    "West Virginia": "WV", "Wisconsin": "WI", "Wyoming": "WY"
}

PALETTE = {
    "primary": "#1D4ED8",
    "female": "#D95F02",
    "male": "#1F78B4",
    "sequential": "Blues",
    "heatmap": "YlGnBu",
    "neutral": "#64748B"
}

REQUIRED_COLUMNS = {
    "state_of_residence",
    "month",
    "month_code",
    "year_code",
    "sex_of_infant",
    "births"
}


# ---------------------------------------------------------
# Data Loader with Caching & Validation
# ---------------------------------------------------------
@st.cache_data(show_spinner="Loading CDC Natality dataset...")
def load_and_validate_data(file_path: str = "Provisional_Natality_2025_CDC1.csv") -> pd.DataFrame:
    """Loads, validates, and prepares the CDC provisional birth records dataset."""
    path = Path(file_path)
    if not path.exists():
        alt_path = Path("data") / file_path
        if alt_path.exists():
            path = alt_path
        else:
            raise FileNotFoundError(
                f"Dataset could not be located at '{file_path}' or '{alt_path}'."
            )

    df = pd.read_csv(path)

    # Schema validation
    missing_cols = REQUIRED_COLUMNS - set(df.columns)
    if missing_cols:
        raise ValueError(f"Dataset is missing required columns: {missing_cols}")

    # Type casting and data hygiene
    df["births"] = pd.to_numeric(df["births"], errors="coerce").fillna(0).astype(int)
    df["month_code"] = pd.to_numeric(df["month_code"], errors="coerce").astype(int)
    df["state_of_residence"] = df["state_of_residence"].astype(str).str.strip()
    df["sex_of_infant"] = df["sex_of_infant"].astype(str).str.strip()

    # Enforce chronological categorical order for months
    df["month"] = pd.Categorical(df["month"], categories=MONTH_ORDER, ordered=True)

    # Map state abbreviations for choropleth rendering
    df["state_abbr"] = df["state_of_residence"].map(USPS_STATE_MAP)

    return df


# ---------------------------------------------------------
# UI Component: Header
# ---------------------------------------------------------
def render_header() -> None:
    """Renders dashboard title, badges, and analytical disclaimers."""
    st.title("CDC Provisional Natality Explorer (2025)")
    st.markdown(
        "Explore geographic patterns, monthly variations, and sex distribution in US births."
    )

    col1, col2, col3 = st.columns(3)
    with col1:
        st.info("📌 **Data Nature**: Provisional Natality Figures (CDC WONDER)", icon="ℹ️")
    with col2:
        st.warning("⚠️ **Metric Alert**: Absolute Birth Counts, **not** Birth Rates", icon="⚠️")
    with col3:
        st.success("🏛️ **Audience**: Undergraduate Business Analytics", icon="🎓")

    st.markdown("---")


# ---------------------------------------------------------
# UI Component: Sidebar Filters
# ---------------------------------------------------------
def render_sidebar(df: pd.DataFrame) -> pd.DataFrame:
    """Renders filtering controls with Select All options and returns filtered DataFrame."""
    st.sidebar.header("Filter Controls")

    all_states = sorted(df["state_of_residence"].dropna().unique().tolist())
    all_months = [m for m in MONTH_ORDER if m in df["month"].dropna().unique()]
    all_sexes = sorted(df["sex_of_infant"].dropna().unique().tolist())

    # Initialize session state for filters if absent
    if "selected_states" not in st.session_state:
        st.session_state.selected_states = all_states
    if "selected_months" not in st.session_state:
        st.session_state.selected_months = all_months
    if "selected_sexes" not in st.session_state:
        st.session_state.selected_sexes = all_sexes

    # Reset Filters Button
    if st.sidebar.button("🔄 Reset All Filters", use_container_width=True):
        st.session_state.selected_states = all_states
        st.session_state.selected_months = all_months
        st.session_state.selected_sexes = all_sexes
        st.rerun()

    st.sidebar.markdown("---")

    # State Multi-Select & Select All
    select_all_states = st.sidebar.checkbox("Select All Geographies", value=True, key="chk_all_states")
    if select_all_states:
        selected_states = all_states
        st.sidebar.multiselect("Geography", all_states, default=all_states, disabled=True, key="states_disabled")
    else:
        selected_states = st.sidebar.multiselect(
            "Geography",
            all_states,
            default=st.session_state.selected_states if set(st.session_state.selected_states) != set(all_states) else all_states[:5],
            key="states_active"
        )
    st.session_state.selected_states = selected_states

    # Month Multi-Select & Select All
    select_all_months = st.sidebar.checkbox("Select All Months", value=True, key="chk_all_months")
    if select_all_months:
        selected_months = all_months
        st.sidebar.multiselect("Month", all_months, default=all_months, disabled=True, key="months_disabled")
    else:
        selected_months = st.sidebar.multiselect(
            "Month",
            all_months,
            default=st.session_state.selected_months,
            key="months_active"
        )
    st.session_state.selected_months = selected_months

    # Infant Sex Multi-Select
    selected_sexes = st.sidebar.multiselect(
        "Infant Sex",
        all_sexes,
        default=st.session_state.selected_sexes,
        key="sexes_active"
    )
    st.session_state.selected_sexes = selected_sexes

    # Filter evaluation
    filtered_df = df[
        (df["state_of_residence"].isin(selected_states)) &
        (df["month"].isin(selected_months)) &
        (df["sex_of_infant"].isin(selected_sexes))
    ]

    # Active filter readout
    st.sidebar.markdown("---")
    st.sidebar.subheader("Active Scope Summary")
    st.sidebar.markdown(f"- **Geographies**: {len(selected_states)} of {len(all_states)}")
    st.sidebar.markdown(f"- **Months**: {len(selected_months)} of {len(all_months)}")
    st.sidebar.markdown(f"- **Sex**: {', '.join(selected_sexes) if selected_sexes else 'None'}")
    st.sidebar.markdown(f"- **Observed Records**: {len(filtered_df):,}")

    return filtered_df


# ---------------------------------------------------------
# UI Component: KPI Cards
# ---------------------------------------------------------
def render_kpis(filtered_df: pd.DataFrame) -> None:
    """Renders top summary cards with thousand separators and empty-state handling."""
    col1, col2, col3, col4, col5 = st.columns(5)

    if filtered_df.empty:
        col1.metric("Total Births", "0")
        col2.metric("Geographies", "0")
        col3.metric("Avg / Month", "0")
        col4.metric("Top Geography", "N/A")
        col5.metric("Peak Month", "N/A")
        return

    total_births = int(filtered_df["births"].sum())
    num_geos = filtered_df["state_of_residence"].nunique()
    num_months = filtered_df["month"].nunique()
    avg_per_month = total_births / num_months if num_months > 0 else 0

    # Highest Geography
    geo_totals = filtered_df.groupby("state_of_residence")["births"].sum()
    top_geo = geo_totals.idxmax()
    top_geo_val = geo_totals.max()

    # Highest Month
    month_totals = filtered_df.groupby("month", observed=True)["births"].sum()
    top_month = month_totals.idxmax()
    top_month_val = month_totals.max()

    col1.metric("Total Births", f"{total_births:,}")
    col2.metric("Selected Geographies", f"{num_geos}")
    col3.metric("Avg Births / Month", f"{int(avg_per_month):,}")
    col4.metric("Top Geography", f"{top_geo}", f"{top_geo_val:,} births")
    col5.metric("Peak Month", f"{top_month}", f"{top_month_val:,} births")

    st.markdown("---")


# ---------------------------------------------------------
# Tab 1: Overview
# ---------------------------------------------------------
def render_overview_tab(df: pd.DataFrame) -> None:
    """Displays monthly volume trends and female vs. male distribution."""
    if df.empty:
        st.warning("No data matching current filters. Please adjust sidebar criteria.")
        return

    col1, col2 = st.columns([3, 2])

    with col1:
        st.subheader("Monthly Birth Trend")
        monthly_trend = (
            df.groupby("month", observed=True)["births"]
            .sum()
            .reindex(MONTH_ORDER)
            .dropna()
            .reset_index()
        )
        fig_trend = px.line(
            monthly_trend,
            x="month",
            y="births",
            markers=True,
            title="Total Births Across Selected Months",
            labels={"month": "Month", "births": "Recorded Births"},
        )
        fig_trend.update_traces(line_color=PALETTE["primary"], line_width=3, marker=dict(size=8))
        fig_trend.update_layout(
            yaxis_range=[0, monthly_trend["births"].max() * 1.15 if not monthly_trend.empty else 100],
            template="plotly_white",
            margin=dict(l=40, r=20, t=50, b=40)
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with col2:
        st.subheader("Infant Sex Distribution")
        sex_totals = df.groupby("sex_of_infant")["births"].sum().reset_index()
        fig_sex = px.pie(
            sex_totals,
            names="sex_of_infant",
            values="births",
            hole=0.45,
            title="Proportion of Births by Sex",
            color="sex_of_infant",
            color_discrete_map={"Female": PALETTE["female"], "Male": PALETTE["male"]}
        )
        fig_sex.update_traces(textposition="inside", textinfo="percent+label")
        fig_sex.update_layout(template="plotly_white", margin=dict(l=20, r=20, t=50, b=40))
        st.plotly_chart(fig_sex, use_container_width=True)


# ---------------------------------------------------------
# Tab 2: Geographic Analysis
# ---------------------------------------------------------
def render_geographic_tab(df: pd.DataFrame) -> None:
    """Renders state choropleth, ranked volume bars, and top vs. bottom comparisons."""
    if df.empty:
        st.warning("No data matching current filters. Please adjust sidebar criteria.")
        return

    st.subheader("National Birth Count Distribution")

    geo_agg = (
        df.groupby(["state_of_residence", "state_abbr"], as_index=False)["births"]
        .sum()
        .sort_values(by="births", ascending=False)
    )

    fig_map = px.choropleth(
        geo_agg,
        locations="state_abbr",
        locationmode="USA-states",
        color="births",
        scope="usa",
        color_continuous_scale=PALETTE["sequential"],
        hover_name="state_of_residence",
        labels={"births": "Birth Count"},
        title="Provisional Birth Counts by State"
    )
    fig_map.update_layout(template="plotly_white", margin=dict(l=10, r=10, t=40, b=10))
    st.plotly_chart(fig_map, use_container_width=True)

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("State Ranking (All Selected)")
        fig_bar = px.bar(
            geo_agg.sort_values(by="births", ascending=True),
            x="births",
            y="state_of_residence",
            orientation="h",
            title="Total Births by State",
            labels={"births": "Births", "state_of_residence": "State"},
            color_discrete_sequence=[PALETTE["primary"]]
        )
        fig_bar.update_layout(
            template="plotly_white",
            height=max(450, len(geo_agg) * 16),
            xaxis_range=[0, geo_agg["births"].max() * 1.05 if not geo_agg.empty else 100],
            margin=dict(l=40, r=20, t=40, b=40)
        )
        st.plotly_chart(fig_bar, use_container_width=True)

    with col2:
        st.subheader("Top vs. Bottom Geographies")
        k = st.slider("Select Top / Bottom Count (N)", min_value=3, max_value=15, value=5)
        top_k = geo_agg.head(k).copy()
        top_k["Group"] = f"Top {k}"
        bottom_k = geo_agg.tail(k).copy()
        bottom_k["Group"] = f"Bottom {k}"
        comp_df = pd.concat([top_k, bottom_k])

        fig_comp = px.bar(
            comp_df,
            x="births",
            y="state_of_residence",
            color="Group",
            orientation="h",
            title=f"Comparison: Top {k} vs Bottom {k} Geographies",
            labels={"births": "Births", "state_of_residence": "State"},
            color_discrete_map={f"Top {k}": PALETTE["primary"], f"Bottom {k}": PALETTE["neutral"]}
        )
        fig_comp.update_layout(
            template="plotly_white",
            height=450,
            xaxis_range=[0, comp_df["births"].max() * 1.05 if not comp_df.empty else 100],
            margin=dict(l=40, r=20, t=40, b=40)
        )
        st.plotly_chart(fig_comp, use_container_width=True)


# ---------------------------------------------------------
# Tab 3: Monthly & Sex Analysis
# ---------------------------------------------------------
def render_monthly_sex_tab(df: pd.DataFrame) -> None:
    """Renders seasonal heatmaps and sex breakdown across calendar months."""
    if df.empty:
        st.warning("No data matching current filters. Please adjust sidebar criteria.")
        return

    st.subheader("State-by-Month Birth Count Heatmap")
    matrix_df = df.pivot_table(
        index="state_of_residence",
        columns="month",
        values="births",
        aggfunc="sum",
        observed=True
    ).reindex(columns=[m for m in MONTH_ORDER if m in df["month"].unique()]).fillna(0)

    fig_heat = px.imshow(
        matrix_df,
        labels=dict(x="Month", y="State", color="Births"),
        x=matrix_df.columns,
        y=matrix_df.index,
        color_continuous_scale=PALETTE["heatmap"],
        aspect="auto",
        title="Birth Density Across Geography and Calendar Month"
    )
    fig_heat.update_layout(
        template="plotly_white",
        height=max(500, len(matrix_df) * 14),
        margin=dict(l=40, r=20, t=50, b=40)
    )
    st.plotly_chart(fig_heat, use_container_width=True)

    st.markdown("---")
    st.subheader("Monthly Birth Volume by Infant Sex")
    sex_monthly = (
        df.groupby(["month", "sex_of_infant"], observed=True)["births"]
        .sum()
        .reset_index()
    )
    fig_grouped = px.bar(
        sex_monthly,
        x="month",
        y="births",
        color="sex_of_infant",
        barmode="group",
        title="Male vs. Female Birth Counts by Month",
        labels={"month": "Month", "births": "Birth Count", "sex_of_infant": "Infant Sex"},
        color_discrete_map={"Female": PALETTE["female"], "Male": PALETTE["male"]}
    )
    fig_grouped.update_layout(
        template="plotly_white",
        yaxis_range=[0, sex_monthly["births"].max() * 1.1 if not sex_monthly.empty else 100],
        margin=dict(l=40, r=20, t=50, b=40)
    )
    st.plotly_chart(fig_grouped, use_container_width=True)


# ---------------------------------------------------------
# Tab 4: Data Table & Download
# ---------------------------------------------------------
def render_data_table_tab(filtered_df: pd.DataFrame) -> None:
    """Renders formatted table and enables instant CSV download."""
    st.subheader("Filtered Natality Records")

    if filtered_df.empty:
        st.warning("No records found with the currently applied filters.")
        return

    csv_bytes = filtered_df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label="📥 Download Current Filtered Data (CSV)",
        data=csv_bytes,
        file_name="cdc_provisional_natality_filtered_2025.csv",
        mime="text/csv",
        use_container_width=False
    )

    st.caption(f"Displaying {len(filtered_df):,} rows matching active sidebar parameters.")

    st.dataframe(
        filtered_df[[
            "state_of_residence",
            "year_code",
            "month",
            "month_code",
            "sex_of_infant",
            "births"
        ]],
        use_container_width=True,
        column_config={
            "state_of_residence": "State / Geography",
            "year_code": "Year",
            "month": "Month",
            "month_code": "Month Number",
            "sex_of_infant": "Infant Sex",
            "births": st.column_config.NumberColumn("Birth Count", format="%d")
        },
        hide_index=True
    )


# ---------------------------------------------------------
# Tab 5: About the Data
# ---------------------------------------------------------
def render_about_tab() -> None:
    """Renders data source documentation and statistical guidance for business students."""
    st.subheader("Methodology & Analytical Guidance")

    st.markdown("""
    ### 1. Count vs. Rate: The Fundamental Distinction
    A common pitfall in geospatial and temporal analysis is treating **raw counts** as indicators of fertility or risk:
    * **Birth Counts**: Simply reflect the aggregate number of live births recorded in a given jurisdiction. Because populous states like California and Texas have millions more residents than Wyoming or Vermont, their birth counts will naturally dominate aggregate charts.
    * **Crude Birth Rates & General Fertility Rates**: Require demographic denominators (e.g., live births per 1,000 total population or per 1,000 women aged 15–44). Without dividing by baseline population sizes, raw birth volume **must not** be used to draw inferences about local birth rates or family planning trends.

    ### 2. Provisional Data Nature
    * These statistics are derived from the **CDC WONDER Provisional Natality System**.
    * **Provisional records** are based on registered birth records received by the National Center for Health Statistics (NCHS) as of data extraction dates.
    * Data may be subject to ongoing reporting delays, corrections, and delayed registrations across state vital statistics jurisdictions before finalization.

    ### 3. Dataset Attribution & Technical Specs
    * **Source Agency**: Centers for Disease Control and Prevention (CDC) / National Center for Health Statistics (NCHS).
    * **Data Year**: 2025 (Provisional Series).
    * **Coverage**: 50 US States and the District of Columbia.
    * **Granularity**: Aggregated monthly counts by maternal state of residence and infant sex.
    """)


# ---------------------------------------------------------
# Main Execution Orchestrator
# ---------------------------------------------------------
def main() -> None:
    # 1. Ingest cached dataset
    try:
        df = load_and_validate_data("Provisional_Natality_2025_CDC1.csv")
    except Exception as exc:
        st.error(f"Failed to load dataset: {exc}")
        st.stop()

    # 2. Header & Badges
    render_header()

    # 3. Sidebar Filtering
    filtered_df = render_sidebar(df)

    # 4. Top KPI Cards
    render_kpis(filtered_df)

    # 5. Dashboard Tabbed Navigation
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "📊 Overview",
        "🗺️ Geographic Analysis",
        "📅 Monthly & Sex Analysis",
        "📋 Data Table & Download",
        "ℹ️ About the Data"
    ])

    with tab1:
        render_overview_tab(filtered_df)
    with tab2:
        render_geographic_tab(filtered_df)
    with tab3:
        render_monthly_sex_tab(filtered_df)
    with tab4:
        render_data_table_tab(filtered_df)
    with tab5:
        render_about_tab()


if __name__ == "__main__":
    main()
