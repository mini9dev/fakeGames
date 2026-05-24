[Setup]
AppName=FakeGames Launcher
AppVersion=2.0
AppPublisher=swg
AppId={{D1E0B870-1234-4F56-89AB-1234567890AB}}
PrivilegesRequired=lowest
LanguageDetectionMethod=uilanguage
ShowLanguageDialog=no
DefaultDirName={localappdata}\FG Launcher
DisableDirPage=yes
DefaultGroupName=FakeGames Launcher
OutputBaseFilename=setup_FakeGames
Compression=lzma2
SolidCompression=yes
WizardStyle=modern
SetupIconFile=icon.ico

[Languages]
Name: "french";  MessagesFile: "compiler:Languages\French.isl"
Name: "english"; MessagesFile: "compiler:Default.isl"

[Files]
Source: "{tmp}\FakeGames.Launcher.exe"; DestDir: "{app}"; Flags: external ignoreversion

[Icons]
Name: "{group}\FakeGames Launcher";   Filename: "{app}\FakeGames.Launcher.exe"
Name: "{autodesktop}\FakeGames Launcher"; Filename: "{app}\FakeGames.Launcher.exe"

[Run]
Filename: "{app}\FakeGames.Launcher.exe"; Flags: nowait postinstall skipifsilent

[UninstallDelete]
Type: filesandordirs; Name: "{app}"

[Code]
var
  DownloadPage: TDownloadWizardPage;

function GetURL(): string;
begin
  if ActiveLanguage = 'french' then
    Result := 'https://github.com/mini9dev/fakeGames/releases/download/FG/FakeGames.Launcher.exe'
  else
    Result := 'https://github.com/mini9dev/fakeGames/releases/download/FG_en/FakeGames.Launcher.exe';
end;

procedure InitializeWizard();
begin
  DownloadPage := CreateDownloadPage(
    'Téléchargement', 
    'Veuillez patienter pendant le téléchargement des fichiers...', 
    nil
  );
end;

function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpReady then
  begin
    DownloadPage.Clear;
    DownloadPage.Add(GetURL(), 'FakeGames.Launcher.exe', '');
    DownloadPage.Show;
    try
      DownloadPage.Download;
      Result := True; 
    except
      if DownloadPage.AbortedByUser then
      begin
        Log('Téléchargement annulé par l’utilisateur.');
        Result := False;
      end
      else
      begin
        if ActiveLanguage = 'french' then
          MsgBox('Le téléchargement a échoué.', mbError, MB_OK)
        else
          MsgBox('Download failed.', mbError, MB_OK);
        Result := False;
      end;
    end;
    DownloadPage.Hide;
  end;
end;
