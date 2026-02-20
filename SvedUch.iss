; Сборка: версия подставляется из version.py скриптом build_installer.py
; Соберите инсталлятор: python build_installer.py
#include "version_is.issi"

[Setup]
AppName=SvedUch
AppVersion={#AppVersion}
AppPublisher=SvedUch
DefaultDirName={autopf}\SvedUch
DefaultGroupName=SvedUch
OutputDir=installer_output
OutputBaseFilename=SvedUch-{#AppVersion}-Setup
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=admin
ArchitecturesInstallIn64BitMode=x64compatible
UninstallDisplayName=SvedUch {#AppVersion}
UninstallDisplayIcon={app}\SvedUch-{#AppVersion}.exe

[Languages]
Name: "russian"; MessagesFile: "compiler:Languages\Russian.isl"

[Tasks]
Name: "desktopicon"; Description: "Создать значок на рабочем столе"; GroupDescription: "Дополнительно:"; Flags: unchecked

[Files]
Source: "dist\SvedUch-{#AppVersion}.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SvedUch"; Filename: "{app}\SvedUch-{#AppVersion}.exe"; Comment: "Журнал завуча"
Name: "{group}\Удалить SvedUch"; Filename: "{uninstallexe}"
Name: "{autodesktop}\SvedUch"; Filename: "{app}\SvedUch-{#AppVersion}.exe"; Tasks: desktopicon; Comment: "Журнал завуча"

[Run]
Filename: "{app}\SvedUch-{#AppVersion}.exe"; Description: "Запустить SvedUch"; Flags: nowait postinstall skipifsilent

[UninstallRun]
; Дополнительные действия при удалении (при необходимости добавьте команды)
; Пример: Filename: "{app}\SvedUch-{#AppVersion}.exe"; Parameters: "/uninstall"

[UninstallDelete]
Type: files; Name: "{app}\*.log"
Type: dirifempty; Name: "{app}"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
