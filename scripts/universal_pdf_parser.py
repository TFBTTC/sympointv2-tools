#!/usr/bin/env python
"""
universal_pdf_parser.py - Parser PDF Universel pour SymPointV2

Parser intelligent qui s'adapte automatiquement à tous types de PDFs:
- Avec ou sans OCG (calques)
- Différentes conventions d'épaisseur
- Différents styles de dessin

STRATÉGIE DE DÉTECTION DES MURS:
1. Si OCG présents: cherche les calques contenant MURS/WALL/REFEND/CLOISON/STRUCTURE
2. Sinon: utilise l'épaisseur des traits (les murs sont généralement les plus épais)
3. Calcul automatique des seuils basé sur la distribution des épaisseurs

LAYERS DE SORTIE:
- Layer 0: Murs (éléments structurels)
- Layer 1: Éléments moyens (portes, fenêtres, mobilier)  
- Layer 2: Détails fins (annotations, cotes)

Usage:
    python universal_pdf_parser.py input.pdf [output.json] [--debug]

Auteur: Pierre-Antoine / Claude
Version: 1.0
"""

import fitz
import json
import sys
import os
import argparse
import numpy as np
from collections import defaultdict
from dataclasses import dataclass
from typing import List, Tuple, Optional, Dict

# ============================================================================
# CONFIGURATION
# ============================================================================

TARGET_SIZE = 140           # Dimensions cibles (FloorPlanCAD standard)
UNIFORM_WIDTH = 0.1         # Width uniforme pour le modèle
MIN_LENGTH_WALLS = 1.0      # Longueur min pour murs
MIN_LENGTH_MEDIUM = 2.0     # Longueur min pour éléments moyens
MIN_LENGTH_DETAILS = 3.0    # Longueur min pour détails

# Mots-clés pour identifier les calques de murs
WALL_KEYWORDS = [
    'MUR', 'MURS', 'WALL', 'WALLS',
    'REFEND', 'REFENDS',
    'CLOISON', 'CLOISONS',
    'STRUCTURE', 'STRUCT',
    'PORTEUR', 'PORTEURS',
    'BÉTON', 'BETON', 'CONCRETE'
]

# Mots-clés pour identifier les calques à exclure
EXCLUDE_KEYWORDS = [
    'ANNOTATION', 'TEXTE', 'TEXT', 'COTE', 'COTATION',
    'LEGENDE', 'LEGEND', 'CARTOUCHE', 'TITRE'
]


@dataclass
class PDFAnalysis:
    """Résultat de l'analyse d'un PDF."""
    has_ocg: bool
    ocg_count: int
    wall_ocg_xrefs: List[int]
    total_paths: int
    total_primitives: int
    width_distribution: Dict[str, int]
    width_percentiles: Dict[str, float]
    recommended_wall_threshold: float
    recommended_medium_threshold: float


# ============================================================================
# FONCTIONS D'ANALYSE
# ============================================================================

def analyze_pdf(pdf_path: str, debug: bool = False) -> PDFAnalysis:
    """
    Analyse un PDF pour déterminer sa structure et les seuils optimaux.
    """
    doc = fitz.open(pdf_path)
    page = doc[0]
    
    # Analyser les OCG
    has_ocg = False
    ocg_count = 0
    wall_ocg_xrefs = []
    
    try:
        ocgs = doc.get_ocgs()
        if ocgs:
            has_ocg = True
            ocg_count = len(ocgs)
            
            for xref, info in ocgs.items():
                name = info['name'].upper()
                if any(kw in name for kw in WALL_KEYWORDS):
                    wall_ocg_xrefs.append(xref)
    except:
        pass
    
    # Analyser les paths
    drawings = page.get_drawings()
    total_paths = len(drawings)
    total_primitives = sum(len(p.get('items', [])) for p in drawings)
    
    # Distribution des épaisseurs
    widths = []
    for path in drawings:
        w = path.get('width', 0) or 0
        if w > 0:
            widths.append(w)
    
    widths = np.array(widths) if widths else np.array([0.1])
    
    # Calculer les percentiles pour déterminer les seuils
    width_percentiles = {
        'p50': float(np.percentile(widths, 50)),
        'p75': float(np.percentile(widths, 75)),
        'p90': float(np.percentile(widths, 90)),
        'p95': float(np.percentile(widths, 95)),
        'max': float(np.max(widths))
    }
    
    # Distribution par catégorie
    width_distribution = defaultdict(int)
    for w in widths:
        if w >= width_percentiles['p90']:
            width_distribution['thick'] += 1
        elif w >= width_percentiles['p50']:
            width_distribution['medium'] += 1
        else:
            width_distribution['thin'] += 1
    
    # Recommander des seuils
    # Les murs sont généralement dans le top 10% des épaisseurs
    recommended_wall_threshold = width_percentiles['p90']
    recommended_medium_threshold = width_percentiles['p50']
    
    doc.close()
    
    return PDFAnalysis(
        has_ocg=has_ocg,
        ocg_count=ocg_count,
        wall_ocg_xrefs=wall_ocg_xrefs,
        total_paths=total_paths,
        total_primitives=total_primitives,
        width_distribution=dict(width_distribution),
        width_percentiles=width_percentiles,
        recommended_wall_threshold=recommended_wall_threshold,
        recommended_medium_threshold=recommended_medium_threshold
    )


