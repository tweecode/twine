; NOTE: this .NSI script is designed for NSIS v1.8+

; This also packages vcredist_x86.exe v9.0.30729.5677 (which includes the MSVCR90.dll v9.0.30729.6161)
; It can be downloaded from: http://www.microsoft.com/en-us/download/details.aspx?id=26368
; This only works for unicode Python 2.7.3/wxPython2.8. 
; Verify which version of MSVCR90.dll you need using dependancy walker on your Python2x.exe
; Place the vcredist_x86.exe file into the ./build directory and this install does the rest 

Name "Twine 1.4.3"
OutFile "dist\twine-1.4.3-win.exe"

; Some default compiler settings (uncomment and change at will):
; SetCompress auto ; (can be off or force)
; SetDatablockOptimize on ; (can be off)
; CRCCheck on ; (can be off)
; AutoCloseWindow false ; (can be true for the window go away automatically at end)
; ShowInstDetails hide ; (can be show to have them shown, or nevershow to disable)
; SetDateSave off ; (can be on to have files restored to their orginal date)
RequestExecutionLevel highest

InstallDir "$PROGRAMFILES\Twine"
InstallDirRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Twine" ""
;DirShow show ; (make this hide to not let the user change it)
DirText "Choose which folder to install Twine into:"

Section "" ; (default section)
SetOutPath "$INSTDIR"

; add files / whatever that need to be installed here.
; see http://nsis.sourceforge.net/Docs/Chapter4.html#4.9.1.5

File "dist\win32\*.pyd"
File "dist\win32\*.zip"
File "dist\win32\*.dll"
File "dist\win32\twine.exe"
File "dist\win32\gpl.txt"
File /r "dist\win32\targets"
File /r "dist\win32\icons"

; add Start Menu entries

CreateDirectory "$SMPROGRAMS\Twine\"
CreateShortCut "$SMPROGRAMS\Twine\Twine.lnk" "$INSTDIR\twine.exe"
CreateShortCut "$SMPROGRAMS\Twine\Uninstall.lnk" "$INSTDIR\uninstalltwine.exe"

; add uninstall entry in Add/Remove Programs

WriteRegStr HKEY_LOCAL_MACHINE "SOFTWARE\Twine" "" "$INSTDIR"
WriteRegStr HKEY_LOCAL_MACHINE "Software\Microsoft\Windows\CurrentVersion\Uninstall\Twine" "DisplayName" "Twine 1.4.3 (remove only)"
WriteRegStr HKEY_LOCAL_MACHINE "Software\Microsoft\Windows\CurrentVersion\Uninstall\Twine" "UninstallString" '"$INSTDIR\uninstalltwine.exe"'

; file association

WriteRegStr HKCR ".tws" "" "Twine.Story"
WriteRegStr HKCR "Twine.Story" "" "Twine Story"
WriteRegStr HKCR "Twine.Story\DefaultIcon" "" "$INSTDIR\twine.exe,1"
WriteRegStr HKCR "Twine.Story\shell\open\command" "" '"$INSTDIR\twine.exe" "%1"'

!define SHCNE_ASSOCCHANGED 0x08000000
!define SHCNF_IDLIST 0

System::Call 'shell32.dll::SHChangeNotify(i, i, i, i) v (${SHCNE_ASSOCCHANGED}, ${SHCNF_IDLIST}, 0, 0)'

; write out uninstaller

WriteUninstaller "$INSTDIR\uninstalltwine.exe"

; Install Visual Studio Redistributable controls

File "build\vcredist_x86.exe"
ExecWait '"$INSTDIR\vcredist_x86.exe" /qb!'
Delete "$INSTDIR\vcredist_x86.exe"

SectionEnd ; end of default section


; begin uninstall settings/section

UninstallText "This will uninstall Twine 1.4.3 from your system."

Section Uninstall

; add delete commands to delete whatever files/registry keys/etc you installed here.

Delete "$INSTDIR\uninstalltwine.exe"
DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Twine"
DeleteRegKey HKEY_LOCAL_MACHINE "SOFTWARE\Microsoft\Windows\CurrentVersion\Uninstall\Twine"
DeleteRegKey HKCR ".tws"
DeleteRegKey HKCR "Twine.Story"
RMDir /r "$SMPROGRAMS\Twine"
RMDir /r "$INSTDIR"
SectionEnd ; end of uninstall section

; eof
