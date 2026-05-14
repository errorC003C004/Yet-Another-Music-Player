@echo off
color 2

pyinstaller !musicplayer.py ^
  --collect-data pykakasi ^
  --collect-all argostranslate ^
  --noconfirm ^
  --windowed ^
  --onefile
