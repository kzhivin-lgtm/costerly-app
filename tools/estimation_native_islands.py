"""Build clean Island crops and neutral CAD evidence from PDF and Detection."""


from collections import defaultdict
from hashlib import sha256
from math import atan2, dist
import json

import pymupdf as pdf


def delta(a,b):
    return b[0]-a[0], b[1]-a[1]

def dot(a,b):
    return a[0]*b[0]+a[1]*b[1]

def cross(a,b):
    return a[0]*b[1]-a[1]*b[0]

def planar_faces(segments, tolerance):
    cuts = [{0., 1.} for _ in segments]
    for i, (a,b) in enumerate(segments):
        u = delta(a,b)
        for j in range(i+1,len(segments)):
            c,d = segments[j]
            v = delta(c,d)
            den = cross(u,v)
            if abs(den)>1e-8:
                t,s = cross(delta(a,c),v)/den,cross(delta(a,c),u)/den
                if 0<t<1 and 0<s<1:
                    cuts[i].add(t)
                    cuts[j].add(s)
            # Snap nearly meeting endpoints to the opposing edge and split at T junctions.
            for start, vec, other_ends, idx in [(a,u,(c,d),i),(c,v,(a,b),j)]:
                for p in other_ends:
                    t=dot(delta(start,p),vec)/dot(vec,vec)
                    if 0<t<1 and abs(cross(vec,delta(start,p))) <= tolerance*dist((0,0),vec):
                        cuts[idx].add(t)
    nodes = []
    graph = defaultdict(set)
    def snap(p):
        for i,q in enumerate(nodes):
            if dist(p,q)<=tolerance:
                return i
        nodes.append(p)
        return len(nodes)-1
    for (a,b),cut in zip(segments,cuts):
        ids=[snap((a[0]+t*(b[0]-a[0]),a[1]+t*(b[1]-a[1]))) for t in sorted(cut)]
        for i,j in zip(ids,ids[1:]):
            if i!=j:
                graph[i].add(j)
                graph[j].add(i)
    for i, ns in graph.items():
        graph[i] = sorted(ns,key=lambda j: atan2(nodes[j][1]-nodes[i][1],nodes[j][0]-nodes[i][0]))
    used=set()
    out=[]
    for i, ns in graph.items():
        for j in ns:
            chain=[]
            a,b=i,j
            while (a,b) not in used:
                used.add((a,b))
                chain.append(nodes[a])
                turns=graph[b]
                a,b=b,turns[(turns.index(a)-1)%len(turns)]
            if len(chain)<3 or (a,b)!=(i,j):
                continue
            area=sum(cross(p,q) for p,q in zip(chain,chain[1:]+chain[:1]))/2
            if area>0:
                out.append((area,chain))
    return out

def bounds(poly):
    return [min(x for x,y in poly), min(y for x,y in poly), max(x for x,y in poly), max(y for x,y in poly)]

def inside(p,poly):
    x,y=p
    hit=False
    for (ax,ay),(bx,by) in zip(poly,poly[1:]+poly[:1]):
        if (ay>y)!=(by>y) and x < (bx-ax)*(y-ay)/(by-ay)+ax:
            hit=not hit
    return hit


def arrow_clusters(vectors):
    # Both arms meet the long shaft at its tip. The long shafts in one callout share a root.
    at_node = defaultdict(list)
    for a,b,w,c,i in vectors:
        if w < .4 and c==(0.,0.,0.):
            at_node[a].append((b,i))
            at_node[b].append((a,i))
    groups = defaultdict(list)
    for tip, neighbors in at_node.items():
        for root, i in neighbors:
            if dist(tip,root) < 25:
                continue
            arms=[(p,k) for p,k in neighbors if 3 < dist(tip,p) < 25 and
                  dot(delta(tip,root),delta(tip,p))>0]
            if len(arms)!=2:
                continue
            if cross(delta(tip,root),delta(tip,arms[0][0])) * cross(delta(tip,root),delta(tip,arms[1][0])) < 0:
                groups[root].append((tip,i,[k for p,k in arms]))
    return groups


def x_marks(lines, candidates):
    at_node=defaultdict(set)
    for a,b,w,c,i in lines:
        if w < .4 and c==(0.,0.,0.) and dist(a,b)>20:
            key_a=next((p for p in at_node if dist(p,a)<=.75),a)
            at_node[key_a].add(b)
            key_b=next((p for p in at_node if dist(p,b)<=.75),b)
            at_node[key_b].add(a)
    result=[]
    for center,ends in sorted(at_node.items()):
        if len(ends)!=4:continue
        ends=sorted(ends)
        directions=[tuple(v/dist(center,q) for v in delta(center,q)) for q in ends]
        if any(min(dot(a,b) for j,b in enumerate(directions) if j!=i)>-.96 for i,a in enumerate(directions)):
            continue
        sides=[]
        for left in (True,False):
            side=[e for e in ends if (e[0]<center[0])==left]
            if len(side)!=2:break
            sample=((center[0]+sum(a[0] for a in side)/2)/2,
                    (center[1]+sum(a[1] for a in side)/2)/2)
            hits=[c for c in candidates if inside(sample,c['polygon'])]
            if len(hits)!=1:break
            sides.append(hits[0]['id'])
        result.append(dict(center=center,ends=ends,leaf_candidates=sides))
    return result


