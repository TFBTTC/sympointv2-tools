# 🤖 Guide pour Claude - SymPointV2

## Quand l'utilisateur dit "Lance un pod SymPointV2"

### ⚠️ IMPORTANT : Limitation API

L'API MCP RunPod ne permet pas de créer un pod avec un template custom qui inclut un Start Command. 

**Réponse à donner :**
> Lance le pod manuellement depuis l'interface RunPod avec le template `sympoint-v2-dev`, dis-moi quand c'est prêt et je me connecte en SSH.

### Après que l'utilisateur dit "c'est prêt" / "c'est bon"

1. Récupérer les infos du pod :
```
runpod:list-pods
```

2. Se connecter en SSH :
```
ssh:remote-ssh
  - host: <IP publique>
  - port: <port SSH (souvent 22xxx)>
  - user: root
```

3. Vérifier l'installation :
```bash
cd /workspace
ls -la smart_pdf_parser_v2.py run_inference.py
python -c "from modules.pointops.functions import pointops; print('OK')"
```

## Workflow Standard

```bash
cd /workspace

# Mettre à jour les scripts (si modifiés sur GitHub)
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

Puis fermer :
```
runpod:stop-pod podId=<ID>
```

## Problèmes Connus

| Problème | Solution |
|----------|----------|
| Bug knnquery indices invalides | Patch intégré dans `run_inference.py` |
| Checkpoint PyTorch incompatible | `load_model_weights_custom()` dans le script |
| `libc10.so` non trouvé | `export LD_LIBRARY_PATH=/opt/conda/lib/python3.7/site-packages/torch/lib:$LD_LIBRARY_PATH` |

## Liens Importants

- **Repo GitHub** : https://github.com/TFBTTC/sympointv2-tools
- **Checkpoint best.pth** : https://drive.google.com/file/d/1LczVNXapght3S65gx0ZOhQ3UqkBg4hJ7/view
- **Config svg_pointT.yaml** : https://drive.google.com/file/d/1c0_al7p72D7eTOHgBP_kxU1H1Ia-ZakV/view

## Ce que l'API MCP RunPod PEUT faire

✅ `runpod:list-pods` - Lister les pods
✅ `runpod:get-pod` - Statut d'un pod
✅ `runpod:stop-pod` - Arrêter un pod
✅ `runpod:start-pod` - Redémarrer un pod arrêté
✅ `runpod:delete-pod` - Supprimer un pod
✅ `runpod:list-templates` - Lister les templates

## Ce que l'API MCP RunPod NE PEUT PAS faire

❌ Créer un pod à partir d'un template avec Start Command custom
❌ Récupérer le Start Command d'un template
