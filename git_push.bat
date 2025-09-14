@echo off
setlocal

echo.
echo ===================================
echo  Git Push Helper (Robust Version)
echo ===================================
echo.

:: Check if this is a git repository before doing anything
git rev-parse --is-inside-work-tree >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo ERROR: This is not a Git repository. Aborting.
    goto end
)

set /p commitMessage="Enter your commit message: "

if not defined commitMessage (
    echo.
    echo No commit message entered. Aborting.
    goto end
)

echo.
echo Staging all files...
git add .
if %ERRORLEVEL% neq 0 (
    echo ERROR: 'git add' failed. Please check the output above.
    goto end
)

echo.
echo Committing with message: "%commitMessage%"
git commit -m "%commitMessage%"
if %ERRORLEVEL% neq 0 (
    echo WARNING: 'git commit' did not complete successfully.
    echo This is often because there are no changes to commit.
    echo Aborting push.
    goto end
)

echo.
echo Pushing to remote repository...
git push
if %ERRORLEVEL% neq 0 (
    echo ERROR: 'git push' failed. You may need to 'git pull' first or check your connection/credentials.
    goto end
)

echo.
echo --- Process Complete ---
echo.

:end
pause