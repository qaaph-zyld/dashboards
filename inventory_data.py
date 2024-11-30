import os
import logging
from typing import Dict, Any, Optional

import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from sqlalchemy import create_engine, text
from dotenv import load_dotenv
import time
from datetime import datetime

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()

def get_connection_string():
    """Generate database connection string based on environment variables"""
    db_type = os.getenv('DB_TYPE', 'mssql')
    db_server = os.getenv('DB_SERVER', 'a265m001')
    db_name = os.getenv('DB_NAME', 'QADEE2798')
    db_user = os.getenv('DB_USER', '')
    db_password = os.getenv('DB_PASSWORD', '')
    db_port = os.getenv('DB_PORT', '1433')
    db_driver = os.getenv('DB_DRIVER', 'ODBC Driver 17 for SQL Server')

    if db_type == 'mssql':
        if not db_user:  # Windows Authentication
            return f'mssql+pymssql://{db_server}/{db_name}?trusted_connection=yes'
        return f'mssql+pymssql://{db_user}:{db_password}@{db_server}:{db_port}/{db_name}'
    elif db_type == 'postgresql':
        return f'postgresql+psycopg2://{db_user}:{db_password}@{db_server}:{db_port}/{db_name}'
    elif db_type == 'mysql':
        return f'mysql+pymysql://{db_user}:{db_password}@{db_server}:{db_port}/{db_name}'
    else:
        raise ValueError(f"Unsupported database type: {db_type}")

from contextlib import contextmanager

@contextmanager
def get_connection():
    """Context manager for database connections using SQLAlchemy"""
    engine = None
    try:
        connection_string = get_connection_string()
        engine = create_engine(connection_string)
        print(f"Attempting to connect to database...")
        with engine.connect() as connection:
            print("Successfully connected to database")
            yield connection
    except Exception as e:
        print(f"Detailed database connection error: {str(e)}")
        st.error(f"Database connection error: {str(e)}")
        yield None
    finally:
        if engine:
            engine.dispose()
            print("Database connection closed")


class InventoryDataProcessor:
    """
    Advanced data processing and analysis for inventory management
    """
    @staticmethod
    def load_inventory_data():
        """
        Load and process inventory data with comprehensive error handling
        """
        query = text("""
            SELECT 
                pt_part,
                pt_desc1,
                pt_dsgn_grp,
                pt_prod_line,
                pt__chr02,
                total_qty_avail,
                ROUND(Total_COGS, 2) as Total_COGS,
                ROUND(COGS_WH, 2) as COGS_WH,
                ROUND(COGS_WIP, 2) as COGS_WIP,
                ROUND(COGS_EXLPICK, 2) as COGS_EXLPICK
            FROM (
                SELECT 
                    pt_part,
                    pt_desc1,
                    pt_dsgn_grp,
                    pt_prod_line,
                    pt__chr02,
                    SUM(qty_avail) as total_qty_avail,
                    SUM(qty_avail * pt_cost) as Total_COGS,
                    SUM(CASE WHEN ld_loc = 'WH' THEN qty_avail * pt_cost ELSE 0 END) as COGS_WH,
                    SUM(CASE WHEN ld_loc = 'WIP' THEN qty_avail * pt_cost ELSE 0 END) as COGS_WIP,
                    SUM(CASE WHEN ld_loc = 'EXLPICK' THEN qty_avail * pt_cost ELSE 0 END) as COGS_EXLPICK
                FROM part_master
                JOIN location_detail ON pt_part = ld_part
                WHERE qty_avail > 0
                GROUP BY pt_part, pt_desc1, pt_dsgn_grp, pt_prod_line, pt__chr02
            ) subquery
            ORDER BY Total_COGS DESC
        """)
        
        with get_connection() as conn:
            if conn:
                return pd.read_sql(query, conn)
            return pd.DataFrame()


class InventoryDashboard:
    """
    Streamlit Dashboard for Inventory Management
    """
    @staticmethod
    def create_design_group_chart(df: pd.DataFrame, cogs_column: str):
        """Create design group distribution chart"""
        design_group_data = df.groupby('pt_dsgn_grp')[cogs_column].sum().reset_index()

        fig = px.pie(
            design_group_data,
            values=cogs_column,
            names='pt_dsgn_grp',
            title=f'Inventory Distribution by Design Group',
            hole=0.4
        )
        return fig

    @staticmethod
    def display_dashboard(df: pd.DataFrame):
        """Comprehensive dashboard display"""
        st.title("Inventory Management Dashboard")

        # Sidebar filters
        st.sidebar.header("Filters")

        # Dynamic filter generation
        filter_columns = ['pt_prod_line', 'pt_dsgn_grp']
        filters = {}
        for col in filter_columns:
            unique_values = df[col].dropna().unique()
            filters[col] = st.sidebar.multiselect(
                f"Filter by {col}", unique_values)

        # Apply filters
        filtered_df = df.copy()
        for col, values in filters.items():
            if values:
                filtered_df = filtered_df[filtered_df[col].isin(values)]

        # Key metrics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Unique Parts", filtered_df['pt_part'].nunique())
        with col2:
            st.metric("Total COGS", f"${filtered_df['Total_COGS'].sum():,.2f}")
        with col3:
            st.metric("Average Part Cost", f"${
                      filtered_df['Total_COGS'].mean():,.2f}")

        # Visualizations
        col1, col2 = st.columns(2)
        with col1:
            design_chart = InventoryDashboard.create_design_group_chart(
                filtered_df, 'Total_COGS')
            st.plotly_chart(design_chart)

        # Detailed data table
        st.dataframe(filtered_df)


def main():
    """Main application runner"""
    st.set_page_config(
        page_title="Inventory Dashboard",
        page_icon="📦",
        layout="wide"
    )

    # Load data
    inventory_data = InventoryDataProcessor.load_inventory_data()

    if inventory_data is not None:
        InventoryDashboard.display_dashboard(inventory_data)
    else:
        st.warning("No inventory data available")


if __name__ == "__main__":
    main()
