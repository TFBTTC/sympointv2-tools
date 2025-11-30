# 🤖 Guide pour Claude - SymPointV2

## Quand l'utilisateur dit "On lance un pod pour SymPointV2"

### Étape 1 : Créer le Pod

Utiliser le MCP RunPod :
```
runpod:create-pod
  - imageName: pytorch/pytorch:1.10.0-cuda11.3-cudnn8-devel
  - gpuTypeIds: ["NVIDIA RTX 4000 Ada Generation"]
  - volumeInGb: 50
  - volumeMountPath: /workspace
  - containerDiskInGb: 20
  - ports: ["8888/http", "22/tcp"]
  - env: voir configs/runpod_config.md
```

### Étape 2 : Attendre le pod RUNNING

```
runpod:get-pod podId=<ID>
```
Attendre `runtime` non null.

### Étape 3 : Se connecter SSH

```
ssh:remote-ssh
  - host: <IP publique>
  - port: <port SSH>
  - user: root
```

### Étape 4 : Vérifier l'installation

```bash
cd /workspace
python -c "from modules.pointops.functions import pointops; print('OK')"
ls -la smart_pdf_parser_v2.py run_inference.py
```

## Workflow Standard

```bash
# Parser un PDF
python smart_pdf_parser_v2.py test_pdfs/plan.pdf

# Inférence
python run_inference.py test_pdfs/plan_s2.json

# Voir résultats
cat test_pdfs/plan_pred.json
```

## Avant Fermeture du Pod

**CRITIQUE** : Sauvegarder les modifications !

```bash
./sync_to_github.sh "Description"
```

## Problèmes Connus

1. **Bug knnquery** → Patch intégré dans run_inference.py
2. **Checkpoint loading** → Utilise load_model_weights_custom()
3. **LD_LIBRARY_PATH** → export dans start command

## Liens Importants

- Repo: https://github.com/TFBTTC/sympointv2-tools
- Checkpoint: https://drive.google.com/file/d/1LczVNXapght3S65gx0ZOhQ3UqkBg4hJ7/view
- Config: https://drive.google.com/file/d/1c0_al7p72D7eTOHgBP_kxU1H1Ia-ZakV/view
