#!/usr/bin/env python
"""
smart_pdf_parser_v5.py - Parser PDF avec protection des murs

AMÉLIORATIONS v5:
1. PROTÈGE les paths épais (murs) même dans les zones texte
2. Utilise l'épaisseur (width) comme indicateur de type d'élément
3. Groupe les primitives par épaisseur pour créer des layers logiques
4. Moins de filtrage sur les éléments structurels

Stratégie:
- width >= 0.4 = MURS (toujours garder, layer 0)
- width 0.15-0.4 = Éléments moyens (portes, fenêtres, layer 1)
- width < 0.15 = Détails fins (texte, annotations, layer 2)

Usage:
    python smart_pdf_parser_v5.py input.pdf [output.json]
"""

import fitz
import json
import sys
import os
import argparse
import numpy as np
from collections import defaultdict

# Paramètres FloorPlanCAD
TARGET_SIZE = 140
UNIFORM_WIDTH = 0.1

# Seuils d'épaisseur (en points PDF)
WALL_WIDTH_THRESHOLD = 0.4      # Murs = traits épais
MEDIUM_WIDTH_THRESHOLD = 0.15   # Éléments moyens
MIN_LENGTH_WALLS = 1.0          # Longueur min pour murs (plus permissif)
MIN_LENGTH_OTHER = 3.0          # Longueur min pour autres éléments


def get_text_zones(page, margin=5):
    """Récupère les zones de texte (margin réduit pour moins exclure)."""
    text_zones = []
    blocks = page.get_text("dict")["blocks"]
    
    for block in blocks:
        if block.get("type") == 0:
            bbox = block.get("bbox")
            if bbox:
                rect = fitz.Rect(bbox)
                rect.x0 -= margin
                rect.y0 -= margin
                rect.x1 += margin
                rect.y1 += margin
                text_zones.append(rect)
    
    return text_zones


def detect_cartouche_zone(page):
    """Détecte la zone du cartouche."""
    rect = page.rect
    width, height = rect.width, rect.height
    
    cartouche = fitz.Rect(
        width * 0.65,
        height * 0.80,
        width,
        height
    )
    
    text_in_zone = page.get_text("text", clip=cartouche)
    if len(text_in_zone) > 100:
        return cartouche
    
    return fitz.Rect(0, height * 0.90, width, height)


def is_point_in_zones(point, zones):
    """Vérifie si un point est dans une zone."""
    for zone in zones:
        if zone and zone.contains(point):
            return True
    return False


def calculate_length(points_flat):
    """Calcule la longueur totale d'une primitive."""
    pts = np.array(points_flat).reshape(4, 2)
    return sum(np.linalg.norm(pts[i+1] - pts[i]) for i in range(3))


def classify_by_width(width):
    """Classifie un élément par son épaisseur."""
    if width >= WALL_WIDTH_THRESHOLD:
        return 'wall'
    elif width >= MEDIUM_WIDTH_THRESHOLD:
        return 'medium'
    else:
        return 'detail'


