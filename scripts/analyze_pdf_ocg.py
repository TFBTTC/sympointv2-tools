#!/usr/bin/env python
"""Analyse la structure OCG d'un PDF"""
import fitz
import sys

def analyze_pdf_ocg(pdf_path):
    doc = fitz.open(pdf_path)
    
    print(f"{'='*60}")
    print(f"ANALYSE PDF : {pdf_path}")
    print(f"{'='*60}")
    
    print(f"\n📄 Infos générales:")
    print(f"  - Pages: {len(doc)}")
    print(f"  - Format: {doc[0].rect.width:.0f} x {doc[0].rect.height:.0f}")
    
    print(f"\n🔍 Analyse OCG:")
    
    ocgs = doc.get_ocgs()
    if ocgs:
        print(f"  ✅ OCGs trouvés: {len(ocgs)}")
        for xref, info in ocgs.items():
            print(f"     - xref={xref}: {info.get('name', '?')}")
    else:
        print(f"  ⚠️ Aucun OCG trouvé")
    
    print(f"\n📐 Analyse des primitives:")
    
    total_primitives = 0
    all_oc_refs = set()
    
    for page_num, page in enumerate(doc):
        drawings = page.get_drawings()
        print(f"\n  Page {page_num + 1}: {len(drawings)} paths")
        
        type_counts = {}
        oc_paths = 0
        
        for path in drawings:
            oc = path.get('oc')
            if oc:
                oc_paths += 1
                all_oc_refs.add(str(oc))
            
            for item in path.get('items', []):
                cmd = item[0]
                type_counts[cmd] = type_counts.get(cmd, 0) + 1
                total_primitives += 1
        
        print(f"     Types: {type_counts}")
        if oc_paths > 0:
            print(f"     ✅ Paths avec OCG: {oc_paths}")
    
    print(f"\n📊 Résumé:")
    print(f"  - Total primitives: {total_primitives}")
    print(f"  - Références OC: {len(all_oc_refs)}")
    
    print(f"\n{'='*60}")
    has_ocg = len(all_oc_refs) > 0 or (ocgs and len(ocgs) > 0)
    if has_ocg:
        print(f"✅ CE PDF A DES OCG")
    else:
        print(f"⚠️ CE PDF N'A PAS D'OCG")
    print(f"{'='*60}")
    
    doc.close()
    return {'has_ocg': has_ocg, 'total_primitives': total_primitives}

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: python analyze_pdf_ocg.py <fichier.pdf>")
        sys.exit(1)
    analyze_pdf_ocg(sys.argv[1])
