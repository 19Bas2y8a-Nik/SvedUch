; Сборка: версия подставляется из version.py скриптом build_installer.py
; Соберите инсталлятор: python build_installer.py
#include "version_is.issi"

[Setup]
AppName=SvedUch
AppVersion={#AppVersion}
; Один и тот же AppId для всех версий — установка новой версии обновляет программу, а не удаляет и ставит заново
AppId={{A1B2C3D4-E5F6-7890-ABCD-EF1234567890}}
AppPublisher=SvedUch
DefaultDirName={autopf}\SvedUch
DefaultGroupName=SvedUch
; При обновлении использовать ту же папку и ту же группу в меню Пуск
UsePreviousAppDir=yes
UsePreviousGroup=yes
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

; При обновлении удалить exe предыдущей версии (имя файла содержит версию), затем установить новый
[InstallDelete]
Type: files; Name: "{app}\SvedUch-*.exe"

[Files]
Source: "dist\SvedUch-{#AppVersion}.exe"; DestDir: "{app}"; Flags: ignoreversion

[Icons]
Name: "{group}\SvedUch"; Filename: "{app}\SvedUch-{#AppVersion}.exe"; Comment: "Журнал завуча"
Name: "{group}\Удалить SvedUch"; Filename: "{uninstallexe}"
Name: "{autodesktop}\SvedUch"; Filename: "{app}\SvedUch-{#AppVersion}.exe"; Tasks: desktopicon; Comment: "Журнал завуча"

[Run]
Filename: "{app}\SvedUch-{#AppVersion}.exe"; Description: "Запустить SvedUch"; Flags: nowait postinstall skipifsilent

; === Секция Uninstall: удаление программы ===
; Inno Setup создаёт uninstall.exe автоматически. Пункт «Удалить SvedUch» — в меню Пуск (см. [Icons]).

[UninstallRun]
; Дополнительные действия перед удалением (при необходимости раскомментируйте)
; Filename: "{app}\SvedUch-{#AppVersion}.exe"; Parameters: "/uninstall"; RunOnceId: "SvedUchUninstall"

[UninstallDelete]
; Удалить логи приложения
Type: files; Name: "{app}\*.log"
; Удалить папку приложения, если пуста
Type: dirifempty; Name: "{app}"

[Code]
function InitializeSetup(): Boolean;
begin
  Result := True;
end;
