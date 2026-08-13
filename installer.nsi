; GRÁFICOS VICTORTRUCKS - Windows Installer Script
; Build with NSIS (Nullsoft Scriptable Install System)

!include "MUI2.nsh"
!include "FileFunc.nsh"

;--------------------------------
; Installer Attributes
;--------------------------------
Name "GRÁFICOS VICTORTRUCKS"
OutFile "dist\Graficos_VictorTrucks_Setup.exe"
InstallDir "$LOCALAPPDATA\GraficosVictorTrucks"
; Use asInvoker instead of admin - reduces SmartScreen/AV alerts
RequestExecutionLevel user

;--------------------------------
; Version Information
;--------------------------------
VIProductVersion "2.0.0.0"
VIAddVersionKey "ProductName" "GRÁFICOS VICTORTRUCKS"
VIAddVersionKey "ProductVersion" "2.0.0"
VIAddVersionKey "FileDescription" "Launcher de Mods Gráficos para American Truck Simulator"
VIAddVersionKey "FileVersion" "2.0.0.0"
VIAddVersionKey "CompanyName" "VictorTrucks"
VIAddVersionKey "LegalCopyright" "© 2026 VictorTrucks"
VIAddVersionKey "OriginalFilename" "Graficos_VictorTrucks_Setup.exe"
VIAddVersionKey "InternalName" "Graficos_VictorTrucks_Setup"
VIAddVersionKey "Comments" "Instalador oficial de GRÁFICOS VICTORTRUCKS"
VIAddVersionKey "LegalTrademarks" "VictorTrucks"
VIAddVersionKey "PrivateBuild" "2.0.0"
VIAddVersionKey "SpecialBuild" "Release"

;--------------------------------
; Interface Settings
;--------------------------------
!define MUI_ABORTWARNING
!define MUI_ICON "logo.ico"
!define MUI_UNICON "logo.ico"
!define MUI_HEADERIMAGE
!define MUI_HEADERIMAGE_RIGHT

;--------------------------------
; Pages
;--------------------------------
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "LICENSE.txt"
!insertmacro MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH

!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

;--------------------------------
; Languages
;--------------------------------
!insertmacro MUI_LANGUAGE "Spanish"
!insertmacro MUI_LANGUAGE "English"

;--------------------------------
; Installer Sections
;--------------------------------
Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    
    ; Copy launcher executable
    File "dist\Graficos_VictorTrucks.exe"
    
    ; Create Start Menu shortcut
    CreateDirectory "$SMPROGRAMS\GRÁFICOS VICTORTRUCKS"
    CreateShortcut "$SMPROGRAMS\GRÁFICOS VICTORTRUCKS\GRÁFICOS VICTORTRUCKS.lnk" "$INSTDIR\Graficos_VictorTrucks.exe"
    CreateShortcut "$DESKTOP\GRÁFICOS VICTORTRUCKS.lnk" "$INSTDIR\Graficos_VictorTrucks.exe"
    
    ; Uninstaller
    WriteUninstaller "$INSTDIR\Uninstall.exe"
    
    ; Registry uninstall entry (HKCU since we run as user)
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GraficosVictorTrucks" "DisplayName" "GRÁFICOS VICTORTRUCKS"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GraficosVictorTrucks" "DisplayVersion" "2.0.0"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GraficosVictorTrucks" "Publisher" "VictorTrucks"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GraficosVictorTrucks" "UninstallString" "$INSTDIR\Uninstall.exe"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GraficosVictorTrucks" "DisplayIcon" "$INSTDIR\Graficos_VictorTrucks.exe"
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GraficosVictorTrucks" "NoModify" 1
    WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GraficosVictorTrucks" "NoRepair" 1
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GraficosVictorTrucks" "InstallLocation" "$INSTDIR"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GraficosVictorTrucks" "URLInfoAbout" "https://github.com/VictorTrucks"
    WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GraficosVictorTrucks" "EstimatedSize" "50000"
SectionEnd

;--------------------------------
; Uninstaller Section
;--------------------------------
Section "Uninstall"
    ; Remove shortcuts
    Delete "$SMPROGRAMS\GRÁFICOS VICTORTRUCKS\GRÁFICOS VICTORTRUCKS.lnk"
    RMDir "$SMPROGRAMS\GRÁFICOS VICTORTRUCKS"
    Delete "$DESKTOP\GRÁFICOS VICTORTRUCKS.lnk"
    
    ; Remove registry entries
    DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GraficosVictorTrucks"
    
    ; Remove installation files
    Delete "$INSTDIR\Graficos_VictorTrucks.exe"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir "$INSTDIR"
SectionEnd