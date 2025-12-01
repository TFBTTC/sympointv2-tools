#!/usr/bin/env python
"""
run_inference.py - Inférence SymPointV2 avec patch knnquery

CORRECTION IMPORTANTE: utiliser argmax(semantic_scores) pour les prédictions,
PAS semantic_labels qui contient les ground truth du fichier d'entrée.
"""

import os
import sys
import json
import numpy as np
import torch
import yaml
from munch import Munch

sys.path.insert(0, '/workspace/SymPointV2')

# PATCH CRITIQUE - Corriger le bug pointops knnquery
def apply_pointops_patch():
    import modules.pointops.functions.pointops as pointops_module
    
    def _patched_interpolation(xyz, new_xyz, feat, offset, new_offset, k=3):
        from modules.pointops.functions import pointops
        idx, dist = pointops.knnquery(k, xyz, new_xyz, offset, new_offset)
        dist_recip = 1.0 / (dist + 1e-8)
        norm = torch.sum(dist_recip, dim=1, keepdim=True)
        weight = dist_recip / norm
        new_feat = torch.cuda.FloatTensor(new_xyz.shape[0], feat.shape[1]).zero_()
        for i in range(k):
            valid_idx = torch.clamp(idx[:, i].long(), 0, feat.shape[0] - 1)
            new_feat += feat[valid_idx, :] * weight[:, i].unsqueeze(-1)
        return new_feat
    
    pointops_module.interpolation = _patched_interpolation
    print("✅ Patch pointops appliqué")

apply_pointops_patch()

from svgnet.model.svgnet import SVGNet as svgnet
from svgnet.data.svg3 import SVGDataset

CLASSES = {
    0: "Single Door", 1: "Double Door", 2: "Sliding Door",
    3: "Folding Door", 4: "Revolving Door", 5: "Rolling Door",
    6: "Window", 7: "Bay Window", 8: "Blind Window", 9: "Opening Symbol",
    10: "Sofa", 11: "Bed", 12: "Chair", 13: "Table", 14: "TV Cabinet",
    15: "Gas Stove", 16: "Sink", 17: "Refrigerator", 18: "AirCon",
    19: "Bath", 20: "Bathtub", 21: "Washing Machine", 22: "Squat Toilet",
    23: "Urinal", 24: "Toilet", 25: "Stairs", 26: "Elevator",
    27: "Escalator", 28: "Row Chairs", 29: "Parking Spot",
    30: "Wall", 31: "Curtain Wall", 32: "Railing", 33: "Fence", 34: "Background"
}


def run_inference(json_path, config_path, checkpoint_path):
    print(f"\n{'='*60}")
    print(f"INFÉRENCE SYMPOINTV2")
    print(f"{'='*60}")
    print(f"Fichier: {json_path}")
    
    cfg = Munch.fromDict(yaml.safe_load(open(config_path)))
    
    print("\n📦 Construction du modèle...")
    model = svgnet(cfg.model).cuda()
    
    state = torch.load(checkpoint_path, map_location='cpu')
    model.load_state_dict({k: v for k, v in state['net'].items() 
                          if k in model.state_dict()}, strict=False)
    model.eval()
    print("✅ Modèle prêt")
    
    print("\n📄 Chargement des données...")
    coords, feats, labels, lengths, layerIds = SVGDataset.load(json_path, idx=0)
    print(f"   Primitives: {len(coords)}")
    
    coords = coords - np.mean(coords, axis=0)
    
    offset = torch.IntTensor([coords.shape[0]])
    batch = (
        torch.FloatTensor(coords).cuda(),
        torch.FloatTensor(feats).cuda(),
        torch.LongTensor(labels).cuda(),
        offset.cuda(),
        torch.FloatTensor(lengths).cuda(),
        torch.LongTensor(layerIds).cuda()
    )
    
    print("\n🔮 Inférence en cours...")
    with torch.no_grad():
        result = model(batch, return_loss=False)
    print("✅ Inférence terminée")
    
    # CORRECT: utiliser argmax sur semantic_scores pour les PRÉDICTIONS
    sem_scores = result['semantic_scores']
    sem_preds = torch.argmax(sem_scores, dim=1).cpu().numpy()
    instances = result['instances']
    
    print(f"\n{'='*60}")
    print(f"📊 RÉSULTATS")
    print(f"{'='*60}")
    
    # Distribution des classes prédites
    unique, counts = np.unique(sem_preds, return_counts=True)
    print(f"\n🏷️ Classes prédites:")
    for cls_id, cnt in sorted(zip(unique, counts), key=lambda x: -x[1]):
        cls_name = CLASSES.get(cls_id, f"Class {cls_id}")
        print(f"   {cls_name:20s}: {cnt:5d} ({100*cnt/len(sem_preds):5.1f}%)")
    
    print(f"\n🎯 Instances détectées: {len(instances)}")
    
    # Sauvegarder les résultats
    output_path = json_path.replace('_s2.json', '_pred.json')
    output = {
        'source_file': os.path.basename(json_path),
        'num_primitives': len(sem_preds),
        'predictions': sem_preds.tolist(),
        'class_distribution': {
            CLASSES.get(int(c), f"Class {c}"): int(cnt) 
            for c, cnt in zip(unique, counts)
        },
        'num_instances': len(instances)
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n💾 Résultats sauvegardés: {output_path}")
    
    return output


def main():
    import argparse
    parser = argparse.ArgumentParser(description='SymPointV2 Inference')
    parser.add_argument('json_file', help='Fichier JSON _s2.json')
    parser.add_argument('--config', default='/workspace/SymPointV2/checkpoints/sympointv2/svg_pointT.yaml')
    parser.add_argument('--checkpoint', default='/workspace/SymPointV2/checkpoints/sympointv2/best.pth')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.json_file):
        print(f"❌ Fichier non trouvé: {args.json_file}")
        sys.exit(1)
    
    run_inference(args.json_file, args.config, args.checkpoint)


if __name__ == '__main__':
    main()
