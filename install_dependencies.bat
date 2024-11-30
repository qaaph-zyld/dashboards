@echo off
echo Installing dependencies with Cisco proxy...
pip install --proxy 104.129.196.38:10563 streamlit==1.16.0
pip install --proxy 104.129.196.38:10563 pandas==1.4.4
pip install --proxy 104.129.196.38:10563 pyodbc==4.0.34
pip install --proxy 104.129.196.38:10563 plotly==5.11.0
echo Installation complete!
pause