def extraction(page, paths, r):
    clip=pdf.Rect(r[0]*page.rect.width,r[1]*page.rect.height,r[2]*page.rect.width,r[3]*page.rect.height)
    zoom=1100/clip.width
    pix=page.get_pixmap(matrix=pdf.Matrix(zoom,zoom),clip=clip,alpha=False)
    def point(raw):
        p=raw*page.rotation_matrix
        return p.x*zoom-pix.x,p.y*zoom-pix.y
    v=[]
    for p in paths:
        if p['type'] not in ('s','fs'):
            continue
        if not (p['rect']*page.rotation_matrix+(-.1,-.1,.1,.1)).intersects(clip):
            continue
        for k,*pts in p['items']:
            if k=='l':pairs=[pts[:2]]
            elif k in ('re','qu'):
                q=pts[0]
                corners=[q.tl,q.tr,q.br,q.bl] if k=='re' else [q.ul,q.ur,q.lr,q.ll]
                pairs=list(zip(corners,corners[1:]+corners[:1]))
            else:continue
            for a,b in pairs:
                a,b=point(a),point(b)
                if a==b or max(a[0],b[0])<-2 or min(a[0],b[0])>pix.width+2 or max(a[1],b[1])<-2 or min(a[1],b[1])>pix.height+2:
                    continue
                v.append((a,b,p['width'] or 0,p['color'],p['seqno']))
    return pix, v


def extract_islands(source_pdf, detection, geometry, key):
    """Produce geometry without labels, expected groups, or prior Analyze outputs."""
    crop_dir = geometry / "full"
    crop_dir.mkdir(parents=True)
    views, paths_by_page = [], {}
    islands = [(obj["object_id"], island) for obj in detection["objects"] for island in obj["islands"]]
    ordered = sorted(islands, key=lambda pair: (pair[1]["page_number"], pair[1]["island_id"]))
    with pdf.open(source_pdf) as document:
        for object_id, island in ordered:
            frame = island["coordinate_frame_pixels"]
            coords = [island["bbox"][name] for name in
                      ("top_left_x", "top_left_y", "bottom_right_x", "bottom_right_y")]
            crop = [value / frame[i % 2] for i, value in enumerate(coords)]
            if not (0 <= crop[0] < crop[2] <= 1 and 0 <= crop[1] < crop[3] <= 1):
                raise ValueError(f"Invalid Detection crop for {island['island_id']}")
            page_number = island["page_number"]
            page = document[page_number - 1]
            if page_number not in paths_by_page:
                paths_by_page[page_number] = page.get_drawings()
            pixels, lines = extraction(page, paths_by_page[page_number], crop)
            number = len(views) + 1
            pixels.save(crop_dir / f"{key}-{number:02}.png")
            segments = [(a, b) for a, b, width, color, _ in lines if width >= .65 and color == (0., 0., 0.)]
            faces = [(area, polygon) for area, polygon in planar_faces(segments, .75) if area >= 500
                     and all(-2 <= x <= pixels.width + 2 and -2 <= y <= pixels.height + 2 for x, y in polygon)]
            faces.sort(key=lambda row: (bounds(row[1])[1], bounds(row[1])[0], row[0]))
            candidates = [{"id": f"C{i:02}", "area": round(area, 1), "polygon": polygon, "bbox": bounds(polygon)}
                          for i, (area, polygon) in enumerate(faces, 1)]
            leaders = [
                {"root": root, "tips": [{"xy": tip, "path": path,
                    "hits": [face["id"] for face in candidates if inside(tip, face["polygon"])]}
                    for tip, path, _ in sorted(group)]}
                for root, group in sorted(arrow_clusters(lines).items())
                if 0 <= root[0] <= pixels.width and 0 <= root[1] <= pixels.height
            ]
            views.append({"view_id": island["island_id"], "object_id": object_id,
                          "bbox_normalized": crop, "coordinate_frame_pixels": frame, "page": page_number,
                          "number": number, "width": pixels.width, "height": pixels.height,
                          "candidates": candidates, "arrows": leaders, "x_marks": x_marks(lines, candidates)})
    (geometry / "estimation-offline-all-islands-evidence.json").write_text(json.dumps({
        "model_calls": 0, "source_sha256": {key: sha256(source_pdf.read_bytes()).hexdigest()},
        "snap_tolerance_px": .75, "min_contour_area_px2": 500, "documents": {key: views},
    }, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
