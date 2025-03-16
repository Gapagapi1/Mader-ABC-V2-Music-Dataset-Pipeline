#!/bin/bash

set -e

mkdir -p archives

echo "Edit this script with the correct path first and appropriate functions called."
exit 1

# Linux
# NOT TESTED, TODO
setup_softwares_linux () {
    cd archives

    wget 'https://ifdo.ca/~seymour/runabc/abcMIDI-2025.02.16.zip'

    cd - > /dev/null
    cd softwares

    unzip '../archives/abcMIDI-2025.02.16.zip'
    echo 'You now have to build abcMidi softwares.'

    cd - > /dev/null

    ln -s '/path/to/musescore/binary/parent/directory' './softwares/musescore' 
}

# Windows
setup_softwares_windows () {
    cd archives
    
    wget 'https://ifdo.ca/~seymour/runabc/abcmidi_win32_mingw64.zip'
    
    cd - > /dev/null
    cd softwares
    
    unzip '../archives/abcmidi_win32_mingw64.zip'
    mv abcmidi_win32_mingw64 abcmidi

    cd - > /dev/null

    echo 'Run a terminal with admin rights and run `mklink /d ".\softwares\musescore" "C:\Program Files\MuseScore 4\bin"` (beware of your current directory, it should be ./data)'
}

# setup_softwares_linux
# setup_softwares_windows
