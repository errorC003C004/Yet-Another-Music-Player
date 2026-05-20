@echo off
color 2
goto full
:full
pyinstaller !musicplayer.py ^
  --collect-data pykakasi ^
  --collect-all argostranslate ^
  --hidden-import scipy._cyutility ^
  --collect-submodules scipy ^
  --noconfirm ^
  --windowed ^
  --onefile
exit

:part
pyinstaller !musicplayer.py ^
  --collect-data pykakasi ^
  --hidden-import scipy._cyutility ^
  --exclude-module argostranslate ^
  --exclude-module torch ^
  --exclude-module torchvision ^
  --exclude-module torchaudio ^
  --noconfirm ^
  --windowed ^
  --onefile
exit
