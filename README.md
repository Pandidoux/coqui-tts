# coqui-tts — Génération de voix par clonage avec Coqui XTTS v2

Outils Python et Bash pour générer en lot des fichiers audio à partir d'un CSV, en clonant une voix de référence via le modèle [Coqui TTS (XTTS v2)](https://github.com/coqui-ai/TTS).

> **Usage principal** : création de packs vocaux EdgeTX (modèles radio RC) avec la voix de GLaDOS (Portal), mais conçu pour être réutilisable sur tout projet TTS.

---

## 📁 Structure du dépôt

```
├── install_coqui.sh          # Installation de Coqui TTS + dépendances
├── generate_voices.py        # Script principal — génération batch depuis un CSV
├── wavConverter.sh           # Conversion audio (24kHz → 32kHz, mono, PCM)
├── place_sounds.py           # Placement des fichiers dans l'arborescence cible
└── EdgeTX/                   # Exemple de données EdgeTX
    ├── fr-FR.csv             # CSV complet EdgeTX (234 entrées)
    └── fr-FR_scripts.csv     # CSV scripts EdgeTX (178 entrées)
```

---

## 🚀 Installation rapide

### Prérequis

- **Ubuntu 18.04+** (testé sur Ubuntu 24 / Debian 12)
- **Python 3.11+** (installé automatiquement par le script)
- **ffmpeg** et **espeak-ng** (dépendances système)
- Environnement `screen` ou `tmux` recommandé (la génération est longue en CPU)

### Script d'installation

```bash
# Télécharge, installe Python 3.11, crée un venv isolé, installe PyTorch CPU + Coqui TTS
bash install_coqui.sh
```

Le script fait tout :

