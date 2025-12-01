#!/usr/bin/env python
"""
smart_pdf_parser_v4.py - Parser PDF intelligent pour SymPointV2

AMÉLIORATIONS v4:
1. Détection et exclusion des zones de texte
2. Détection du cartouche (zone en bas à droite)
3. Filtrage agressif des micro-primitives
4. Statistiques détaillées pour diagnostic
5. Mode crop automatique

Usage:
    python smart_pdf_parser_v4.py input.pdf [output.json]
    python smart_pdf_parser_v4.py input.pdf --min-length 5  # Plus strict
    python smart_pdf_parser_v4.py input.pdf --exclude-text  # Exclure zones texte
    python smart_pdf_parser_v4.py input.pdf --crop-plan     # Auto-crop plan seulement
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
MIN_LENGTH_DEFAULT = 4.0  # Plus strict qu'avant (était 0.5)
UNIFORM_WIDTH = 0.1


def get_text_zones(page, margin=10):
    """
    Récupère les zones contenant du texte pour les exclure.
    Retourne une liste de fitz.Rect.
    """
    text_zones = []
    blocks = page.get_text("dict")["blocks"]
    
    for block in blocks:
        if block.get("type") == 0:  # Text block
            bbox = block.get("bbox")
            if bbox:
                # Agrandir légèrement la zone
                rect = fitz.Rect(bbox)
                rect.x0 -= margin
                rect.y0 -= margin
                rect.x1 += margin
                rect.y1 += margin
                text_zones.append(rect)
    
    return text_zones


def detect_cartouche_zone(page):
    """
    Détecte la zone du cartouche (généralement en bas à droite).
    Utilise la densité de texte comme indicateur.
    """
    rect = page.rect
    width, height = rect.width, rect.height
    
    # Heuristique: cartouche dans les 20% du bas ou 25% de droite
    # On combine les deux pour être sûr
    cartouche = fitz.Rect(
        width * 0.6,   # Commence à 60% de la largeur
        height * 0.75, # Commence à 75% de la hauteur
        width,
        height
    )
    
    # Vérifier s'il y a du texte dans cette zone
    text_in_zone = page.get_text("text", clip=cartouche)
    if len(text_in_zone) > 50:  # Beaucoup de texte = probablement cartouche
        return cartouche
    
    # Alternative: juste le bas
    return fitz.Rect(0, height * 0.85, width, height)


def detect_legend_zone(page):
    """
    Détecte la zone de légende (souvent à droite du plan).
    """
    rect = page.rect
    width, height = rect.width, rect.height
    
    # Chercher "LEGENDE" ou "LEGEND" dans le texte
    text = page.get_text("text")
    if "LEGENDE" in text.upper() or "LEGEND" in text.upper():
        # Légende probablement à droite
        return fitz.Rect(width * 0.75, 0, width, height * 0.85)
    
    return None


def is_point_in_zones(point, zones):
    """Vérifie si un point est dans une des zones à exclure."""
    for zone in zones:
        if zone and zone.contains(point):
            return True
    return False


def calculate_length(points_flat):
    """Calcule la longueur totale d'une primitive."""
    pts = np.array(points_flat).reshape(4, 2)
    return sum(np.linalg.norm(pts[i+1] - pts[i]) for i in range(3))


