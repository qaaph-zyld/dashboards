# Inventory Dashboard

A Streamlit-based dashboard for visualizing and analyzing inventory data from QADEE2798 database.

## Features

- Real-time inventory metrics visualization
- Interactive filtering by:
  - COGS Type (Total_COGS, COGS_WH, COGS_WIP, COGS_EXLPICK)
  - Design Group
  - Product Line
  - CHR02
- Key metrics display:
  - Total Parts
  - COGS Analysis
  - Average Cost per Part
  - Total Quantity
- Visual analytics:
  - Inventory distribution by design group
  - Top 10 parts by COGS

## Prerequisites

- Python 3.12 or higher
- SQL Server access to a265m001
- Windows authentication configured for database access

## Installation

1. Clone the repository:
```bash
git clone https://github.com/qaaph-zyld/dashboards.git
cd dashboards
```

2. Run the dependency installation script:
```bash
install_dependencies.bat
```

Or install dependencies manually with the Cisco proxy:
```bash
pip install --proxy 104.129.196.38:10563 -r requirements.txt
```

## Running the Dashboard

1. Start the Streamlit application:
```bash
streamlit run inventory_data.py
```

2. Open your web browser and navigate to:
```
http://localhost:8502
```

## Database Configuration

The application connects to:
- Server: a265m001
- Database: QADEE2798
- Authentication: Windows Authentication (Trusted Connection)

## Usage

1. Use the sidebar filters to narrow down the data:
   - Select COGS Type for different cost analysis views
   - Filter by Design Group, Product Line, or CHR02
2. View the main metrics at the top of the dashboard
3. Explore the interactive charts:
   - Hover over chart elements for detailed information
   - Click legend items to show/hide categories
4. Scroll down to view the detailed inventory table

## Troubleshooting

- If you encounter database connection issues:
  - Verify your network connection
  - Ensure you have proper database access permissions
  - Check if you're connected to the corporate network
- For visualization issues:
  - Try refreshing the browser page
  - Verify that all dependencies are correctly installed
