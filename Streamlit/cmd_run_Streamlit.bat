@echo off
cd C:\source\taihan\Scripts
call activate
cd C:\source\Streamlit
start /B streamlit run fiber_streamlit.py --server.port 8502