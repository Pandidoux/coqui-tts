#!/usr/bin/env bash
# Installation de Coqui TTS (fork maintenu idiap/coqui-ai-TTS) en mode CPU
# Testé pour Ubuntu 18.04 avec Python système 3.6.9 (on n'utilise PAS ce Python)
set -euo pipefail

echo "== 1/6 : dépendances système =="
sudo apt-get update
sudo apt-get install -y ffmpeg libsndfile1 build-essential curl espeak-ng

echo "== 2/6 : installation de uv (gestionnaire Python/paquets, remplace pip+pyenv) =="
if ! command -v uv &> /dev/null; then
    curl -LsSf https://astral.sh/uv/install.sh | sh
    source "$HOME/.local/bin/env" 2>/dev/null || export PATH="$HOME/.local/bin:$PATH"
fi
uv --version

echo "== 3/6 : installation d'un Python 3.11 isolé (indépendant du Python système 3.6.9) =="
uv python install 3.11

echo "== 4/6 : création de l'environnement virtuel =="
mkdir -p "$HOME/tts-env"
uv venv --python 3.11 "$HOME/tts-env"
source "$HOME/tts-env/bin/activate"

echo "== 5/6 : installation de PyTorch (CPU only, pas de CUDA) puis coqui-tts =="
# Pin torch < 2.9 : evite la dependance a torchcodec (instable, erreurs de
# chargement de libs FFmpeg constatees sur plusieurs distros). soundfile
# suffit pour l'IO audio sur ces versions de torch.
uv pip install "torch==2.8.*" "torchaudio==2.8.*" --index-url https://download.pytorch.org/whl/cpu
uv pip install coqui-tts "transformers>=4.57,<5"

echo "== 6/6 : téléchargement + validation du modèle XTTS v2 (clonage de voix multilingue) =="
# Le modèle est sous licence CPML (non-commercial) : COQUI_TOS_AGREED=1 permet
# d'accepter automatiquement le prompt de licence lors du premier chargement.
export COQUI_TOS_AGREED=1
python3 - <<'PYEOF'
from TTS.api import TTS
print("Chargement du modèle XTTS v2 (peut prendre plusieurs minutes au premier lancement, ~2GB à télécharger)...")
tts = TTS("tts_models/multilingual/multi-dataset/xtts_v2", progress_bar=True).to("cpu")
print("Modèle chargé avec succès. Langues supportées :", tts.languages if hasattr(tts, "languages") else "n/a")
PYEOF

echo ""
echo "=================================================="
echo "Installation terminée."
echo "Pour l'utiliser plus tard : source ~/tts-env/bin/activate"
echo "=================================================="
