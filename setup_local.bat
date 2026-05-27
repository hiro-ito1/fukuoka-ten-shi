@echo off

echo ========================================
echo fukuoka-ten-shi local setup
echo ========================================

cd /d "%~dp0"

if not exist "local" mkdir local

copy /Y "..\ten-shi\ACTIVE_CODE\app.py" "local\app.py"
copy /Y "..\ten-shi\ACTIVE_CODE\generate_html.py" "local\generate_html_auto.py"
copy /Y "..\ten-shi\ACTIVE_CODE\scraping_engine.py" "local\scraping_engine.py"
copy /Y "..\ten-shi\ACTIVE_CODE\schema.py" "local\schema.py"

if not exist "local\parsers" mkdir local\parsers
copy /Y "..\ten-shi\ACTIVE_CODE\parsers\base_parser.py" "local\parsers\"
copy /Y "..\ten-shi\ACTIVE_CODE\parsers\chikushino.py" "local\parsers\"
copy /Y "..\ten-shi\ACTIVE_CODE\parsers\itoshima.py" "local\parsers\"
copy /Y "..\ten-shi\ACTIVE_CODE\parsers\jonan.py" "local\parsers\"

if not exist "local\DATA" mkdir local\DATA
if exist "..\ten-shi\DATA\events_approved.json" (
    copy /Y "..\ten-shi\DATA\events_approved.json" "local\DATA\"
)
if exist "..\ten-shi\DATA\events_pending.json" (
    copy /Y "..\ten-shi\DATA\events_pending.json" "local\DATA\"
)
if exist "..\ten-shi\DATA\targets.json" (
    copy /Y "..\ten-shi\DATA\targets.json" "local\DATA\"
)

echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Run admin panel:
echo   cd local
echo   python -m streamlit run app.py
echo.

pause