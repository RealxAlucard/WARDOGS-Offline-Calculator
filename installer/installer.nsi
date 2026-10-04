Unicode true
SetCompress off
!define APPNAME "WARDOGS Offline Calculator"
!define VERSION "1.0.0"
Name "${APPNAME} ${VERSION}"
OutFile "wardogs-offline-calculator-setup-v1.0.0.exe"
InstallDir "$LOCALAPPDATA\Programs\${APPNAME}"
RequestExecutionLevel user
Icon "installer/icon.ico"
UninstallIcon "installer/icon.ico"
ShowInstDetails nevershow
Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File /r /x bundled-data "build/app/*.*"
  SetOutPath "$INSTDIR\resources\bundled-data"
  SetCompress off
  File "build/bundled-data/tiles-zestafona.tar"
  File "build/bundled-data/tiles-bakurani.tar"
  File "build/bundled-data/tiles-ozeti.tar"
  File "build/bundled-data/tiles-color-zestafona.tar"
  File "build/bundled-data/tiles-color-bakurani.tar"
  File "build/bundled-data/tiles-color-ozeti.tar"
  SetOutPath "$INSTDIR"
  File "installer/icon.ico"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateShortCut "$DESKTOP\${APPNAME}.lnk" "$INSTDIR\${APPNAME}.exe" "" "$INSTDIR\icon.ico"
  CreateDirectory "$SMPROGRAMS\${APPNAME}"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\${APPNAME}.lnk" "$INSTDIR\${APPNAME}.exe" "" "$INSTDIR\icon.ico"
  CreateShortCut "$SMPROGRAMS\${APPNAME}\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayName" "${APPNAME}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayVersion" "${VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}" "DisplayIcon" "$INSTDIR\icon.ico"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\${APPNAME}.lnk"
  RMDir /r "$SMPROGRAMS\${APPNAME}"
  RMDir /r "$APPDATA\${APPNAME}\map-data"
  RMDir /r "$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\${APPNAME}"
SectionEnd
