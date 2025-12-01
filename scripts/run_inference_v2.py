#!/usr/bin/env python
"""
run_inference_v2.py - Inférence SymPointV2 avec post-traitement pour murs

Amélioration: Remappe Railing/Fence → Wall pour le layer 0 (traits épais)
Nécessite un fichier JSON généré par smart_pdf_parser_v5.py
"""

import os
import sys
import json
import numpy as np
import torch
import yaml
from munch import Munch

sys.path.insert(0, '/workspace/SymPointV2')

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


def remap_walls(predictions, layerIds, num_preds):
    """
    Post-traitement: Remappe Railing/Fence → Wall pour layer 0 (murs épais).
    """
    if len(layerIds) < num_preds:
        padded = np.full(num_preds, layerIds[-1] if len(layerIds) > 0 else 0)
        padded[:len(layerIds)] = layerIds
        layerIds = padded
    else:
        layerIds = layerIds[:num_preds]
    
    wall_layer = (layerIds == 0)
    railing_or_fence = np.isin(predictions, [32, 33])
    to_remap = wall_layer & railing_or_fence
    
    predictions_fixed = predictions.copy()
    predictions_fixed[to_remap] = 30  # Wall
    
    return predictions_fixed, to_remap.sum()


def run_inference(json_path, config_path, checkpoint_path):
    print(f"\n{'='*60}")
    print(f"INFÉRENCE SYMPOINTV2 v2 (avec remapping murs)")
    print(f"{'='*60}")
    print(f"Fichier: {json_path}")
    
    with open(json_path) as f:
        source_data = json.load(f)
    layerIds = np.array(source_data.get('layerIds', []))
    
    cfg = Munch.fromDict(yaml.safe_load(open(config_path)))
    
    print("\n📦 Construction du modèle...")
    model = svgnet(cfg.model).cuda()
    state = torch.load(checkpoint_path, map_location='cpu')
    model.load_state_dict({k: v for k, v in state['net'].items() 
                          if k in model.state_dict()}, strict=False)
    model.eval()
    print("✅ Modèle prêt")
    
    print("\n📄 Chargement des données...")
    coords, feats, labels, lengths, layerIds_loaded = SVGDataset.load(json_path, idx=0)
    print(f"   Primitives: {len(coords)} (padded à 2048)")
    
    coords = coords - np.mean(coords, axis=0)
    
    offset = torch.IntTensor([coords.shape[0]])
    batch = (
        torch.FloatTensor(coords).cuda(),
        torch.FloatTensor(feats).cuda(),
        torch.LongTensor(labels).cuda(),
        offset.cuda(),
        torch.FloatTensor(lengths).cuda(),
        torch.LongTensor(layerIds_loaded).cuda()
    )
    
    print("\n🔮 Inférence en cours...")
    with torch.no_grad():
        result = model(batch, return_loss=False)
    print("✅ Inférence terminée")
    
    sem_scores = result['semantic_scores']
    sem_preds_raw = torch.argmax(sem_scores, dim=1).cpu().numpy()
    instances = result['instances']
    
    print("\n🔧 Post-traitement (remapping murs)...")
    sem_preds, n_remapped = remap_walls(sem_preds_raw, layerIds, len(sem_preds_raw))
    print(f"   Remappé {n_remapped} primitives Railing/Fence → Wall")
    
    print(f"\n{'='*60}")
    print(f"📊 RÉSULTATS")
    print(f"{'='*60}")
    
    unique, counts = np.unique(sem_preds, return_counts=True)
    print(f"\n🏷️ Classes prédites (après remapping):")
    for cls_id, cnt in sorted(zip(unique, counts), key=lambda x: -x[1]):
        cls_name = CLASSES.get(cls_id, f"Class {cls_id}")
        print(f"   {cls_name:20s}: {cnt:5d} ({100*cnt/len(sem_preds):5.1f}%)")
    
    print(f"\n🎯 Instances détectées: {len(instances)}")
    
    output_path = json_path.replace('_s2.json', '_pred.json')
    output = {
        'source_file': os.path.basename(json_path),
        'num_primitives': len(sem_preds),
        'predictions': sem_preds.tolist(),
        'predictions_raw': sem_preds_raw.tolist(),
        'class_distribution': {
            CLASSES.get(int(c), f"Class {c}"): int(cnt) 
            for c, cnt in zip(unique, counts)
        },
        'num_instances': len(instances),
        'wall_remapping': {
            'enabled': True,
            'remapped_count': int(n_remapped)
        }
    }
    
    with open(output_path, 'w') as f:
        json.dump(output, f, indent=2)
    print(f"\n💾 Résultats sauvegardés: {output_path}")
    
    return output


def main():
    import argparse
    parser = argparse.ArgumentParser(description='SymPointV2 Inference v2')
    parser.add_argument('json_file', help='Fichier JSON _s2.json (généré par parser v5)')
    parser.add_argument('--config', default='/workspace/SymPointV2/checkpoints/sympointv2/svg_pointT.yaml')
    parser.add_argument('--checkpoint', default='/workspace/SymPointV2/checkpoints/sympointv2/best.pth')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.json_file):
        print(f"❌ Fichier non trouvé: {args.json_file}")
        sys.exit(1)
    
    run_inference(args.json_file, args.config, args.checkpoint)


if __name__ == '__main__':
    main()
