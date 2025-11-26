#define MyAppPublisher "swg"
#define MyAppURL "https://github.com/mini9dev/fakeGames"

[Setup]
AppName=FakeGames Launcher
AppVersion=1.5

AppPublisher={#MyAppPublisher}
AppPublisherURL={#MyAppURL}
AppSupportURL={#MyAppURL}
AppUpdatesURL={#MyAppURL}

DefaultDirName={userdocs}\FakeGamesLauncher
AppendDefaultDirName=no
DefaultGroupName=FakeGames Launcher
OutputBaseFilename=setup_FakeGames
Compression=lzma
SolidCompression=yes

PrivilegesRequired=lowest
PrivilegesRequiredOverridesAllowed=dialog

[Languages]
Name: "english"; MessagesFile: "compiler:Default.isl"
Name: "french"; MessagesFile: "compiler:Languages\French.isl"

[Components]
Name: "appfr"; Description: "Version française de l'application"; Types: full; Flags: exclusive
Name: "appen"; Description: "English version of the application"; Types: full; Flags: exclusive

[Files]
Source: "fakeGamesLauncher_VF.exe"; DestDir: "{app}"; DestName: "FakeGamesLauncher.exe"; Components: appfr; Flags: ignoreversion
Source: "fakeGamesLauncher_VA.exe"; DestDir: "{app}"; DestName: "FakeGamesLauncher.exe"; Components: appen; Flags: ignoreversion
Source: "FakeGamesGitHub.url"; DestDir: "{app}"; Flags: ignoreversion uninsneveruninstall

[UninstallDelete]
Type: filesandordirs; Name: "{app}\cache_images"
Type: filesandordirs; Name: "{app}\fakeGames_downloads"
Type: files; Name: "{app}\FakeGamesLauncher.exe"

[Run]
Filename: "{app}\FakeGamesLauncher.exe"; Description: "Launch FakeGames Launcher"; Flags: nowait postinstall skipifsilent