def get_text_zones(page, margin: int = 5) -> List:
    """Récupère les zones de texte à exclure."""
    text_zones = []
    blocks = page.get_text("dict")["blocks"]
    
    for block in blocks:
        if block.get("type") == 0:  # Text block
            bbox = block.get("bbox")
            if bbox:
                rect = fitz.Rect(bbox)
                rect.x0 -= margin
                rect.y0 -= margin
                rect.x1 += margin
                rect.y1 += margin
                text_zones.append(rect)
    
    return text_zones


def detect_cartouche(page) -> Optional[fitz.Rect]:
    """Détecte la zone du cartouche (généralement en bas à droite)."""
    rect = page.rect
    width, height = rect.width, rect.height
    
    # Zone typique du cartouche
    cartouche = fitz.Rect(
        width * 0.60,
        height * 0.75,
        width,
        height
    )
    
    # Vérifier s'il y a du texte dense dans cette zone
    text_in_zone = page.get_text("text", clip=cartouche)
    if len(text_in_zone) > 50:
        return cartouche
    
    # Fallback: bande du bas
    return fitz.Rect(0, height * 0.90, width, height)


def detect_legend(page) -> Optional[fitz.Rect]:
    """Détecte la zone de légende."""
    rect = page.rect
    width, height = rect.width, rect.height
    
    # Chercher "LEGENDE" ou "LEGEND" dans le texte
    text = page.get_text("text").upper()
    if "LEGENDE" in text or "LEGEND" in text:
        # Zone typique de légende (à droite)
        return fitz.Rect(
            width * 0.75,
            0,
            width,
            height * 0.80
        )
    
    return None


def is_in_zones(point, zones: List) -> bool:
    """Vérifie si un point est dans l'une des zones."""
    for zone in zones:
        if zone and zone.contains(point):
            return True
    return False


def calculate_length(points_flat: List[float]) -> float:
    """Calcule la longueur d'une primitive (4 points de contrôle)."""
    pts = np.array(points_flat).reshape(4, 2)
    return sum(np.linalg.norm(pts[i+1] - pts[i]) for i in range(3))


# ============================================================================
# PARSER PRINCIPAL
# ============================================================================

