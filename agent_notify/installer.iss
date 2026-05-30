; Agent Notify — Inno Setup 安装脚本
; 用 Inno Setup 6 打包为 Windows 安装程序
;
; 使用方法：
;   1. 先用 PyInstaller 打包：pyinstaller agent_notify.spec --noconfirm
;   2. 用 Inno Setup 编译此脚本：iscc installer.iss
;   3. 产物在 output/AgentNotifySetup.exe

#define MyAppName "Agent Notify"
#define MyAppVersion "1.2.0"
#define MyAppPublisher "WUW"
#define MyAppURL "https://github.com/wuw22458/agent_notify"
#define MyAppExeName "AgentNotify.exe"
#define MyAppSourceDir "dist"

[Setup]
AppId={{B8E5C2A1-7F3D-4E6B-9A1C-2D4F6E8B0A3C}
AppName={#MyAppName}
AppVersion={#MyAppVersion}
AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}/issues
AppUpdatesURL={#MyAppURL}/releases
DefaultDirName={autopf}\{#MyAppName}
DefaultGroupName={#MyAppName}
LicenseFile=LICENSE
OutputDir=output
OutputBaseFilename=AgentNotifySetup
SetupIconFile=resources\icon.ico
UninstallDisplayIcon={app}\{#MyAppExeName}
Compression=lzma2/ultra64
SolidCompression=yes
WizardStyle=modern
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
; 暗色主题配色
WizardImageBackColor=$131118
BackColor=$13118
BackColor2=$1E1B2E

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"

[Tasks]
Name: "desktopicon"; Description: "{cm:CreateDesktopIcon}"; GroupDescription: "{cm:AdditionalIcons}"; Flags: unchecked
Name: "autostart"; Description: "开机自动启动"; GroupDescription: "其他选项:"; Flags: checkedonce

[Files]
Source: "{#MyAppSourceDir}\{#MyAppExeName}"; DestDir: "{app}"; Flags: ignoreversion
; 如果有其他资源文件需要随安装包分发，在这里添加
; Source: "resources\*"; DestDir: "{app}\resources"; Flags: ignoreversion recursesubdirs

[Icons]
; 开始菜单快捷方式
Name: "{group}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"
Name: "{group}\{cm:UninstallProgram,{#MyAppName}}"; Filename: "{uninstallexe}"
; 桌面快捷方式
Name: "{autodesktop}\{#MyAppName}"; Filename: "{app}\{#MyAppExeName}"; Tasks: desktopicon

[Registry]
; 开机自启（仅当用户选择了 autostart 任务时）
Root: HKA; Subkey: "Software\Microsoft\Windows\CurrentVersion\Run"; \
    ValueType: string; ValueName: "AgentNotify"; ValueData: """{app}\{#MyAppExeName}"""; \
    Flags: uninsdeletevalue; Tasks: autostart

[Run]
; 安装完成后可选启动
Filename: "{app}\{#MyAppExeName}"; Description: "{cm:LaunchProgram,{#StringChange(MyAppName, '&', '&&')}}"; \
    Flags: nowait postinstall skipifsilent unchecked

[UninstallRun]
; 卸载前先退出进程
Filename: "{cmd}"; Parameters: "/C taskkill /F /IM {#MyAppExeName} >nul 2>&1"; \
    Flags: runhidden; RunOnceId: "KillAgentNotify"

[UninstallDelete]
Type: filesandordirs; Name: "{app}"
; 清理用户数据（可选，取消注释则卸载时删除配置）
; Type: filesandordirs; Name: "{userappdata}\.agent-notify"

[Code]
// 安装前检测是否正在运行
function InitializeSetup(): Boolean;
var
  ResultCode: Integer;
begin
  Result := True;
  // 尝试结束正在运行的进程（静默）
  Exec('cmd', '/C taskkill /F /IM {#MyAppExeName} >nul 2>&1', '', 
    SW_HIDE, ewWaitUntilTerminated, ResultCode);
end;
