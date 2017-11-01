mkdir -p ./dist
rm -rf ./dist/*
python compile.py
cp -r icon.png Menu.png game-over.jpg the-end.jpg chat map mob npc players portals questeffects shots sound ui dist
rm ./dist/w9xpopen.exe
rm -rf ./dist/tcl