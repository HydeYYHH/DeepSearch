@echo off
setlocal

set "ROOT_DIR=%~dp0"
set "ROOT_DIR=%ROOT_DIR:~0,-1%"

echo DeepSearch setup

if "%GOOGLE_API_KEY%"=="" (
  set /p GOOGLE_API_KEY=Enter GOOGLE_API_KEY:
)
if "%USE_ONLINE_EMBEDDING%"=="" (
  set USE_ONLINE_EMBEDDING=False
)

pushd "%ROOT_DIR%\search-engine"
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
popd

pushd "%ROOT_DIR%\llm-agent"
if not exist ".venv\Scripts\python.exe" (
  python -m venv .venv
)
".venv\Scripts\python.exe" -m pip install -r requirements.txt
popd

pushd "%ROOT_DIR%\frontend"
if exist "package.json" (
  call npm install
)
popd

start "SearchEngine" cmd /c "set GOOGLE_API_KEY=%GOOGLE_API_KEY% && set USE_ONLINE_EMBEDDING=%USE_ONLINE_EMBEDDING% && cd /d \"%ROOT_DIR%\search-engine\" && .\.venv\Scripts\python.exe server\server.py"
start "LLMAgent" cmd /c "set GOOGLE_API_KEY=%GOOGLE_API_KEY% && set USE_ONLINE_EMBEDDING=%USE_ONLINE_EMBEDDING% && cd /d \"%ROOT_DIR%\llm-agent\" && .\.venv\Scripts\python.exe main.py"
start "Frontend" cmd /c "cd /d \"%ROOT_DIR%\frontend\" && npm run dev"

echo DeepSearch started
exit /b 0
