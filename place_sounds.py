#!/usr/bin/env python3
"""Place les fichiers audio d'un dossier source dans l'arborescence de sortie
selon le CSV EdgeTX (colonnes Filename et Path).

Usage :
    python3 place_sounds.py [source] [csv] [output]

Arguments positionnels (optionnels — valeurs par défaut = comportement historique) :
    source  dossier contenant les fichiers audio      (défaut : ./ok)
    csv     fichier CSV EdgeTX                        (défaut : ./fr-FR.csv)
    output  arborescence de sortie                    (défaut : ./SOUND/fr)

Destination d'une entrée du CSV : <output>/<Path>/<Filename>
Si la colonne Path est vide, le fichier va directement dans <output>/.

Idempotent — relancer ne fait que recopier (override signalé).
"""

import argparse
import csv
import os
import shutil
from collections import Counter

WORKDIR = os.path.dirname(os.path.abspath(__file__))


def main():
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("source", nargs="?", default=os.path.join(WORKDIR, "ok"),
                        help="dossier des fichiers audio source")
    parser.add_argument("csv", nargs="?", default=os.path.join(WORKDIR, "fr-FR.csv"),
                        help="fichier CSV EdgeTX (Filename, Path)")
    parser.add_argument("output", nargs="?", default=os.path.join(WORKDIR, "SOUND", "fr"),
                        help="arborescence de sortie")
    args = parser.parse_args()

    src_dir = os.path.abspath(args.source)
    csv_path = os.path.abspath(args.csv)
    out_dir = os.path.abspath(args.output)

    if not os.path.isfile(csv_path):
        print(f"ERREUR : CSV introuvable : {csv_path}")
        return 1
    if not os.path.isdir(src_dir):
        print(f"ERREUR : dossier source introuvable : {src_dir}")
        return 1

    copied = 0
    missing = []
    overrides = []
    dest_count = Counter()

    with open(csv_path, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            filename = row["Filename"].strip()
            path = row["Path"].strip()

            src = os.path.join(src_dir, filename)
            if not os.path.isfile(src):
                missing.append(filename)
                continue

            # Path vide -> racine de l'output ; sinon sous-dossier <Path>/
            dest_dir = os.path.join(out_dir, path) if path else out_dir
            os.makedirs(dest_dir, exist_ok=True)
            dest = os.path.join(dest_dir, filename)

            is_override = os.path.isfile(dest)
            shutil.copy2(src, dest)
            if is_override:
                overrides.append(f"{path or 'racine'}/{filename}")

            dest_count[path or "racine"] += 1
            copied += 1

    total_csv = copied + len(missing)
    print(f"Source : {src_dir}")
    print(f"CSV    : {csv_path}")
    print(f"Sortie : {out_dir}")
    print()
    print(f"Fichiers copiés : {copied}/{total_csv}")
    print(f"Fichiers manquants dans le dossier source : {len(missing)}")
    if missing:
        for m in missing:
            print(f"  - {m}")
    print(f"Overrides (déjà en place, recopiés) : {len(overrides)}")
    if overrides:
        for o in overrides[:10]:
            print(f"  - {o}")
        if len(overrides) > 10:
            print(f"  ... et {len(overrides) - 10} autres")
    print()
    print("Répartition par destination :")
    for dest, count in sorted(dest_count.items()):
        label = out_dir + "/" if dest == "racine" else f"{out_dir}/{dest}/"
        print(f"  {label} : {count} fichiers")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
