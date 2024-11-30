import streamlit as st
import pandas as pd
import pyodbc
import time
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from contextlib import contextmanager


@contextmanager
def get_connection():
    """Context manager for database connections"""
    conn = None
    try:
        conn_str = (
            'DRIVER={SQL Server};'
            'SERVER=a265m001;'
            'DATABASE=QADEE2798;'
            'Trusted_Connection=yes;'
        )
        print(f"Attempting to connect with connection string: {conn_str}")
        conn = pyodbc.connect(conn_str, timeout=30)
        print("Successfully connected to database")
        yield conn
    except Exception as e:
        print(f"Detailed database connection error: {str(e)}")
        st.error(f"Database connection error: {str(e)}")
        yield None
    finally:
        if conn:
            conn.close()
            print("Database connection closed")


def apply_filters(df, selected_design_groups, selected_cogs_type, selected_prod_lines, selected_chr02):
    """Apply filters to the dataframe based on user selections"""
    if df is None or df.empty:
        return pd.DataFrame()

    filtered_df = df.copy()

    # Convert None values to empty strings or appropriate default values
    filtered_df['pt_dsgn_grp'] = filtered_df['pt_dsgn_grp'].fillna('')
    filtered_df['pt_prod_line'] = filtered_df['pt_prod_line'].fillna('')
    filtered_df['pt__chr02'] = filtered_df['pt__chr02'].fillna('')

    if selected_design_groups:
        filtered_df = filtered_df[filtered_df['pt_dsgn_grp'].isin(
            selected_design_groups)]

    if selected_prod_lines:
        filtered_df = filtered_df[filtered_df['pt_prod_line'].isin(
            selected_prod_lines)]

    if selected_chr02:
        filtered_df = filtered_df[filtered_df['pt__chr02'].isin(
            selected_chr02)]

    return filtered_df


def create_inventory_charts(df, selected_cogs_type):
    """Create enhanced visualizations with COGS analysis"""
    if df is None or df.empty:
        return None, None

    try:
        # Use the selected COGS type for calculations
        cogs_column = selected_cogs_type

        # Design Group COGS Distribution Chart
        design_group_data = df.groupby('pt_dsgn_grp')[
            cogs_column].sum().reset_index()
        design_group_data = design_group_data.sort_values(
            cogs_column, ascending=True)

        fig_design_groups = px.pie(
            design_group_data,
            values=cogs_column,
            names='pt_dsgn_grp',
            title=f'Inventory Distribution by Design Group ({cogs_column})',
            hole=0.4,
            color_discrete_sequence=px.colors.qualitative.Set3
        )

        fig_design_groups.update_traces(
            textinfo='percent+value',
            hovertemplate=f'<b>%{{label}}</b><br>{
                cogs_column}: $%{{value:,.2f}}<br>Percentage: %{{percent:.1%}}<extra></extra>'
        )

        # Top Parts by COGS Chart
        top_parts = df.nlargest(10, cogs_column).copy()
        top_parts['hover_text'] = top_parts.apply(
            lambda x: f"Part: {x['pt_part']}<br>" +
            f"Description: {x['pt_desc1']}<br>" +
            f"{cogs_column}: ${x[cogs_column]:,.2f}",
            axis=1
        )

        fig_top_parts = px.bar(
            top_parts.sort_values(cogs_column, ascending=True),
            x=cogs_column,
            y='pt_part',
            orientation='h',
            title=f'Top 10 Parts by {cogs_column}',
            labels={cogs_column: f'{
                cogs_column} ($)', 'pt_part': 'Part Number'},
            text=cogs_column,
            custom_data=['hover_text']
        )

        fig_top_parts.update_traces(
            texttemplate='$%{text:,.2f}',
            hovertemplate='%{customdata[0]}<extra></extra>'
        )

        return fig_design_groups, fig_top_parts
    except Exception as e:
        st.error(f"Chart creation error: {str(e)}")
        return None, None


