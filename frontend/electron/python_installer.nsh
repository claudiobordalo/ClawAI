; Python Installer NSIS Script
; This script checks for Python installation and offers to install if missing

; Check if Python is installed
Function CheckPython
    ; Check Python in registry
    ReadRegStr $R0 HKLM "SOFTWARE\Python\PythonCore\3.12\InstallPath" ""
    ${If} $R0 != ""
        StrCpy $R1 $R0
        Goto PythonFound
    ${EndIf}
    
    ReadRegStr $R0 HKLM "SOFTWARE\Python\PythonCore\3.11\InstallPath" ""
    ${If} $R0 != ""
        StrCpy $R1 $R0
        Goto PythonFound
    ${EndIf}
    
    ; Check in Program Files
    IfFileExists "$PROGRAMFILES\Python312\python.exe" +2
    StrCpy $R1 "$PROGRAMFILES\Python312\python.exe"
    Goto PythonFound
    
    IfFileExists "$PROGRAMFILES\Python311\python.exe" +2
    StrCpy $R1 "$PROGRAMFILES\Python311\python.exe"
    Goto PythonFound
    
    ; Check in LocalAppData
    IfFileExists "$LOCALAPPDATA\Programs\Python\Python312\python.exe" +2
    StrCpy $R1 "$LOCALAPPDATA\Programs\Python\Python312\python.exe"
    Goto PythonFound
    
    IfFileExists "$LOCALAPPDATA\Programs\Python\Python311\python.exe" +2
    StrCpy $R1 "$LOCALAPPDATA\Programs\Python\Python311\python.exe"
    Goto PythonFound
    
    ; Python not found
    StrCpy $R1 ""
    Goto PythonCheckDone
    
    PythonFound:
    ; Verify it works
    ExecWait '"$R1\python.exe" --version' $R0
    ${If} $R0 == 0
        Goto PythonCheckDone
    ${EndIf}
    
    StrCpy $R1 ""
    
    PythonCheckDone:
FunctionEnd

; Install Python silently
Function InstallPython
    ; Extract Python installer from extraResources
    File "$EXEDIR\python_installer.exe"
    
    ; Run installer silently
    ExecWait '"$EXEDIR\python_installer.exe" /quiet InstallAllUsers=1 PrependPath=1'
FunctionEnd
