[Setup]
; Informations générales
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
; Copie du fichier téléchargé depuis {tmp} vers {app} (external pour ne pas l'inclure dans l'installeur)
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

// Renvoie l'URL de téléchargement en fonction de la langue active (français ou anglais)
function GetURL(): string;
begin
  if ActiveLanguage = 'french' then
    Result := 'https://github.com/mini9dev/fakeGames/releases/download/FG/FakeGames.Launcher.exe'
  else
    Result := 'https://github.com/mini9dev/fakeGames/releases/download/FG_en/FakeGames.Launcher.exe';
end;

procedure InitializeWizard();
begin
  // Création d'une page de téléchargement avec titre et description
  DownloadPage := CreateDownloadPage(
    'Téléchargement', 
    'Veuillez patienter pendant le téléchargement des fichiers...', 
    nil
  );
end;

// Cet événement est déclenché avant l'installation (page "Ready")
function NextButtonClick(CurPageID: Integer): Boolean;
begin
  Result := True;
  if CurPageID = wpReady then
  begin
    // Préparer le téléchargement
    DownloadPage.Clear;
    DownloadPage.Add(GetURL(), 'FakeGames.Launcher.exe', '');
    DownloadPage.Show;
    try
      // Lancer le téléchargement (vers {tmp}\FakeGames.Launcher.exe)
      DownloadPage.Download;
      Result := True;  // Continuer vers l'installation si réussi
    except
      // En cas d'erreur de téléchargement ou annulation
      if DownloadPage.AbortedByUser then
      begin
        // Utilisateur a cliqué sur "Stop download", on interrompt l'installation
        Log('Téléchargement annulé par l’utilisateur.');
        Result := False;
      end
      else
      begin
        // Affiche un message d'erreur adapté à la langue
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
