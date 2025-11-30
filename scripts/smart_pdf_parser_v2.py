#!/usr/bin/env python
"""
smart_pdf_parser_v2.py - Parser PDF intelligent pour SymPointV2
Gère 3 cas: OCG direct, OCG content_stream, sans OCG
"""

import fitz
import json
import sys
import os
import numpy as np
from collections import Counter

class SmartPDFParserV2:
    def __init__(self, max_primitives=50000, verbose=True):
        self.max_primitives = max_primitives
        self.verbose = verbose
        
    def log(self, msg):
        if self.verbose: print(msg)
    
    def detect_ocg_mode(self, doc):
        ocgs = doc.get_ocgs()
        if not ocgs: return 'none', {}
        for page in doc:
            for path in page.get_drawings():
                if path.get('oc'): return 'direct', ocgs
        return 'content_stream', ocgs
    
    def build_layer_mapping_from_ocgs(self, ocgs):
        categories = {
            'MURS_EXT': [], 'REFENDS': [], 'DALLES': [], 'ESCALIERS': [],
            'CLOISONS': [], 'SANITAIRES': [], 'CUISINE': [], 'ELEC': [],
            'FLUIDES': [], 'ANNOTATIONS': [], 'AUTRES': []
        }
        ocg_to_category = {}
        
        for xref, info in ocgs.items():
            name = info.get('name', '').upper()
            if 'MURS EXT' in name or 'MUR EXT' in name: cat = 'MURS_EXT'
            elif 'REFEND' in name: cat = 'REFENDS'
            elif 'DALLE' in name or 'SOL' in name: cat = 'DALLES'
            elif 'ESCALIER' in name or 'ASCENSEUR' in name: cat = 'ESCALIERS'
            elif 'CLOISON' in name or 'AGGLO' in name or 'SAD' in name: cat = 'CLOISONS'
            elif 'SANITAIRE' in name or 'WC' in name: cat = 'SANITAIRES'
            elif 'CUISINE' in name: cat = 'CUISINE'
            elif 'ELEC' in name: cat = 'ELEC'
            elif 'FLUIDE' in name or 'VB' in name or 'VH' in name: cat = 'FLUIDES'
            elif 'ANNOTATION' in name or 'COTATION' in name or 'TEXTE' in name: cat = 'ANNOTATIONS'
            else: cat = 'AUTRES'
            categories[cat].append(xref)
            ocg_to_category[xref] = cat
        
        ocg_to_layer = {}
        layer_to_name = {}
        for lid, (xref, info) in enumerate(ocgs.items()):
            ocg_to_layer[xref] = lid
            layer_to_name[lid] = info.get('name', f'Layer_{lid}')
        
        self.log(f"\n📊 Catégories détectées:")
        for cat, xrefs in categories.items():
            if xrefs: self.log(f"   {cat}: {len(xrefs)} OCGs")
        
        return ocg_to_layer, layer_to_name, ocg_to_category
    
    def interpolate_line(self, p1, p2):
        return [
            [p1[0], p1[1]],
            [p1[0] + (p2[0]-p1[0])*0.333, p1[1] + (p2[1]-p1[1])*0.333],
            [p1[0] + (p2[0]-p1[0])*0.667, p1[1] + (p2[1]-p1[1])*0.667],
            [p2[0], p2[1]]
        ]
    
    def parse(self, pdf_path, output_path=None):
        doc = fitz.open(pdf_path)
        mode, ocgs = self.detect_ocg_mode(doc)
        
        self.log(f"\n{'='*60}")
        self.log(f"PARSING PDF : {os.path.basename(pdf_path)}")
        self.log(f"{'='*60}")
        self.log(f"\n🔍 Mode OCG: {mode}")
        self.log(f"   OCGs définis: {len(ocgs)}")
        
        if mode != 'none':
            ocg_to_layer, layer_to_name, ocg_to_category = self.build_layer_mapping_from_ocgs(ocgs)
        else:
            ocg_to_layer, layer_to_name, ocg_to_category = {}, {}, {}
        
        commands, args, layerIds, widths = [], [], [], []
        width, height = 0, 0
        path_index = 0
        
        for page_num, page in enumerate(doc):
            width = max(width, page.rect.width)
            height = max(height, page.rect.height)
            drawings = page.get_drawings()
            self.log(f"\n📄 Page {page_num + 1}: {len(drawings)} paths")
            
            for path in drawings:
                stroke_width = path.get('width', 1.0) or 1.0
                
                if mode == 'direct':
                    oc = path.get('oc')
                    layer_id = ocg_to_layer.get(oc, len(ocg_to_layer)) if oc else len(ocg_to_layer)
                elif mode == 'content_stream':
                    layer_id = path_index % max(1, len(ocgs))
                else:
                    layer_id = path_index
                
                for item in path.get('items', []):
                    cmd = item[0]
                    
                    if cmd == 'l':
                        p1, p2 = item[1], item[2]
                        points = self.interpolate_line([p1.x, p1.y], [p2.x, p2.y])
                        commands.append('l')
                        args.append(points)
                        layerIds.append(layer_id)
                        widths.append(stroke_width)
                    elif cmd == 'c' and len(item) >= 5:
                        points = [[p.x, p.y] for p in item[1:5]]
                        commands.append('c')
                        args.append(points)
                        layerIds.append(layer_id)
                        widths.append(stroke_width)
                    elif cmd == 're':
                        r = item[1]
                        corners = [(r.x0,r.y0),(r.x1,r.y0),(r.x1,r.y1),(r.x0,r.y1)]
                        for i in range(4):
                            p1, p2 = corners[i], corners[(i+1)%4]
                            points = self.interpolate_line(list(p1), list(p2))
                            commands.append('l')
                            args.append(points)
                            layerIds.append(layer_id)
                            widths.append(stroke_width)
                    elif cmd == 'qu' and len(item) >= 2:
                        q = item[1]
                        corners = [(q.ul.x,q.ul.y),(q.ur.x,q.ur.y),(q.lr.x,q.lr.y),(q.ll.x,q.ll.y)]
                        for i in range(4):
                            p1, p2 = corners[i], corners[(i+1)%4]
                            points = self.interpolate_line(list(p1), list(p2))
                            commands.append('l')
                            args.append(points)
                            layerIds.append(layer_id)
                            widths.append(stroke_width)
                    
                    if len(commands) >= self.max_primitives: break
                
                path_index += 1
                if len(commands) >= self.max_primitives: break
            if len(commands) >= self.max_primitives:
                self.log(f"⚠️ Limite de {self.max_primitives} primitives atteinte")
                break
        
        doc.close()
        n = min(len(commands), self.max_primitives)
        
        result = {
            "width": int(width), "height": int(height),
            "commands": commands[:n], "args": args[:n],
            "layerIds": layerIds[:n],
            "semanticIds": [35] * n, "instanceIds": [0] * n,
            "widths": widths[:n],
            "_metadata": {
                "source": os.path.basename(pdf_path),
                "ocg_mode": mode,
                "num_ocgs": len(ocgs),
                "num_layers": len(set(layerIds[:n])),
                "layer_names": layer_to_name,
                "ocg_categories": {str(k): v for k, v in ocg_to_category.items()}
            }
        }
        
        self.log(f"\n{'='*60}")
        self.log(f"📊 RÉSULTAT")
        self.log(f"{'='*60}")
        self.log(f"   Primitives: {n}")
        self.log(f"   Layers uniques: {len(set(layerIds[:n]))}")
        self.log(f"   Dimensions: {result['width']} x {result['height']}")
        
        layer_counts = Counter(result['layerIds'])
        self.log(f"\n   Distribution des layers (top 10):")
        for lid, cnt in sorted(layer_counts.items(), key=lambda x: -x[1])[:10]:
            name = layer_to_name.get(lid, f'Layer_{lid}')[:40]
            self.log(f"      L{lid}: {cnt:5d} ({100*cnt/n:.1f}%) - {name}")
        
        if output_path is None:
            output_path = os.path.splitext(pdf_path)[0] + '_s2.json'
        
        with open(output_path, 'w') as f:
            json.dump(result, f)
        
        self.log(f"\n✅ Sauvegardé: {output_path}")
        return result, output_path


def main():
    if len(sys.argv) < 2:
        print("Usage: python smart_pdf_parser_v2.py <fichier.pdf> [output.json]")
        print("\nOptions:")
        print("  --max-primitives N  Limite (défaut: 50000)")
        print("  --quiet             Mode silencieux")
        sys.exit(1)
    
    pdf_path = sys.argv[1]
    output_path = None
    max_prims = 50000
    verbose = True
    
    i = 2
    while i < len(sys.argv):
        if sys.argv[i] == '--max-primitives' and i+1 < len(sys.argv):
            max_prims = int(sys.argv[i+1])
            i += 2
        elif sys.argv[i] == '--quiet':
            verbose = False
            i += 1
        elif not sys.argv[i].startswith('--'):
            output_path = sys.argv[i]
            i += 1
        else:
            i += 1
    
    parser = SmartPDFParserV2(max_primitives=max_prims, verbose=verbose)
    parser.parse(pdf_path, output_path)


if __name__ == '__main__':
    main()
