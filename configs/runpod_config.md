# Configuration RunPod pour SymPointV2

## 🚀 Template Personnalisé (Recommandé)

| Paramètre | Valeur |
|-----------|--------|
| **Template** | `sympoint-v2-dev` |
| **GPU** | RTX 4000 Ada (20GB VRAM) - ~0.26$/h |
| **Volume Disk** | 50 GB |
| **Volume Mount Path** | `/workspace` |

L'image custom `sympoint-v2-dev` inclut déjà :
- SymPointV2 installé
- Checkpoint téléchargé
- pointops compilé
- sympointv2-tools cloné
- Toutes les dépendances

## Variables d'Environnement

```
JUPYTER_PASSWORD=a
PUBLIC_KEY=ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDYegPrtRxOmcaIy3dBLMOw5INs1XF60aCQM6EsCRWD7 pierreantoine.bq@gmail.com
```

## Clé SSH

```
ssh-ed25519 AAAAC3NzaC1lZDI1NTE5AAAAIDYegPrtRxOmcaIy3dBLMOw5INs1XF60aCQM6EsCRWD7 pierreantoine.bq@gmail.com
```

## Connexion SSH

Après démarrage du pod :
1. Récupérer l'IP publique et le port SSH depuis la console RunPod
2. Connexion : `ssh -p <PORT> root@<IP>`

## Premier Usage

```bash
cd /workspace

# Mettre à jour les scripts depuis GitHub (si modifiés)
cd sympointv2-tools && git pull && cd ..

# Workflow standard
python smart_pdf_parser_v2.py test_pdfs/plan.pdf
python run_inference.py test_pdfs/plan_s2.json
```

## Avant de Fermer le Pod

**IMPORTANT** : Sauvegarder les modifications !

```bash
cd /workspace
./sync_to_github.sh "Description des modifications"
```

---

## 📦 Alternative : Image de Base

Si le template custom n'est pas disponible, utiliser :

| Paramètre | Valeur |
|-----------|--------|
| **Container Image** | `pytorch/pytorch:1.10.0-cuda11.3-cudnn8-devel` |
| **Container Disk** | 20 GB |
| **Volume Disk** | 50 GB |
| **Volume Mount Path** | `/workspace` |
| **HTTP Ports** | 8888 |

Avec le Container Start Command suivant :

```bash
bash -c "cd /workspace && \
apt-key adv --fetch-keys https://developer.download.nvidia.com/compute/cuda/repos/ubuntu1804/x86_64/3bf863cc.pub 2>/dev/null && \
apt-get update && \
apt-get install -y git libgl1-mesa-glx libglib2.0-0 openssh-server && \
mkdir -p ~/.ssh && \
echo \"\$PUBLIC_KEY\" >> ~/.ssh/authorized_keys && \
chmod 600 ~/.ssh/authorized_keys && \
service ssh start && \
pip install gdown && \
if [ ! -d 'SymPointV2' ]; then \
  git clone https://github.com/nicehuster/SymPointV2.git && \
  cd SymPointV2 && \
  pip install mmcv==0.2.14 svgpathtools==1.6.1 munch==2.5.0 tensorboard==2.10.0 tensorboardx==2.5.1 pymupdf scipy scikit-learn && \
  pip install detectron2 -f https://dl.fbaipublicfiles.com/detectron2/wheels/cu113/torch1.10/index.html && \
  mkdir -p checkpoints/sympointv2 && \
  cd checkpoints/sympointv2 && \
  gdown 1LczVNXapght3S65gx0ZOhQ3UqkBg4hJ7 -O best.pth && \
  gdown 1c0_al7p72D7eTOHgBP_kxU1H1Ia-ZakV -O svg_pointT.yaml && \
  cd /workspace/SymPointV2/modules/pointops && \
  python setup.py install && \
  cd /workspace; \
fi && \
if [ ! -d 'sympointv2-tools' ]; then \
  git clone https://github.com/TFBTTC/sympointv2-tools.git && \
  cd sympointv2-tools && chmod +x *.sh && cd /workspace && \
  ln -sf sympointv2-tools/scripts/smart_pdf_parser_v2.py . && \
  ln -sf sympointv2-tools/scripts/run_inference.py . && \
  ln -sf sympointv2-tools/scripts/analyze_pdf_ocg.py . && \
  ln -sf sympointv2-tools/sync_to_github.sh .; \
fi && \
mkdir -p test_pdfs && \
export LD_LIBRARY_PATH=/opt/conda/lib/python3.7/site-packages/torch/lib:\$LD_LIBRARY_PATH && \
echo 'export LD_LIBRARY_PATH=/opt/conda/lib/python3.7/site-packages/torch/lib:\$LD_LIBRARY_PATH' >> ~/.bashrc && \
pip install jupyterlab ipykernel && \
python -m ipykernel install --user --name python3 --display-name 'Python 3' && \
jupyter lab --ip=0.0.0.0 --port=8888 --no-browser --allow-root --NotebookApp.token='' --NotebookApp.password=''"
```
