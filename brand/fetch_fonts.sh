#!/bin/bash
# Fonts used to outline the Emend Press logos (both SIL Open Font License).
# The SVGs contain outlines only, so these are needed just to regenerate them.
set -e
cd "$(dirname "$0")"; mkdir -p fonts
B=https://raw.githubusercontent.com/google/fonts/main/ofl
curl -sL -o "fonts/CormorantGaramond[wght].ttf" "$B/cormorantgaramond/CormorantGaramond%5Bwght%5D.ttf"   # EMEND, SemiBold 600
curl -sL -o "fonts/Montserrat[wght].ttf"        "$B/montserrat/Montserrat%5Bwght%5D.ttf"                 # PRESS, Medium 500
