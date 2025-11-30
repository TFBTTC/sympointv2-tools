# 🤖 Guide pour Claude - SymPointV2

## Quand l'utilisateur dit "Lance un pod SymPointV2"

### Méthode 1 : Template Custom (Recommandé)

Chercher le template `sympoint-v2-dev` dans les templates RunPod de l'utilisateur.

```
runpod:list-templates
```

Puis créer le pod avec ce template.

### Méthode 2 : Image de base

Si le template n'existe pas :
```
runpod:create-pod
  - imageName: pytorch/pytorch:1.10.0-cuda11.3-cudnn8-devel
  - gpuTypeIds: ["NVIDIA RTX 4000 Ada Generation"]
  - volumeInGb: 50
  - volumeMountPath: /workspace
  - containerDiskInGb: 20
  - ports: ["8888/http", "22/tcp"]
```

### Étapes après création

1. Attendre le pod RUNNING : `runpod:get-pod podId=<ID>`
2. Se connecter SSH : `ssh:remote-ssh host=<IP> port=<PORT> user=root`
3. Vérifier : `python -c "from modules.pointops.functions import pointops; print('OK')"`

## Workflow Standard

```bash
cd /workspace

# Mettre à jour les scripts
cd sympointv2-tools && git pull && cd ..

# Parser un PDF
python smart_pdf_parser_v2.py test_pdfs/plan.pdf

# Inférence
python run_inference.py test_pdfs/plan_s2.json
```

## ⚠️ AVANT FERMETURE DU POD

**TOUJOURS** demander à l'utilisateur s'il veut sauvegarder les modifications :

```bash
./sync_to_github.sh "Description"
```

## Problèmes Connus

1. **Bug knnquery** → Patch intégré dans run_inference.py
2. **Checkpoint loading** → Utilise load_model_weights_custom()
3. **LD_LIBRARY_PATH** → `export LD_LIBRARY_PATH=/opt/conda/lib/python3.7/site-packages/torch/lib:$LD_LIBRARY_PATH`

## Liens

- Repo: https://github.com/TFBTTC/sympointv2-tools
- Checkpoint: https://drive.google.com/file/d/1LczVNXapght3S65gx0ZOhQ3UqkBg4hJ7/view
- Config: https://drive.google.com/file/d/1c0_al7p72D7eTOHgBP_kxU1H1Ia-ZakV/view