def display_dashboard(df):
    """Display the dashboard components with COGS metrics and filters"""
    if df is None or df.empty:
        st.error("No data available to display")
        return

    st.title("Inventory Dashboard-2798 FOAM")

    # Last updated timestamp
    st.sidebar.write(f"Last Updated: {
                     datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")

    # Add filters in sidebar
    st.sidebar.subheader("Filters")

    # COGS Type selector
    cogs_types = ['Total_COGS', 'COGS_WH', 'COGS_WIP', 'COGS_EXLPICK']
    selected_cogs_type = st.sidebar.selectbox("Select COGS Type", cogs_types)

    # Design Group filter - handle None values
    design_groups = sorted(
        [g for g in df['pt_dsgn_grp'].unique() if pd.notna(g)])
    selected_design_groups = st.sidebar.multiselect(
        "Filter by Design Group",
        options=design_groups
    )

    # Product Line filter - handle None values
    prod_lines = sorted(
        [p for p in df['pt_prod_line'].unique() if pd.notna(p)])
    selected_prod_lines = st.sidebar.multiselect(
        "Filter by Product Line",
        options=prod_lines
    )

    # CHR02 filter - handle None values
    chr02_values = sorted([c for c in df['pt__chr02'].unique() if pd.notna(c)])
    selected_chr02 = st.sidebar.multiselect(
        "Filter by CHR02",
        options=chr02_values
    )

    # Apply filters
    filtered_df = apply_filters(
        df, selected_design_groups, selected_cogs_type, selected_prod_lines, selected_chr02)

    if filtered_df.empty:
        st.warning("No data available after applying filters")
        return

    # Display metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Parts", len(filtered_df['pt_part'].unique()))
    with col2:
        st.metric(selected_cogs_type, f"${
                  filtered_df[selected_cogs_type].sum():,.2f}")
    with col3:
        st.metric("Avg Cost per Part", f"${
                  filtered_df[selected_cogs_type].mean():,.2f}")
    with col4:
        st.metric("Total Quantity", f"{
                  filtered_df['total_qty_avail'].sum():,.0f}")

    # Create and display charts
    fig_design_groups, fig_top_parts = create_inventory_charts(
        filtered_df, selected_cogs_type)
    if fig_design_groups and fig_top_parts:
        col1, col2 = st.columns(2)
        with col1:
            st.plotly_chart(fig_design_groups, use_container_width=True)
        with col2:
            st.plotly_chart(fig_top_parts, use_container_width=True)

    # Display and download detailed table
    st.subheader("Detailed Inventory Table")

    # Format the display table
    display_df = filtered_df.copy()
    numeric_cols = ['Total_COGS', 'COGS_WH', 'COGS_WIP', 'COGS_EXLPICK']
    for col in numeric_cols:
        display_df[col] = display_df[col].map('${:,.2f}'.format)

    st.dataframe(display_df)

    # Download button
    csv = filtered_df.to_csv(index=False).encode('utf-8')
    st.download_button(
        label="Download Full Report",
        data=csv,
        file_name=f"inventory_report_2798{
            datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        mime="text/csv"
    )


@st.cache_data(ttl=3600)
def load_inventory_data():
    """Load inventory data with progress bar and error handling"""
    try:
        with st.spinner('Loading inventory data...'):
            progress_bar = st.progress(0)

            with get_connection() as conn:
                if conn is None:
                    st.error("Failed to establish database connection")
                    return pd.DataFrame()

                # Execute query with chunking for large datasets
                query = get_inventory_data()
                chunks = []
                for i, chunk in enumerate(pd.read_sql(query, conn, chunksize=1000)):
                    chunks.append(chunk)
                    progress_bar.progress(min(1.0, (i + 1) / 10))

                if not chunks:
                    st.warning("No data retrieved from database")
                    return pd.DataFrame()

                df = pd.concat(chunks, ignore_index=True)
                progress_bar.empty()

                # Filter for non-zero total quantity
                df = df[df['total_qty_avail'] != 0]

                # Convert pt_part to string type
                df['pt_part'] = df['pt_part'].astype(str)

                # Fill NA values
                df['pt_dsgn_grp'] = df['pt_dsgn_grp'].fillna('')
                df['pt_prod_line'] = df['pt_prod_line'].fillna('')
                df['pt__chr02'] = df['pt__chr02'].fillna('')

                return df
    except Exception as e:
        print(f"Detailed data loading error: {str(e)}")
        st.error(f"Data loading error: {str(e)}")
        return pd.DataFrame()


def get_inventory_data():
    """Get inventory data SQL query with COGS calculations"""
    query = """
    WITH PartInventory AS (
        SELECT 
            CAST(pt.pt_part AS VARCHAR(50)) AS pt_part,
            pt.pt_desc1,
            pt.pt_desc2,
            pt.pt_prod_line, 
            pt.pt__chr02,
            pt.pt_dsgn_grp,
            sd.sct_cst_tot,
            (sd.sct_mtl_tl + sd.sct_mtl_ll) AS MaterialCost,
            ISNULL(ldx.WH_Qty, 0) AS WH_Qty,
            ISNULL(ldx.WIP_Qty, 0) AS WIP_Qty,
            ISNULL(ldx.EXLPICK_Qty, 0) AS EXLPICK_Qty,
            ISNULL(ldx.WH_Qty, 0) + ISNULL(ldx.WIP_Qty, 0) + ISNULL(ldx.EXLPICK_Qty, 0) AS total_qty_avail,
            ISNULL(sd.sct_cst_tot * (ISNULL(ldx.WH_Qty, 0) + ISNULL(ldx.WIP_Qty, 0) + ISNULL(ldx.EXLPICK_Qty, 0)), 0) AS Total_COGS,
            ISNULL(sd.sct_cst_tot * ISNULL(ldx.WH_Qty, 0), 0) AS COGS_WH,
            ISNULL(sd.sct_cst_tot * ISNULL(ldx.WIP_Qty, 0), 0) AS COGS_WIP,
            ISNULL(sd.sct_cst_tot * ISNULL(ldx.EXLPICK_Qty, 0), 0) AS COGS_EXLPICK
        FROM 
            [QADEE2798].[dbo].[pt_mstr] pt
        LEFT JOIN 
            [QADEE2798].[dbo].[sct_det] sd 
            ON pt.pt_part = sd.sct_part 
            AND sd.sct_sim = 'Standard'
        LEFT JOIN (
            SELECT 
                ld.ld_part,
                SUM(CASE WHEN xz.xxwezoned_area_id = 'WH' THEN ld.ld_qty_oh ELSE 0 END) AS WH_Qty,
                SUM(CASE WHEN xz.xxwezoned_area_id = 'WIP' THEN ld.ld_qty_oh ELSE 0 END) AS WIP_Qty,
                SUM(CASE WHEN xz.xxwezoned_area_id = 'EXLPICK' THEN ld.ld_qty_oh ELSE 0 END) AS EXLPICK_Qty
            FROM 
                [QADEE2798].[dbo].[ld_det] ld
            LEFT JOIN 
                [QADEE2798].[dbo].[xxwezoned_det] xz 
                ON ld.ld_loc = xz.xxwezoned_loc
            GROUP BY 
                ld.ld_part
        ) ldx ON pt.pt_part = ldx.ld_part
        WHERE 
            pt.pt_part_type NOT IN ('xc', 'rc')
    )
    SELECT * FROM PartInventory
    ORDER BY Total_COGS DESC
    """
    return query


def main():
    """Main application function"""
    try:
        # Configure the page
        st.set_page_config(
            page_title="Inventory Dashboard-2798 FOAM",
            page_icon="📦",
            layout="wide",
            initial_sidebar_state="expanded"
        )

        # Initialize session state for data
        if 'data' not in st.session_state:
            st.session_state.data = None

        # Sidebar controls
        st.sidebar.title("Dashboard Controls")

        # Add a connection test button
        if st.sidebar.button("Test Database Connection"):
            with get_connection() as conn:
                if conn is not None:
                    st.sidebar.success("Database connection successful!")
                else:
                    st.sidebar.error("Database connection failed!")

        if st.sidebar.button("Refresh Data"):
            st.session_state.data = load_inventory_data()

        # Load or use cached data
        if st.session_state.data is None:
            st.session_state.data = load_inventory_data()

        if not st.session_state.data.empty:
            display_dashboard(st.session_state.data)
        else:
            st.error(
                "No data available. Please check database connection and try again.")

            # Add troubleshooting information
            st.info("""
            Troubleshooting steps:
            1. Verify SQL Server is running and accessible
            2. Check if you have necessary permissions
            3. Verify the connection string details:
               - Server: a265m001
               - Database: QADEE2798
            4. Ensure you're on the correct network
            """)

    except Exception as e:
        st.error(f"Application error: {str(e)}")
        if st.button("Restart Application"):
            st.experimental_rerun()


if __name__ == "__main__":
    import os
    os.environ['STREAMLIT_SERVER_ADDRESS'] = 'localhost'
    main()
