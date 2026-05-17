@ECHO OFF

pushd %~dp0

REM Command file for Sphinx documentation
REM Usage: make.bat html

if "%SPHINXBUILD%" == "" (
    set SPHINXBUILD=uv run sphinx-build
)
set SOURCEDIR=source
set BUILDDIR=build

if "%1" == "" goto help

%SPHINXBUILD% -b %1 %SOURCEDIR% %BUILDDIR%\%1 %SPHINXOPTS% %O%
goto end

:help
echo.Usage: make.bat ^<target^>
echo.
echo.Targets:
echo.  html       Build standalone HTML pages
echo.  clean      Remove build output

:end
popd
