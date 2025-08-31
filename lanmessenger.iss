; Script Inno Setup para instalar o Lan Messenger
[Setup]
AppName=Lan Messenger
AppVersion=1.0
DefaultDirName={pf}\LanMessenger
DefaultGroupName=Lan Messenger
OutputDir=.
OutputBaseFilename=LanMessengerSetup
Compression=lzma
SolidCompression=yes

[Files]
Source: "dist\main.exe"; DestDir: "{app}"; Flags: ignoreversion
Source: "config.json"; DestDir: "{app}"; Flags: ignoreversion
Source: "icons.ttf"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon.ico"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon_font_mapping.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "app_icons.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "icon_manager.py"; DestDir: "{app}"; Flags: ignoreversion
Source: "emojis\*"; DestDir: "{app}\emojis"; Flags: ignoreversion recursesubdirs createallsubdirs

[Icons]
Name: "{group}\Lan Messenger"; Filename: "{app}\main.exe"; IconFilename: "{app}\icon.ico"
