@echo off
:dependencycheck
echo Checking dependencies...
:: clear variables
set "DOWNLOAD_PYTHON="
set "DOWNLOAD_GIT="
set "DOWNLOAD_NODE="
::goto debug
@echo off
:: Check Python
:: small workarround to windows ghost Python.exe
:: Yes, windows is a bitch...
python -c "exit()" >nul 2>&1
if %ERRORLEVEL%==0 (
    echo Python already installed.
) else (
    echo Python not found, will download and install.
    set "DOWNLOAD_PYTHON=1"
)
:: Check Git
where git >nul 2>nul
if %ERRORLEVEL%==0 (
    echo Git already installed.
) else (
    echo Git not found, will download and install.
    set "DOWNLOAD_GIT=1"
)
:: Check Node.js
where node >nul 2>nul
if %ERRORLEVEL%==0 (
    echo Node.js already installed.
) else (
    echo Node.js not found, will download and install.
    set "DOWNLOAD_NODE=1"
)
pause

:installs
cls
if not "%DOWNLOAD_PYTHON%"=="1" (
	if not "%DOWNLOAD_GIT%"=="1" (
		if not "%DOWNLOAD_NODE%"=="1" (
		goto :versions
		)
	)
)
echo Installing dependencies...
if "%DOWNLOAD_PYTHON%"=="1" (
        echo Installing Python 3.13...
	winget install -e --id Python.Python.3.13 --override "PrependPath=1"
	echo Python installation finished.
)
if "%DOWNLOAD_GIT%"=="1" (
        echo Installing Git...
        winget install -e --id Git.Git --accept-package-agreements --accept-source-agreements
	if %ERRORLEVEL%==0 (
		echo Git installation finished.
	) else (
		echo Git installation FAILED.
	)
)
if "%DOWNLOAD_NODE%"=="1" (
        echo Installing Node.js...
        winget install -e --id OpenJS.NodeJS --accept-package-agreements --accept-source-agreements
	if %ERRORLEVEL%==0 (
		echo Node.js installation finished.
	) else (
		echo Node.js installation FAILED.
	)
)
pause


:versions
cls
echo All dependencies found.
echo.
:: --- REFRESH PATH ---
if "%DOWNLOAD_PYTHON%"=="1" goto REFRESH
if "%DOWNLOAD_GIT%"=="1" goto REFRESH
if "%DOWNLOAD_NODE%"=="1" goto REFRESH
goto no_refresh
:REFRESH
echo.
echo Refreshing PATH from Registry...

:: 1. Get System PATH using the Absolute Path to reg.exe
for /f "skip=1 tokens=2*" %%A in ('%SystemRoot%\System32\reg.exe query "HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Environment" /v Path') do set "sysPath=%%B"

:: 2. Get User PATH
for /f "skip=1 tokens=2*" %%A in ('%SystemRoot%\System32\reg.exe query "HKCU\Environment" /v Path') do set "userPath=%%B"

:: 3. Apply to current session
set "PATH=%sysPath%;%userPath%"

:no_refresh
echo.
python --version
git --version
node --version
echo.
echo Start setup?
pause



:setup
:spot_setup_browser
:: Open the Spotify developer dashboard in default browser
start "" "https://developer.spotify.com/dashboard/applications"
:spot_setup
cls
echo -------------------------------------------
echo Spotify Credentials Setup
echo -------------------------------------------
echo.
echo.
echo If you didnt get redirected please open https://developer.spotify.com/dashboard/applications on your browser.
:spot_setup_propt
:: Prompt user to enter Client ID
set /p SPOTIPY_CLIENT_ID="Paste your Spotify Client ID here: "
:: Prompt user to enter Client Secret
set /p SPOTIPY_CLIENT_SECRET="Paste your Spotify Client Secret here: "

:spot_confirm_prompt
set /p CONFIRM="Are you sure? (Y/N): "
if /i "%CONFIRM%"=="Y" (
    goto env_setup
) else if /i "%CONFIRM%"=="N" (
    goto spot_setup
) else (
    goto spot_confirm_prompt 
)
goto spot_confirm_prompt


:env_setup
cls
echo Starting SpotTransfer setup...
echo.
git clone https://github.com/Pushan2005/SpotTransfer.git
cd SpotTransfer
:: --- Backend setup ---
cd backend
:: Create backend .env with user-provided Spotify credentials
(
echo SPOTIPY_CLIENT_ID=%SPOTIPY_CLIENT_ID%
echo SPOTIPY_CLIENT_SECRET=%SPOTIPY_CLIENT_SECRET%
echo FRONTEND_URL=http://localhost:5173
) > .env
echo Backend .env file created.
echo Installing backend Python packages...
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
echo Backend setup complete.
cd ..
:: --- Frontend setup ---
cd frontend
echo Creating frontend .env file...
(
echo VITE_API_URL=http://localhost:8080
) > .env
:: Install frontend dependencies
echo Installing frontend packages...
echo Waiting on npm installer...
start /wait powershell -Command "npm install --loglevel verbose 2>&1 | Tee-Object npm-log.txt"
echo Frontend install complete!

:run_setup
:: Create run.bat inside SpotTransfer
cd SpotTransfer
cd ..
::have both here just in case lol
(
echo @echo off
echo title SpotTransfer Launcher
echo.
echo echo Starting SpotTransfer...
echo echo.
echo.
echo :: Start backend
echo echo Launching backend...
echo start "SpotTransfer Backend" cmd /k "cd backend && python main.py"
echo.
echo :: Start frontend
echo echo Launching frontend...
echo start "SpotTransfer Frontend" cmd /k "cd frontend && npm run dev -- --host"
echo.
echo echo.
echo echo SpotTransfer is starting.
echo echo Backend:  http://127.0.0.1:8080
echo echo Frontend: http://localhost:5173
echo echo.
echo start "" "http://localhost:5173/create-playlist"
) > run.bat
echo.
echo.
echo.
echo.
echo Congrats!
echo.
echo The installer ran succesfully.
echo We have included a run.bat file that will conviniently run things for you.
echo.
echo You may now safely delete the installer. :)
pause