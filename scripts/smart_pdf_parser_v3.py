#!/usr/bin/env python
"""
smart_pdf_parser_v3.py - Parser PDF optimisé pour SymPointV2

=== CORRECTIONS CRITIQUES (Session debugging 2024-12) ===

PROBLÈMES IDENTIFIÉS:
1. Format args incorrect: utilisait [[x1,y1],...] au lieu de [x1,y1,x2,y2,...]
2. Dimensions trop grandes: 1190x841 vs FloorPlanCAD 140x140
3. Trop de micro-primitives: 78% < 0.1 unité (textes, détails)
4. widths variables: devrait être uniforme (0.1)
5. instanceIds=0: devrait être -1

SOLUTIONS APPLIQUÉES:
1. Format args en liste plate [x1,y1,x2,y2,x3,y3,x4,y4]
2. Rescaling vers ~140x140 (comme FloorPlanCAD)
3. Filtrage des primitives trop courtes (length >= MIN_LENGTH après rescale)
4. Widths uniformes = 0.1
5. instanceIds = -1
6. Ajout champ rgb = [[0,0,0], ...]

STATISTIQUES CIBLES (FloorPlanCAD):
- Dimensions: ~140x140
- Primitives: ~900-2000
- Lengths mean: ~5.4, median: ~2.1
- Distribution: 55% dans [1-5], 22% dans [0.1-1]

Usage:
    python smart_pdf_parser_v3.py input.pdf [output.json] [--mode ocg|visible|all]
    python smart_pdf_parser_v3.py input.pdf --min-length 1.0  # Filtrage plus strict
"""

import fitz
import json
import sys
import os
import argparse
import numpy as np
from collections import defaultdict

# ============================================================================
# PARAMÈTRES OPTIMISÉS POUR FLOORPLANCAD
# ============================================================================
TARGET_SIZE = 140        # Taille cible (FloorPlanCAD ~140x140)
MIN_LENGTH = 0.5         # Longueur min après rescaling
UNIFORM_WIDTH = 0.1      # Épaisseur uniforme
MAX_PRIMITIVES = 50000   # Limite de sécurité


def get_ocg_layers(doc):
    """Récupère les layers OCG avec leurs états."""
    try:
        oc_config = doc.get_oc_items()
        if not oc_config:
            return {}
        layers = {}
        for xref, name, state in oc_config:
            layers[xref] = {'name': name, 'visible': state == 1, 'xref': xref}
        return layers
    except Exception as e:
        print(f"   ⚠️ Erreur OCG: {e}")
        return {}


def should_exclude_layer(layer_name):
    """
    Détermine si un layer doit être exclu.
    Exclut: texte, annotations, côtes, légendes, cartouches.
    """
    if not layer_name:
        return False
    
    name_lower = layer_name.lower()
    exclude_patterns = [
        'text', 'texte', 'annotation', 'annot',
        'cote', 'dimension', 'dim', 'mesure',
        'legende', 'legend', 'légende',
        'cartouche', 'title', 'titre',
        'hatch', 'hachure', 'fill',
        'grid', 'grille', 'axe',
    ]
    
    return any(pattern in name_lower for pattern in exclude_patterns)


def calculate_length(points_flat):
    """Calcule la longueur d'une primitive (somme des segments)."""
    pts = np.array(points_flat).reshape(4, 2)
    length = sum(np.linalg.norm(pts[i+1] - pts[i]) for i in range(3))
    return float(length)


def parse_primitives_from_page(page):
    """
    Extrait les primitives vectorielles d'une page PDF.
    Retourne: List of (cmd, points_flat_8, layer_id, stroke_width)
    """
    primitives = []
    drawings = page.get_drawings()
    
    for path_idx, path in enumerate(drawings):
        stroke_width = path.get('width', 1.0) or 1.0
        layer_id = path_idx
        
        for item in path['items']:
            cmd_type = item[0]
            
            if cmd_type == 'l':  # Ligne
                p1, p2 = item[1], item[2]
                points = [
                    p1.x, p1.y,
                    p1.x + (p2.x - p1.x) * 0.33, p1.y + (p2.y - p1.y) * 0.33,
                    p1.x + (p2.x - p1.x) * 0.66, p1.y + (p2.y - p1.y) * 0.66,
                    p2.x, p2.y
                ]
                primitives.append((0, points, layer_id, stroke_width))
                
            elif cmd_type == 'c':  # Courbe Bézier
                if len(item) >= 5:
                    points = []
                    for p in item[1:5]:
                        points.extend([p.x, p.y])
                    if len(points) == 8:
                        primitives.append((1, points, layer_id, stroke_width))
                        
            elif cmd_type == 're':  # Rectangle -> 4 lignes
                rect = item[1]
                corners = [
                    (rect.x0, rect.y0), (rect.x1, rect.y0),
                    (rect.x1, rect.y1), (rect.x0, rect.y1)
                ]
                for i in range(4):
                    p1, p2 = corners[i], corners[(i + 1) % 4]
                    points = [
                        p1[0], p1[1],
                        p1[0] + (p2[0] - p1[0]) * 0.33, p1[1] + (p2[1] - p1[1]) * 0.33,
                        p1[0] + (p2[0] - p1[0]) * 0.66, p1[1] + (p2[1] - p1[1]) * 0.66,
                        p2[0], p2[1]
                    ]
                    primitives.append((0, points, layer_id, stroke_width))
    
    return primitives