def parse_pdf(pdf_path, output_path=None, min_length=MIN_LENGTH_DEFAULT, 
              exclude_text=True, crop_plan=True, debug=False):
    """
    Parse un PDF en format SymPointV2 avec filtrage intelligent.
    """
    print(f"📄 Ouverture: {pdf_path}")
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    orig_width, orig_height = page.rect.width, page.rect.height
    print(f"   Dimensions: {orig_width:.0f} x {orig_height:.0f}")
    
    # Zones à exclure
    exclude_zones = []
    
    if exclude_text:
        text_zones = get_text_zones(page)
        exclude_zones.extend(text_zones)
        print(f"   Zones texte à exclure: {len(text_zones)}")
    
    if crop_plan:
        cartouche = detect_cartouche_zone(page)
        if cartouche:
            exclude_zones.append(cartouche)
            print(f"   Cartouche détecté: {cartouche}")
        
        legend = detect_legend_zone(page)
        if legend:
            exclude_zones.append(legend)
            print(f"   Légende détectée: {legend}")
    
    # Extraire les primitives
    drawings = page.get_drawings()
    print(f"   Paths bruts: {len(drawings)}")
    
    # Collecter les primitives
    all_primitives = []
    excluded_by_zone = 0
    excluded_by_length = 0
    
    for path_idx, path in enumerate(drawings):
        layer_id = path_idx
        
        for item in path['items']:
            cmd_type = item[0]
            
            if cmd_type == 'l':  # Ligne
                p1, p2 = item[1], item[2]
                
                # Vérifier si dans zone à exclure
                if is_point_in_zones(p1, exclude_zones) and is_point_in_zones(p2, exclude_zones):
                    excluded_by_zone += 1
                    continue
                
                points = [
                    p1.x, p1.y,
                    p1.x + (p2.x - p1.x) * 0.33, p1.y + (p2.y - p1.y) * 0.33,
                    p1.x + (p2.x - p1.x) * 0.66, p1.y + (p2.y - p1.y) * 0.66,
                    p2.x, p2.y
                ]
                all_primitives.append((0, points, layer_id))
                
            elif cmd_type == 'c':  # Courbe
                if len(item) >= 5:
                    p_start = item[1]
                    if is_point_in_zones(p_start, exclude_zones):
                        excluded_by_zone += 1
                        continue
                    
                    points = []
                    for p in item[1:5]:
                        points.extend([p.x, p.y])
                    if len(points) == 8:
                        all_primitives.append((1, points, layer_id))
                        
            elif cmd_type == 're':  # Rectangle
                rect = item[1]
                center = fitz.Point((rect.x0 + rect.x1)/2, (rect.y0 + rect.y1)/2)
                if is_point_in_zones(center, exclude_zones):
                    excluded_by_zone += 1
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
                    all_primitives.append((0, points, layer_id))
    
    print(f"   Exclus par zone: {excluded_by_zone}")
    print(f"   Primitives après zones: {len(all_primitives)}")
    
    doc.close()
    
    # Rescaling vers TARGET_SIZE
    scale = TARGET_SIZE / max(orig_width, orig_height)
    
    # Filtrage par longueur APRÈS rescaling
    commands, args, lengths, layerIds = [], [], [], []
    
    for cmd, points, layer_id in all_primitives:
        scaled_points = [p * scale for p in points]
        length = calculate_length(scaled_points)
        
        if length >= min_length:
            commands.append(cmd)
            args.append(scaled_points)
            lengths.append(length)
            layerIds.append(layer_id)
        else:
            excluded_by_length += 1
    
    print(f"   Exclus par longueur < {min_length}: {excluded_by_length}")
    print(f"   Primitives finales: {len(commands)}")
    
    if not commands:
        print("⚠️  Aucune primitive restante! Essayez --min-length plus bas")
        return None
    
    # Stats
    lengths_arr = np.array(lengths)
    print(f"\n📊 Statistiques finales:")
    print(f"   Dimensions: {int(orig_width * scale)} x {int(orig_height * scale)}")
    print(f"   Primitives: {len(commands)}")
    print(f"   Lengths: min={lengths_arr.min():.2f}, max={lengths_arr.max():.2f}")
    print(f"            mean={lengths_arr.mean():.2f}, median={np.median(lengths_arr):.2f}")
    
    # Comparaison avec FloorPlanCAD
    print(f"\n📈 Comparaison FloorPlanCAD:")
    print(f"   Target: ~900-2000 primitives, lengths mean ~5.4, median ~2.1")
    if len(commands) > 5000:
        print(f"   ⚠️  Trop de primitives! Augmentez --min-length")
    if lengths_arr.mean() < 2:
        print(f"   ⚠️  Lengths trop courts! Augmentez --min-length")
    
    # Construire JSON
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
    
    # Sauvegarder
    if output_path is None:
        output_path = os.path.splitext(pdf_path)[0] + '_s2.json'
    
    with open(output_path, 'w') as f:
        json.dump(result, f)
    
    print(f"\n✅ Sauvegardé: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description='Parser PDF intelligent pour SymPointV2')
    parser.add_argument('pdf', help='Fichier PDF')
    parser.add_argument('output', nargs='?', help='Fichier JSON de sortie')
    parser.add_argument('--min-length', type=float, default=MIN_LENGTH_DEFAULT,
                        help=f'Longueur min après rescaling (défaut: {MIN_LENGTH_DEFAULT})')
    parser.add_argument('--no-exclude-text', action='store_true',
                        help='Ne pas exclure les zones de texte')
    parser.add_argument('--no-crop', action='store_true',
                        help='Ne pas exclure cartouche/légende')
    parser.add_argument('--debug', action='store_true',
                        help='Mode debug')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf):
        print(f"❌ Fichier non trouvé: {args.pdf}")
        sys.exit(1)
    
    result = parse_pdf(
        args.pdf, 
        args.output, 
        min_length=args.min_length,
        exclude_text=not args.no_exclude_text,
        crop_plan=not args.no_crop,
        debug=args.debug
    )
    
    sys.exit(0 if result else 1)


if __name__ == '__main__':
    main()
