@echo off
echo ========================================
echo fukuoka-ten-shi local setup
echo ========================================

cd /d "%~dp0"

if not exist "local" mkdir local
if not exist "local\parsers" mkdir local\parsers
if not exist "local\DATA" mkdir local\DATA

copy /Y "..\ACTIVE_CODE\app.py" "local\app.py"
copy /Y "..\ACTIVE_CODE\generate_html.py" "local\generate_html_auto.py"
copy /Y "..\ACTIVE_CODE\scraping_engine.py" "local\scraping_engine.py"
copy /Y "..\ACTIVE_CODE\schema.py" "local\schema.py"

copy /Y "..\ACTIVE_CODE\parsers\base_parser.py" "local\parsers\"
copy /Y "..\ACTIVE_CODE\parsers\chikushino.py" "local\parsers\"
copy /Y "..\ACTIVE_CODE\parsers\itoshima.py" "local\parsers\"
copy /Y "..\ACTIVE_CODE\parsers\jonan.py" "local\parsers\"

if exist "..\DATA\events_approved.json" copy /Y "..\DATA\events_approved.json" "local\DATA\"
if exist "..\DATA\events_pending.json" copy /Y "..\DATA\events_pending.json" "local\DATA\"
if exist "..\DATA\targets.json" copy /Y "..\DATA\targets.json" "local\DATA\"

python patch_app.py

echo ========================================
echo Setup complete!
echo ========================================
echo.
echo Run admin panel:
echo   cd local
echo   python -m streamlit run app.py
echo.
pause