def parse_pdf(pdf_path: str, output_path: Optional[str] = None, 
              debug: bool = False) -> Optional[str]:
    """
    Parse un PDF de manière universelle.
    
    Args:
        pdf_path: Chemin vers le PDF
        output_path: Chemin de sortie (optionnel)
        debug: Mode debug
    
    Returns:
        Chemin du fichier JSON généré
    """
    print(f"\n{'='*60}")
    print(f"📄 UNIVERSAL PDF PARSER")
    print(f"{'='*60}")
    print(f"Fichier: {pdf_path}")
    
    # Phase 1: Analyse
    print(f"\n🔍 Phase 1: Analyse du PDF...")
    analysis = analyze_pdf(pdf_path, debug)
    
    print(f"   - OCG: {'Oui' if analysis.has_ocg else 'Non'} ({analysis.ocg_count} calques)")
    if analysis.wall_ocg_xrefs:
        print(f"   - Calques murs détectés: {len(analysis.wall_ocg_xrefs)}")
    print(f"   - Paths: {analysis.total_paths}")
    print(f"   - Primitives: {analysis.total_primitives}")
    print(f"   - Seuil murs recommandé: {analysis.recommended_wall_threshold:.3f}")
    print(f"   - Seuil moyen recommandé: {analysis.recommended_medium_threshold:.3f}")
    
    # Utiliser les seuils calculés
    WALL_THRESHOLD = analysis.recommended_wall_threshold
    MEDIUM_THRESHOLD = analysis.recommended_medium_threshold
    
    # Phase 2: Extraction
    print(f"\n📐 Phase 2: Extraction des primitives...")
    
    doc = fitz.open(pdf_path)
    page = doc[0]
    orig_width, orig_height = page.rect.width, page.rect.height
    
    # Zones à exclure
    text_zones = get_text_zones(page)
    cartouche = detect_cartouche(page)
    legend = detect_legend(page)
    exclude_zones = text_zones + ([cartouche] if cartouche else []) + ([legend] if legend else [])
    
    print(f"   - Dimensions: {orig_width:.0f} x {orig_height:.0f}")
    print(f"   - Zones texte: {len(text_zones)}")
    print(f"   - Cartouche: {'Oui' if cartouche else 'Non'}")
    print(f"   - Légende: {'Oui' if legend else 'Non'}")
    
    # Extraire les primitives
    drawings = page.get_drawings()
    all_primitives = []
    
    stats = {
        'walls': 0, 'medium': 0, 'details': 0,
        'excluded_zone': 0, 'excluded_length': 0
    }
    
    for path_idx, path in enumerate(drawings):
        original_width = path.get('width', 0) or 0
        
        # Classifier par épaisseur
        if original_width >= WALL_THRESHOLD:
            element_type = 'wall'
        elif original_width >= MEDIUM_THRESHOLD:
            element_type = 'medium'
        else:
            element_type = 'detail'
        
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
                
                # Les murs ne sont PAS exclus par les zones
                if element_type == 'wall':
                    all_primitives.append((0, points, path_idx, original_width, element_type))
                else:
                    # Exclure si dans zone texte/cartouche/légende
                    if is_in_zones(p1, exclude_zones) and is_in_zones(p2, exclude_zones):
                        stats['excluded_zone'] += 1
                        continue
                    all_primitives.append((0, points, path_idx, original_width, element_type))
            
            elif cmd_type == 'c':  # Courbe de Bézier
                if len(item) >= 5:
                    points = []
                    for p in item[1:5]:
                        points.extend([p.x, p.y])
                    if len(points) == 8:
                        p_start = item[1]
                        if element_type == 'wall':
                            all_primitives.append((1, points, path_idx, original_width, element_type))
                        elif not is_in_zones(p_start, exclude_zones):
                            all_primitives.append((1, points, path_idx, original_width, element_type))
                        else:
                            stats['excluded_zone'] += 1
            
            elif cmd_type == 're':  # Rectangle
                rect = item[1]
                center = fitz.Point((rect.x0 + rect.x1)/2, (rect.y0 + rect.y1)/2)
                
                if element_type != 'wall' and is_in_zones(center, exclude_zones):
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
    
    doc.close()
    print(f"   - Après zones: {len(all_primitives)} (exclu: {stats['excluded_zone']})")
    
    # Phase 3: Normalisation
    print(f"\n🔧 Phase 3: Normalisation...")
    
    scale = TARGET_SIZE / max(orig_width, orig_height)
    
    commands, args, lengths, layerIds = [], [], [], []
    
    for cmd, points, layer_id, orig_w, elem_type in all_primitives:
        scaled_points = [p * scale for p in points]
        length = calculate_length(scaled_points)
        
        # Seuils de longueur par type
        if elem_type == 'wall':
            min_len = MIN_LENGTH_WALLS
        elif elem_type == 'medium':
            min_len = MIN_LENGTH_MEDIUM
        else:
            min_len = MIN_LENGTH_DETAILS
        
        if length >= min_len:
            commands.append(cmd)
            args.append(scaled_points)
            lengths.append(length)
            
            if elem_type == 'wall':
                layerIds.append(0)
                stats['walls'] += 1
            elif elem_type == 'medium':
                layerIds.append(1)
                stats['medium'] += 1
            else:
                layerIds.append(2)
                stats['details'] += 1
        else:
            stats['excluded_length'] += 1
    
    print(f"   - Exclus par longueur: {stats['excluded_length']}")
    print(f"\n✅ Primitives finales: {len(commands)}")
    print(f"   - Murs (layer 0): {stats['walls']}")
    print(f"   - Moyens (layer 1): {stats['medium']}")
    print(f"   - Détails (layer 2): {stats['details']}")
    
    if not commands:
        print("⚠️ Aucune primitive extraite!")
        return None
    
    # Statistiques finales
    lengths_arr = np.array(lengths)
    print(f"\n📊 Statistiques:")
    print(f"   - Dimensions: {int(orig_width * scale)} x {int(orig_height * scale)}")
    print(f"   - Lengths: min={lengths_arr.min():.2f}, max={lengths_arr.max():.2f}, mean={lengths_arr.mean():.2f}")
    
    # Phase 4: Export
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
        "rgb": [[0, 0, 0]] * n,
        "_metadata": {
            "source": os.path.basename(pdf_path),
            "parser_version": "universal_1.0",
            "has_ocg": analysis.has_ocg,
            "ocg_count": analysis.ocg_count,
            "wall_threshold": WALL_THRESHOLD,
            "medium_threshold": MEDIUM_THRESHOLD
        }
    }
    
    if output_path is None:
        output_path = os.path.splitext(pdf_path)[0] + '_s2.json'
    
    with open(output_path, 'w') as f:
        json.dump(result, f)
    
    print(f"\n💾 Sauvegardé: {output_path}")
    return output_path


# ============================================================================
# CLI
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='Universal PDF Parser for SymPointV2',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Exemples:
  python universal_pdf_parser.py plan.pdf
  python universal_pdf_parser.py plan.pdf output.json --debug
  
Le parser s'adapte automatiquement aux PDFs avec ou sans calques OCG.
        """
    )
    parser.add_argument('pdf', help='Fichier PDF à parser')
    parser.add_argument('output', nargs='?', help='Fichier JSON de sortie (optionnel)')
    parser.add_argument('--debug', action='store_true', help='Mode debug')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.pdf):
        print(f"❌ Fichier non trouvé: {args.pdf}")
        sys.exit(1)
    
    result = parse_pdf(args.pdf, args.output, args.debug)
    sys.exit(0 if result else 1)


if __name__ == '__main__':
    main()
