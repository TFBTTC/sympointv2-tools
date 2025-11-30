#!/usr/bin/env python
"""
run_inference.py - Inférence SymPointV2 avec patch knnquery
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
    1: "Single Door", 2: "Double Door", 3: "Sliding Door",
    4: "Folding Door", 5: "Revolving Door", 6: "Rolling Door",
    7: "Window", 8: "Bay Window", 9: "Blind Window", 10: "Opening Symbol",
    11: "Sofa", 12: "Bed", 13: "Chair", 14: "Table", 15: "TV Cabinet",
    16: "Gas Stove", 17: "Sink", 18: "Refrigerator", 19: "AirCon",
    20: "Bath", 21: "Bathtub", 22: "Washing Machine", 23: "Squat Toilet", 24: "Urinal",
    25: "Toilet", 26: "Stairs", 27: "Elevator",
    28: "Escalator", 29: "Row Chairs", 30: "Parking Spot",
    31: "Wall", 32: "Curtain Wall", 33: "Railing",
    34: "Fence", 35: "Background"
}


def load_model_weights_custom(model, checkpoint_path):
    print(f"📦 Chargement: {checkpoint_path}")
    state_dict = torch.load(checkpoint_path, map_location='cpu')
    
    src = state_dict.get('net', state_dict)
    epoch = state_dict.get('epoch', '?')
    print(f"   Epoch: {epoch}")
    
    model_dict = model.state_dict()
    filtered = {k: v for k, v in src.items() if k in model_dict and v.shape == model_dict[k].shape}
    model.load_state_dict(filtered, strict=False)
    print(f"   ✅ Chargé: {len(filtered)}/{len(src)} paramètres")
    return model


def run_inference(json_path, config_path, checkpoint_path):
    print(f"\n{'='*60}")
    print(f"INFÉRENCE SYMPOINTV2")
    print(f"{'='*60}")
    print(f"Fichier: {json_path}")
    
    cfg = Munch.fromDict(yaml.safe_load(open(config_path)))
    
    print("\n📦 Construction du modèle...")
    model = svgnet(cfg.model).cuda()
    model = load_model_weights_custom(model, checkpoint_path)
    model.eval()
    print("✅ Modèle prêt")
    
    print("\n📄 Chargement des données...")
    coords, feats, labels, lengths, layerIds = SVGDataset.load(json_path, idx=0)
    
    print(f"   Primitives: {len(coords)}")
    print(f"   Features: {feats.shape}")
    print(f"   Layers: {len(np.unique(layerIds))}")
    
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
    
    semantic_labels = result['semantic_labels'].cpu().numpy()
    instances = result['instances']
    
    print(f"\n{'='*60}")
    print(f"📊 RÉSULTATS")
    print(f"{'='*60}")
    
    unique, counts = np.unique(semantic_labels, return_counts=True)
    print(f"\n🏷️ Classes détectées:")
    for c, cnt in sorted(zip(unique, counts), key=lambda x: -x[1]):
        print(f"   {CLASSES.get(int(c), f'Class {c}'):20s}: {cnt:6d} ({100*cnt/len(semantic_labels):.1f}%)")
    
    print(f"\n🎯 Instances: {len(instances)}")
    if instances:
        print(f"\n   Top 10:")
        for i, inst in enumerate(sorted(instances, key=lambda x: -x['conf'])[:10]):
            cls = CLASSES.get(inst['label_id'], '?')
            print(f"   {i+1:2d}. {cls:20s} conf={inst['conf']:.3f} pts={int(inst['pred_mask'].sum())}")
    
    return {
        'source_file': os.path.basename(json_path),
        'num_primitives': len(semantic_labels),
        'semantic_labels': semantic_labels.tolist(),
        'class_distribution': {CLASSES.get(int(c), f"Class {c}"): int(cnt) for c, cnt in zip(unique, counts)},
        'num_instances': len(instances),
        'instances': [
            {'class': CLASSES.get(inst['label_id'], '?'), 'label_id': int(inst['label_id']),
             'confidence': float(inst['conf']), 'num_points': int(inst['pred_mask'].sum())}
            for inst in instances
        ]
    }


def main():
    if len(sys.argv) < 2:
        print("Usage: python run_inference.py <fichier_s2.json> [output.json]")
        sys.exit(1)
    
    json_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else json_path.replace('_s2.json', '_pred.json')
    
    config_path = '/workspace/SymPointV2/checkpoints/sympointv2/svg_pointT.yaml'
    checkpoint_path = '/workspace/SymPointV2/checkpoints/sympointv2/best.pth'
    
    if not os.path.exists(config_path):
        print(f"❌ Config non trouvée: {config_path}")
        sys.exit(1)
    if not os.path.exists(checkpoint_path):
        print(f"❌ Checkpoint non trouvé: {checkpoint_path}")
        sys.exit(1)
    
    result = run_inference(json_path, config_path, checkpoint_path)
    
    with open(output_path, 'w') as f:
        json.dump(result, f, indent=2)
    
    print(f"\n✅ Résultats sauvegardés: {output_path}")


if __name__ == '__main__':
    main()
