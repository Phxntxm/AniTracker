CALL .env\Scripts\activate
CALL pyinstaller distribute\windows.spec --distpath=dist\windows -y
CALL makensis distribute\anitracker.nsi