#!/usr/bin/env bash
# wavConverter.sh — Convertit récursivement tous les .wav d'un dossier vers 32 kHz,
# mono, PCM 16 bits (format attendu par EdgeTX), en conservant la structure et les noms.
#
# Usage :
#   bash wavConverter.sh --input-folder <dossier_source> --output-folder <dossier_cible>

set -euo pipefail

INPUT=""
OUTPUT=""

while [[ $# -gt 0 ]]; do
    case "$1" in
        --input-folder)
            INPUT="$2"; shift 2 ;;
        --output-folder)
            OUTPUT="$2"; shift 2 ;;
        *)
            echo "Option inconnue : $1" >&2; exit 1 ;;
    esac
done

if [[ -z "$INPUT" || -z "$OUTPUT" ]]; then
    echo "Usage : bash wavConverter.sh --input-folder <src> --output-folder <dst>" >&2
    exit 1
fi

if [[ ! -d "$INPUT" ]]; then
    echo "ERREUR : dossier source introuvable : $INPUT" >&2; exit 1
fi

# Chemins absolus pour que la soustraction de préfixe soit fiable
abspath() { printf '%s/%s' "$(cd "$(dirname "$1")" && pwd)" "$(basename "$1")"; }
INPUT="$(abspath "$INPUT")"
mkdir -p "$OUTPUT"
OUTPUT="$(cd "$OUTPUT" && pwd)"

count=0
while IFS= read -r -d '' file; do
    rel="${file#"$INPUT"/}"
    dest="$OUTPUT/$rel"
    mkdir -p "$(dirname "$dest")"
    ffmpeg -nostdin -y -hide_banner -loglevel error -i "$file" \
        -ar 32000 -ac 1 -sample_fmt s16 -c:a pcm_s16le "$dest"
    count=$((count + 1))
done < <(find "$INPUT" -type f -iname '*.wav' -print0 | LC_ALL=C sort -z)

echo "Conversion terminée : $count fichier(s) écrit(s) dans $OUTPUT"