def parse_pdf(pdf_path, output_path=None, mode='ocg', min_length=MIN_LENGTH, target_size=TARGET_SIZE):
    """
    Convertit un PDF en format SymPointV2 optimisé.
    """
    print(f"📄 Ouverture: {pdf_path}")
    doc = fitz.open(pdf_path)
    
    ocg_layers = get_ocg_layers(doc) if mode == 'ocg' else {}
    if ocg_layers:
        print(f"   {len(ocg_layers)} layers OCG trouvés")
        for xref, info in list(ocg_layers.items())[:5]:
            status = "✓" if info['visible'] else "✗"
            print(f"     [{status}] {info['name']}")
    
    # Extraire primitives
    all_primitives = []
    width, height = 0, 0
    
    for page in doc:
        rect = page.rect
        width = max(width, rect.width)
        height = max(height, rect.height)
        all_primitives.extend(parse_primitives_from_page(page))
        if len(all_primitives) >= MAX_PRIMITIVES:
            break
    
    doc.close()
    
    print(f"   Dimensions originales: {width:.0f} x {height:.0f}")
    print(f"   Primitives extraites: {len(all_primitives)}")
    
    if not all_primitives:
        print("⚠️ Aucune primitive trouvée!")
        return None
    
    # Rescaling
    scale = target_size / max(width, height)
    new_width = int(width * scale)
    new_height = int(height * scale)
    print(f"   Rescaling vers: {new_width} x {new_height} (facteur: {scale:.4f})")
    
    # Appliquer rescaling et filtrage
    commands, args, lengths, layerIds = [], [], [], []
    
    for cmd, points, layer_id, _ in all_primitives:
        scaled_points = [p * scale for p in points]
        length = calculate_length(scaled_points)
        
        if length >= min_length:
            commands.append(cmd)
            args.append(scaled_points)
            lengths.append(length)
            layerIds.append(layer_id)
    
    print(f"   Après filtrage (length >= {min_length}): {len(commands)} primitives")
    
    if not commands:
        print("⚠️ Toutes les primitives filtrées!")
        return None
    
    # Statistiques
    lengths_arr = np.array(lengths)
    print(f"   Lengths: min={lengths_arr.min():.2f}, max={lengths_arr.max():.2f}, "
          f"mean={lengths_arr.mean():.2f}, median={np.median(lengths_arr):.2f}")
    
    # Construire JSON final
    n = len(commands)
    result = {
        "width": new_width,
        "height": new_height,
        "commands": commands,
        "args": args,  # Liste plate [x1,y1,x2,y2,x3,y3,x4,y4]
        "lengths": lengths,
        "layerIds": layerIds,
        "widths": [UNIFORM_WIDTH] * n,
        "semanticIds": [35] * n,  # 35 = Background
        "instanceIds": [-1] * n,  # -1 = pas d'instance
        "rgb": [[0, 0, 0]] * n
    }
    
    # Sauvegarder
    if output_path is None:
        output_path = os.path.splitext(pdf_path)[0] + '_s2.json'
    
    with open(output_path, 'w') as f:
        json.dump(result, f)
    
    print(f"✅ Sauvegardé: {output_path}")
    print(f"   {n} primitives, {len(set(layerIds))} layers")
    
    return output_path


def main():
    parser = argparse.ArgumentParser(description='Convertit PDF en format SymPointV2')
    parser.add_argument('pdf', help='Fichier PDF')
    parser.add_argument('output', nargs='?', help='Fichier JSON de sortie')
    parser.add_argument('--mode', choices=['ocg', 'visible', 'all'], default='ocg')
    parser.add_argument('--min-length', type=float, default=MIN_LENGTH,
                        help=f'Longueur min (défaut: {MIN_LENGTH})')
    parser.add_argument('--target-size', type=int, default=TARGET_SIZE,
                        help=f'Taille cible (défaut: {TARGET_SIZE})')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf):
        print(f"❌ Fichier non trouvé: {args.pdf}")
        sys.exit(1)
    
    result = parse_pdf(args.pdf, args.output, args.mode, args.min_length, args.target_size)
    sys.exit(0 if result else 1)


if __name__ == '__main__':
    main()
