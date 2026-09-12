#!/usr/bin/env python3
"""
Génère les fichiers .wav du CSV fr-FR.csv en clonant la voix de ~/sample/GLaDOS1.wav
avec Coqui XTTS v2 (CPU only).

Usage :
    source ~/tts-env/bin/activate
    export COQUI_TOS_AGREED=1
    python3 generate_voices.py \
        --csv ~/fr-FR.csv \
        --speaker-wav ~/sample/GLaDOS1.wav \
        --out-dir ~/output \
        --lang fr

Le script reprend automatiquement là où il s'est arrêté (il saute les fichiers
déjà générés), ce qui est pratique vu la lenteur du CPU pour 234 fichiers.
"""
import argparse
import csv
import os
import re
import sys
import time

# Chiffres seuls mal prononcés par XTTS (pas de contexte phrase) -> on épelle.
DIGITS_FR = {
    "0": "zéro", "1": "un", "2": "deux", "3": "trois", "4": "quatre",
    "5": "cinq", "6": "six", "7": "sept", "8": "huit", "9": "neuf",
    "10": "dix",
}

# Heuristique simple : texte quasi entièrement ASCII + mots anglais typiques
# -> probablement une ligne restée en anglais dans le CSV fr-FR.csv.
EN_HINTS = re.compile(r"\b(mode|speed|on|off|active|high|low|thermal|normal|landing)\b", re.IGNORECASE)


def guess_language(text, default_lang):
    if default_lang != "fr":
        return default_lang
    # accents/caractères français absents + mots anglais présents -> anglais
    has_accents = re.search(r"[àâäéèêëïîôöùûüçÀÂÄÉÈÊËÏÎÔÖÙÛÜÇ]", text)
    if not has_accents and EN_HINTS.search(text):
        return "en"
    return default_lang


def normalize_text(text, lang):
    stripped = text.strip()
    if lang == "fr" and stripped in DIGITS_FR:
        return DIGITS_FR[stripped]
    return text


def main():
    parser = argparse.ArgumentParser(description="Génération TTS batch depuis un CSV (clonage de voix XTTS v2)")
    parser.add_argument("--csv", required=True, help="Chemin vers le fichier CSV (ex: fr-FR.csv)")
    parser.add_argument("--speaker-wav", required=True, help="Chemin vers l'échantillon de voix à cloner (ex: ~/sample/GLaDOS1.wav)")
    parser.add_argument("--out-dir", default="./output", help="Dossier de sortie des .wav générés")
    parser.add_argument("--lang", default="fr", help="Code langue XTTS par défaut (fr, en, ...)")
    parser.add_argument("--auto-lang", action="store_true", help="Détecte automatiquement les lignes anglaises mélangées dans le CSV et bascule --lang en conséquence")
    parser.add_argument("--normalize-digits", action="store_true", help="Épelle les chiffres seuls (0->zéro, etc.) pour une meilleure prononciation")
    parser.add_argument("--text-column", default="Translation", help="Colonne du CSV à synthétiser")
    parser.add_argument("--filename-column", default="Filename", help="Colonne du CSV donnant le nom du fichier de sortie")
    parser.add_argument("--force", action="store_true", help="Régénère même les fichiers déjà présents")
    parser.add_argument("--only", default=None, help="Ne (re)génère que ce(s) fichier(s), séparés par virgule (ex: 0000.wav,armed.wav). Implique --force.")
    parser.add_argument("--retries", type=int, default=1, help="Nombre de tentatives par fichier en cas d'échec (défaut 1)")
    parser.add_argument("--temperature", type=float, default=0.65, help="Température XTTS (défaut 0.75 côté modèle ; plus bas = plus stable/moins d'erreurs de prononciation, moins d'expressivité)")
    args = parser.parse_args()

    csv_path = os.path.expanduser(args.csv)
    speaker_wav = os.path.expanduser(args.speaker_wav)
    out_dir = os.path.expanduser(args.out_dir)

    if not os.path.isfile(csv_path):
        sys.exit(f"CSV introuvable : {csv_path}")
    if not os.path.isfile(speaker_wav):
        sys.exit(f"Échantillon de voix introuvable : {speaker_wav}")

    os.makedirs(out_dir, exist_ok=True)

    # Import ici pour que --help soit instantané même sans l'environnement activé
    from TTS.api import TTS

    print("Chargement du modèle XTTS v2 en mode CPU (peut prendre 1-2 min)...")
    tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2").to("cpu")

    with open(csv_path, encoding="utf-8") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    only_set = set(x.strip() for x in args.only.split(",")) if args.only else None
    force = args.force or only_set is not None

    total = len(rows)
    done = skipped = failed = 0
    t0 = time.time()

    for i, row in enumerate(rows, start=1):
        text = (row.get(args.text_column) or "").strip()
        filename = (row.get(args.filename_column) or "").strip()

        if not text or not filename:
            print(f"[{i}/{total}] Ligne ignorée (texte ou nom de fichier vide) : {row}")
            skipped += 1
            continue

        if only_set is not None and filename not in only_set:
            skipped += 1
            continue

        out_path = os.path.join(out_dir, filename)

        if os.path.exists(out_path) and not force:
            print(f"[{i}/{total}] Déjà présent, on saute : {filename}")
            skipped += 1
            continue

        lang = guess_language(text, args.lang) if args.auto_lang else args.lang
        spoken_text = normalize_text(text, lang) if args.normalize_digits else text

        tag = f" [lang={lang}]" if lang != args.lang else ""
        print(f"[{i}/{total}] Génération '{filename}'{tag} <- \"{spoken_text}\"")

        last_err = None
        for attempt in range(1, args.retries + 1):
            try:
                tts.tts_to_file(
                    text=spoken_text,
                    speaker_wav=speaker_wav,
                    language=lang,
                    file_path=out_path,
                    temperature=args.temperature,
                )
                last_err = None
                break
            except Exception as e:
                last_err = e
                print(f"  .. tentative {attempt}/{args.retries} échouée: {e}")

        if last_err is None:
            done += 1
        else:
            print(f"  !! ÉCHEC définitif sur '{filename}': {last_err}")
            failed += 1

    elapsed = time.time() - t0
    print("\n== Terminé ==")
    print(f"Générés : {done}, Ignorés (déjà présents/vides) : {skipped}, Échecs : {failed}")
    print(f"Temps total : {elapsed:.0f}s")


if __name__ == "__main__":
    main()
