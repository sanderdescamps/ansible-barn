#!/bin/bash

CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" >/dev/null 2>&1 && pwd )"
ln -sf $CURRENT_DIR/ansible-barn.py ~/.local/bin/ansible-barn
echo "Added ansible-barn in ~/.local/bin/ansible-barn"

echo "For autocomplete, add following line in ~/.bashrc"
echo '   >>>  eval "$(_ANSIBLE_BARN_COMPLETE=source_bash ansible-barn)"'