| Étape | Action |
|-------|--------|
| 1/6   | Installe les dépendances système (`ffmpeg`, `libsndfile1`, `build-essential`, `curl`, `espeak-ng`) |
| 2/6   | Installe [`uv`](https://github.com/astral-sh/uv) (gestionnaire de paquets Python rapide) |
| 3/6   | Télécharge et installe **Python 3.11** de manière isolée |
| 4/6   | Crée un environnement virtuel dans `~/tts-env` |
| 5/6   | Installe PyTorch (CPU only, version pinée < 2.9) puis Coqui TTS + transformers |
| 6/6   | Télécharge et valide le modèle **XTTS v2** (~2 Go, premier chargement long) |

### Activation manuelle

```bash
source ~/tts-env/bin/activate
export COQUI_TOS_AGREED=1    # Accepte la licence CPML automatiquement
```

---

## 🎙️ Génération des fichiers audio

### Commande de base

```bash
python3 generate_voices.py \
    --csv ~/fr-FR-trad.csv \
    --speaker-wav ~/sample/GLaDOS_1h.wav \
    --out-dir ~/patch \
    --lang fr \
    --text-column "Translation"
```

### Arguments complets de `generate_voices.py`

| Argument | Obligatoire | Défaut | Description |
|----------|:-----------:|--------|-------------|
| `--csv` | ✅ | — | Chemin vers le fichier CSV (ex: `fr-FR.csv`). Le CSV doit contenir les colonnes spécifiées par `--text-column` et `--filename-column`. |
| `--speaker-wav` | ✅ | — | Fichier audio WAV de référence dont on clone la voix (ex: `~/sample/GLaDOS_1h.wav`). Un échantillon propre de 30s à 2 min est suffisant. |
| `--out-dir` | ❌ | `./output` | Dossier où seront écrits les fichiers `.wav` générés. |
| `--lang` | ❌ | `fr` | Code langue XTTS par défaut (`fr`, `en`, `de`, etc.). |
| `--auto-lang` | ❌ | désactivé | Détecte automatiquement les lignes en anglais dans un CSV français et bascule la langue pour ces lignes uniquement. Utile si le CSV contient du texte non traduit. |
| `--normalize-digits` | ❌ | désactivé | Épelle les chiffres seuls (0 → "zéro", 1 → "un", etc.) pour une meilleure prononciation par XTTS. |
| `--text-column` | ❌ | `"Translation"` | Nom de la colonne du CSV contenant le texte à synthétiser. |
| `--filename-column` | ❌ | `"Filename"` | Nom de la colonne du CSV donnant le nom du fichier `.wav` de sortie. |
| `--force` | ❌ | désactivé | Force la régénération même si le fichier de sortie existe déjà. |
| `--only` | ❌ | tous | Ne génère que les fichiers spécifiés, séparés par des virgules (ex: `0000.wav,armed.wav`). Équivalent à `--force`. |
| `--retries` | ❌ | `1` | Nombre de tentatives par fichier en cas d'erreur. Utile si certaines générations échouent aléatoirement. |
| `--temperature` | ❌ | `0.65` | Température XTTS (la valeur par défaut du modèle est 0.75). Plus bas = prononciation plus stable mais moins expressif. Plus haut = plus expressif mais risque d'erreurs. |

### Comportement automatique

Le script intègre plusieurs intelligences :

1. **Reprise automatique** — Les fichiers déjà générés sont sautés (`Déjà présent, on saute`). Relancez le script après une interruption, il reprend là où il s'est arrêté.
2. **Détection de langue auto** (`--auto-lang`) — Si une ligne contient des mots anglais typiques (`mode`, `speed`, `on`, `off`, etc.) sans accents français, elle est synthétisée en anglais automatiquement.
3. **Normalisation des chiffres** (`--normalize-digits`) — XTTS prononce mal les chiffres seuls. Cette option remplace `0` par `zéro`, `1` par `un`, etc.

### Exemples avancés

```bash
# Régénérer uniquement 2 fichiers qui ont mal sonné
python3 generate_voices.py \
    --csv ~/fr-FR-trad.csv \
    --speaker-wav ~/sample/GLaDOS_1h.wav \
    --out-dir ~/patch \
    --lang fr \
    --only "0042.wav,0157.wav"

# Générer avec une température plus basse pour plus de stabilité
python3 generate_voices.py \
    --csv ~/fr-FR-trad.csv \
    --speaker-wav ~/sample/GLaDOS_1h.wav \
    --out-dir ~/patch \
    --lang fr \
    --temperature 0.5 \
    --retries 3

# Détecter automatiquement les lignes en anglais restantes
python3 generate_voices.py \
    --csv ~/fr-FR-trad.csv \
    --speaker-wav ~/sample/GLaDOS_1h.wav \
    --out-dir ~/patch \
    --lang fr \
    --auto-lang \
    --normalize-digits
```

### Format du CSV attendu

Le CSV doit être au format **UTF-8 avec en-têtes** et contenir au minimum :

| Colonne | Description | Exemple |
|---------|-------------|---------|
| `Translation` (ou via `--text-column`) | Texte à synthétiser | `"Batterie critique"` |
| `Filename` (ou via `--filename-column`) | Nom du fichier `.wav` de sortie | `"batcrt.wav"` |

Le CSV EdgeTX (`EdgeTX/fr-FR.csv`) contient 6 colonnes :

```
String ID, Source text, Translation, Context, Path, Filename
```

Seules `Translation` et `Filename` sont utilisées par le script (les autres sont ignorées).

---

## 🔊 Conversion audio avec `wavConverter.sh`

Coqui XTTS génère du WAV en **24 kHz**. Certains cibles (EdgeTX) nécessitent du **32 kHz, mono, PCM 16 bits**.

```bash
bash wavConverter.sh \
    --input-folder ./output \
    --output-folder ./converted
```

### Ce que fait le script

| Paramètre | Description |
|-----------|-------------|
| `--input-folder` | Dossier source contenant les fichiers `.wav` à convertir (structure récursive) |
| `output-folder` | Dossier de destination — la structure de sous-dossiers est conservée |

**Conversion appliquée** :
- Fréquence d'échantillonnage → **32 000 Hz**
- Canaux → **mono** (1 canal)
- Format d'échantillon → **PCM signed 16 bits** (`pcm_s16le`)

Le script préserve l'arborescence des sous-dossiers et conserve les noms de fichiers originaux.

---

## 📂 Placement des fichiers avec `place_sounds.py`

Une fois les fichiers générés et convertis, ce script les place dans l'arborescence finale selon le CSV EdgeTX (colonnes `Path` + `Filename`).

```bash
python3 place_sounds.py [source] [csv] [output]
```

### Arguments positionnels (tous optionnels)

| Position | Défaut | Description |
|----------|--------|-------------|
| 1ᵉʳ (`source`) | `./ok` | Dossier contenant les fichiers audio `.wav` |
| 2ᵇᵐ (`csv`) | `./fr-FR.csv` | Fichier CSV EdgeTX (colonnes `Filename`, `Path`) |
| 3ᵉ (`output`) | `./SOUND/fr` | Arborescence de sortie finale |

### Ce que fait le script

- Lit chaque ligne du CSV et copie le fichier `.wav` correspondant vers `<output>/<Path>/<Filename>`
- Si la colonne `Path` est vide, le fichier va directement dans `<output>/`
- Affiche un résumé : fichiers copiés, manquants, overrides, répartition par dossier
- **Idempotent** — relancer ne fait que recopier (les overrides sont signalés)

### Exemple de sortie

```
Source : /home/user/converted
CSV    : /home/user/coqui-tts/EdgeTX/fr-FR.csv
Sortie : /home/user/SOUND/fr

Fichiers copiés : 234/234
Fichiers manquants dans le dossier source : 0
Overrides (déjà en place, recopiés) : 0

Répartition par destination :
  /home/user/SOUND/fr/BETAFLIGHT/ : 15 fichiers
  /home/user/SOUND/fr/INAV/ : 42 fichiers
  ...
```

---

## 🔄 Pipeline complet (EdgeTX)

Voici la séquence complète pour générer un pack vocal EdgeTX :

```bash
# 1. Installation (une seule fois)
bash install_coqui.sh
source ~/tts-env/bin/activate
export COQUI_TOS_AGREED=1

# 2. Génération des WAV depuis le CSV
python3 generate_voices.py \
    --csv EdgeTX/fr-FR.csv \
    --speaker-wav ~/sample/GLaDOS_1h.wav \
    --out-dir ./output \
    --lang fr \
    --text-column "Translation"

# 3. Conversion audio (24kHz → 32kHz, mono, PCM)
bash wavConverter.sh \
    --input-folder ./output \
    --output-folder ./converted

# 4. Placement dans l'arborescence EdgeTX
python3 place_sounds.py ./converted EdgeTX/fr-FR.csv ./SOUND/fr
```

Le dossier `./SOUND/fr` est alors prêt à être copié sur la carte SD de votre radio EdgeTX.

---

## ⚙️ Configuration du modèle XTTS v2

| Paramètre | Valeur par défaut | Recommandation |
|-----------|-------------------|----------------|
| `temperature` | 0.65 | **0.5–0.7** pour la stabilité, **0.7–0.8** pour plus d'expressivité |
| `retries` | 1 | **2–3** si des erreurs aléatoires surviennent |
| Langue | `fr` | Utilisez `--auto-lang` si le CSV contient du texte non traduit |

### Astuces de qualité vocale

- L'échantillon de référence (`--speaker-wav`) doit être **propre** (peu de bruit de fond, pas de musique)
- Un extrait de **30 secondes à 2 minutes** est suffisant pour un bon clonage
- La voix doit parler clairement et être proche du registre souhaité
- XTTS v2 supporte le **clonage zero-shot** : aucun entraînement nécessaire

---

## 📋 Résumé des scripts

| Script | Rôle | Langue | Dépendance |
|--------|------|--------|------------|
| `install_coqui.sh` | Installation complète (Python, venv, PyTorch, Coqui TTS) | Bash | `curl`, `apt` |
| `generate_voices.py` | Génération batch de WAV depuis un CSV avec clonage vocal | Python 3.11+ | Coqui TTS activé |
| `wavConverter.sh` | Conversion audio (fréquence, canaux, format) | Bash | `ffmpeg` |
| `place_sounds.py` | Placement des fichiers dans l'arborescence cible | Python 3.11+ | Aucune |

---

## 📄 Licence du modèle XTTS v2

Le modèle XTTS v2 est sous licence **CPML** (Coqui Public Model License). Définir `COQUI_TOS_AGREED=1` accepte la licence automatiquement au premier chargement. Consultez [coqui-ai/TTS](https://github.com/coqui-ai/TTS) pour plus de détails.

---

## 🛠️ Dépannage

| Problème | Solution |
|----------|----------|
| `torchcodec` error au chargement du modèle | Le script pin PyTorch < 2.9 automatiquement. Vérifiez que vous avez bien relancé `install_coqui.sh` |
| Prononciation incorrecte de chiffres | Ajoutez `--normalize-digits` |
| Ligne prononcée en anglais dans un CSV français | Utilisez `--auto-lang` |
| Échec aléatoire d'un fichier WAV | Augmentez `--retries 3` ou baissez `--temperature 0.5` |
| Modèle lent à charger au premier lancement | C'est normal : ~2 Go téléchargés + chargement CPU. Patientez 1–2 min |
