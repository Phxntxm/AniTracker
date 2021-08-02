#!/bin/bash

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" &> /dev/null && pwd )"

mkdir -p $HOME/.local/bin/ $HOME/.local/share/applications/ 2> /dev/null
rm $HOME/.local/bin/anitracker 2> /dev/null

ln -s $SCRIPT_DIR/anitracker/anitracker $HOME/.local/bin/anitracker
sed -i "s|Path=|Path=$SCRIPT_DIR|" $SCRIPT_DIR/anitracker.desktop
cp $SCRIPT_DIR/anitracker.desktop $HOME/.local/share/applications/anitracker.desktop

echo "Setup finished!"
echo "Added anitracker to ~/.local/bin (make sure this is in your PATH) and added a desktop entry"