def parse_pdf(pdf_path, output_path=None, debug=False):
    """
    Parse un PDF en protégeant les murs.
    """
    print(f"📄 Ouverture: {pdf_path}")
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    orig_width, orig_height = page.rect.width, page.rect.height
    print(f"   Dimensions: {orig_width:.0f} x {orig_height:.0f}")
    
    text_zones = get_text_zones(page)
    cartouche = detect_cartouche_zone(page)
    exclude_zones = text_zones + ([cartouche] if cartouche else [])
    print(f"   Zones texte: {len(text_zones)}, Cartouche: {cartouche is not None}")
    
    drawings = page.get_drawings()
    print(f"   Paths bruts: {len(drawings)}")
    
    width_stats = defaultdict(int)
    for path in drawings:
        w = path.get('width', 0) or 0
        width_stats[classify_by_width(w)] += 1
    
    print(f"\n📊 Distribution par épaisseur:")
    print(f"   Murs (width >= {WALL_WIDTH_THRESHOLD}): {width_stats['wall']}")
    print(f"   Moyens ({MEDIUM_WIDTH_THRESHOLD} <= width < {WALL_WIDTH_THRESHOLD}): {width_stats['medium']}")
    print(f"   Détails (width < {MEDIUM_WIDTH_THRESHOLD}): {width_stats['detail']}")
    
    all_primitives = []
    stats = {'walls_kept': 0, 'medium_kept': 0, 'detail_kept': 0,
             'excluded_zone': 0, 'excluded_length': 0}
    
    for path_idx, path in enumerate(drawings):
        original_width = path.get('width', 0) or 0
        element_type = classify_by_width(original_width)
        
        for item in path['items']:
            cmd_type = item[0]
            
            if cmd_type == 'l':
                p1, p2 = item[1], item[2]
                points = [
                    p1.x, p1.y,
                    p1.x + (p2.x - p1.x) * 0.33, p1.y + (p2.y - p1.y) * 0.33,
                    p1.x + (p2.x - p1.x) * 0.66, p1.y + (p2.y - p1.y) * 0.66,
                    p2.x, p2.y
                ]
                
                if element_type == 'wall':
                    all_primitives.append((0, points, path_idx, original_width, 'wall'))
                else:
                    if is_point_in_zones(p1, exclude_zones) and is_point_in_zones(p2, exclude_zones):
                        stats['excluded_zone'] += 1
                        continue
                    all_primitives.append((0, points, path_idx, original_width, element_type))
                
            elif cmd_type == 'c':
                if len(item) >= 5:
                    p_start = item[1]
                    points = []
                    for p in item[1:5]:
                        points.extend([p.x, p.y])
                    if len(points) == 8:
                        if element_type == 'wall':
                            all_primitives.append((1, points, path_idx, original_width, 'wall'))
                        elif not is_point_in_zones(p_start, exclude_zones):
                            all_primitives.append((1, points, path_idx, original_width, element_type))
                        else:
                            stats['excluded_zone'] += 1
                            
            elif cmd_type == 're':
                rect = item[1]
                center = fitz.Point((rect.x0 + rect.x1)/2, (rect.y0 + rect.y1)/2)
                
                if element_type != 'wall' and is_point_in_zones(center, exclude_zones):
                    stats['excluded_zone'] += 1
                    continue
                
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
                    all_primitives.append((0, points, path_idx, original_width, element_type))
    
    print(f"\n   Après exclusion zones: {len(all_primitives)} (exclu: {stats['excluded_zone']})")
    
    doc.close()
    
    scale = TARGET_SIZE / max(orig_width, orig_height)
    
    commands, args, lengths, layerIds, widths_out = [], [], [], [], []
    
    for cmd, points, layer_id, orig_w, elem_type in all_primitives:
        scaled_points = [p * scale for p in points]
        length = calculate_length(scaled_points)
        
        if elem_type == 'wall':
            min_len = MIN_LENGTH_WALLS
        else:
            min_len = MIN_LENGTH_OTHER
        
        if length >= min_len:
            commands.append(cmd)
            args.append(scaled_points)
            lengths.append(length)
            if elem_type == 'wall':
                layerIds.append(0)
                stats['walls_kept'] += 1
            elif elem_type == 'medium':
                layerIds.append(1)
                stats['medium_kept'] += 1
            else:
                layerIds.append(2)
                stats['detail_kept'] += 1
            widths_out.append(orig_w * scale)
        else:
            stats['excluded_length'] += 1
    
    print(f"   Exclus par longueur: {stats['excluded_length']}")
    print(f"\n✅ Primitives finales: {len(commands)}")
    print(f"   - Murs: {stats['walls_kept']}")
    print(f"   - Moyens: {stats['medium_kept']}")
    print(f"   - Détails: {stats['detail_kept']}")
    
    if not commands:
        print("⚠️  Aucune primitive!")
        return None
    
    lengths_arr = np.array(lengths)
    print(f"\n📊 Statistiques:")
    print(f"   Dimensions: {int(orig_width * scale)} x {int(orig_height * scale)}")
    print(f"   Lengths: min={lengths_arr.min():.2f}, max={lengths_arr.max():.2f}, mean={lengths_arr.mean():.2f}")
    
    n = len(commands)
    result = {
        "width": int(orig_width * scale),
        "height": int(orig_height * scale),
        "commands": commands,
        "args": args,
        "lengths": lengths,
        "layerIds": layerIds,
        "widths": [UNIFORM_WIDTH] * n,
        "semanticIds": [35] * n,
        "instanceIds": [-1] * n,
        "rgb": [[0, 0, 0]] * n
    }
    
    if output_path is None:
        output_path = os.path.splitext(pdf_path)[0] + '_s2.json'
    
    with open(output_path, 'w') as f:
        json.dump(result, f)
    
    print(f"\n💾 Sauvegardé: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description='Parser PDF v5 - Protection des murs')
    parser.add_argument('pdf', help='Fichier PDF')
    parser.add_argument('output', nargs='?', help='Fichier JSON de sortie')
    parser.add_argument('--debug', action='store_true')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf):
        print(f"❌ Fichier non trouvé: {args.pdf}")
        sys.exit(1)
    
    result = parse_pdf(args.pdf, args.output, args.debug)
    sys.exit(0 if result else 1)


if __name__ == '__main__':
    main()
