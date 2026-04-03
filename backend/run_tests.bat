@echo off
REM ========================================
REM Test Runner Script for Django Backend
REM ========================================

echo Running all tests...
echo.

REM Activate virtual environment if it exists
if exist venv\Scripts\activate.bat (
    call venv\Scripts\activate.bat
)

REM Run pytest with coverage
pytest apps/ -v --tb=short --nomigrations --cov=apps --cov-report=term-missing

echo.
echo Tests completed!
pause
