"""Derive a weight-only, blockier font from Inter's sources.

- Drops Inter's optical-size axis (keeps the text-size masters: Thin, Regular, Black).
- Lowers the lowercase x-height (ascenders and descenders stay put).
- Widens letter shapes per group (straight, round, diagonal, ...).
- Tightens sidebearings and word spaces.
- Optionally makes a master heavier (weight_v / weight_h), e.g. a Regular with
  thicker, less contrasted stems.
- Per-glyph ink factors in "ink" override the group defaults (tools/fit.py
  fills these from the mockup).
- All scaling is weight-compensated: coordinates come from a slightly lighter
  (x) or heavier (y) interpolation so stems keep their original thickness.

Usage: python tools/derive.py <Inter-Roman.glyphspackage> <out.glyphspackage> [params.json]
"""

import json
import sys

import glyphsLib
from glyphsLib.types import Point, Transform

PARAMS = {
    "family": "Placeholder Sans",
    "xheight": 0.96,      # lowercase x-height factor
    "spacing": 0.82,      # positive sidebearings factor (lowercase and others)
    "spacing_upper": 0.82,  # positive sidebearings factor (capitals)
    "xh_overshoot": 25,   # lowercase overshoot above the new x-height
    "weight_v": {},       # per-master vertical stem factor, e.g. {"Regular": 1.07}
    "weight_h": {},       # per-master horizontal stem factor
    "weight_v_lower": {}, # per-master vertical stem factor for lowercase (default: weight_v)
    "ink": {},            # per-glyph ink factor overrides
    "sb": {},             # per-glyph [left, right] sidebearing adjustments in units
    "masters": {},        # per-master overrides of the keys above, e.g. {"Thin": {"ink": {...}}}
    "space": 0.85,        # whitespace width factor
    # ink-width factors (applied to the weight-compensated outline)
    "lower": 1.01,
    "lower_round": 1.03,
    "lower_diagonal": 1.045,
    "lower_xz": 1.08,
    "lower_tr": 1.14,
    "upper": 1.03,
    "upper_round": 1.06,
    "upper_diagonal": 1.06,
    "figures": 1.03,
    "other": 1.0,
}

LOWER_ROUND = {"o", "c", "b", "d", "p", "q", "g", "a.1", "a.2"}
LOWER_DIAGONAL = {"v", "w", "y"}
LOWER_XZ = {"x", "z"}
LOWER_TR = {"t", "r"}
UPPER_ROUND = {"O", "Q", "C", "G", "G.1", "D"}
UPPER_DIAGONAL = {"A", "V", "W", "X", "Y", "K"}
SKIP_SUFFIXES = {"sups", "subs", "sinf", "numr", "dnom", "sc", "circled", "squared"}

XHEIGHT = 1118
ASCENDER = 1490
V_STEMS = {"Thin": 46, "Regular": 190, "Black": 404}   # width of "I"
H_STEMS = {"Thin": 46, "Regular": 168, "Black": 326}   # "E" arm thickness


def compensation(masters, stems, s, boost):
    """For each master: (layer A id, layer B id, f) whose mix has stem = stem * boost / s."""
    order = sorted(masters, key=lambda m: m.axes[0])
    values = [stems[m.name] for m in order]
    out = {}
    for i, m in enumerate(order):
        target = values[i] * boost.get(m.name, 1.0) / s
        lighter = target < values[i]
        j = i - 1 if lighter else i + 1
        if j < 0 or j >= len(order):
            j = i + 1 if j < 0 else i - 1
        lo, hi = min(i, j), max(i, j)
        f = (target - values[lo]) / (values[hi] - values[lo])
        out[m.id] = (order[lo].id, order[hi].id, f)
    return out


def mix(a, b, f):
    return a + (b - a) * f


def main(src, dst, params_path=None):
    P = dict(PARAMS)
    if params_path:
        P.update(json.load(open(params_path)))
    K = P["xheight"]

    # Lowercase vertical remap: baseline fixed, x-height lowered, Inter's 14-unit
    # top overshoot widened to xh_overshoot, ascender fixed.
    YMAP = [(0, 0), (XHEIGHT, K * XHEIGHT), (XHEIGHT + 14, K * XHEIGHT + P["xh_overshoot"]),
            (ASCENDER, ASCENDER)]

    def ymap(y):
        if y <= 0 or y >= ASCENDER:
            return y
        for (a, fa), (b, fb) in zip(YMAP, YMAP[1:]):
            if y <= b:
                return fa + (y - a) * (fb - fa) / (b - a)
        return y

    font = glyphsLib.GSFont(src)

    # --- Drop the optical-size axis -------------------------------------
    drop = {m.id for m in font.masters if m.axes[0] != 14}
    font.masters = [m for m in font.masters if m.axes[0] == 14]
    for m in font.masters:
        m.axes = [m.axes[1]]
        for cp in m.customParameters:
            if cp.name == "Axis Location":
                cp.value = [loc for loc in cp.value if loc["Axis"] != "Optical size"]
    font.axes = [a for a in font.axes if a.axisTag != "opsz"]
    font.instances = [i for i in font.instances if i.axes[0] == 14]
    for inst in font.instances:
        inst.axes = [inst.axes[1]]
    for cp in font.customParameters:
        if cp.name == "Axis Mappings":
            cp.value = {k: v for k, v in cp.value.items() if k != "opsz"}
    for mid in list(font.kerningLTR.keys()):
        if mid in drop:
            del font.kerningLTR[mid]
    for glyph in font.glyphs:
        for layer in list(glyph.layers):
            if layer.associatedMasterId in drop:
                del glyph.layers[layer.layerId]

    font.familyName = P["family"]
    for m in font.masters:
        m.xHeight = round(XHEIGHT * K)

    # --- Classify -------------------------------------------------------
    glyphs = {g.name: g for g in font.glyphs}
    mids = [m.id for m in font.masters]
    reg = mids[1]

    def char_of(name):
        base = name.split(".")[0].split("_")[0]
        g = glyphs.get(base)
        return chr(int(g.unicode, 16)) if g is not None and g.unicode else ""

    def suffixes(name):
        return set(name.split(".")[1:])

    def is_mark(name):
        # Zero-width glyphs (combining marks and the like) are left untouched.
        g = glyphs.get(name)
        return g is not None and g.layers[reg].width == 0

    def is_lower(name):
        return char_of(name).islower() and not (suffixes(name) & SKIP_SUFFIXES)

    def is_tabular(name):
        return "tf" in suffixes(name)

    master_name = {m.id: m.name for m in font.masters}

    def opt(key, mid):
        """A parameter for one master: its override if it has one, else the global value."""
        return P["masters"].get(master_name[mid], {}).get(key, P[key])

    def per_glyph(key, name, mid, default):
        own = P["masters"].get(master_name[mid], {}).get(key, {})
        return own[name] if name in own else P[key].get(name, default)

    def ink_factor(name, mid):
        f = per_glyph("ink", name, mid, None)
        if f is not None:
            return f
        P_ = {k: opt(k, mid) for k in ("lower", "lower_round", "lower_diagonal", "lower_xz",
                                       "lower_tr", "upper", "upper_round", "upper_diagonal",
                                       "figures", "other")}
        return group_factor(name, P_)

    def group_factor(name, P):
        if suffixes(name) & SKIP_SUFFIXES:
            return P["other"]
        key = name.split(".ss")[0].split(".cv")[0]
        ch = char_of(name)
        if key in LOWER_ROUND or name.split(".")[0] in LOWER_ROUND - {"a.1", "a.2"}:
            return P["lower_round"]
        if name.split(".")[0] in LOWER_DIAGONAL:
            return P["lower_diagonal"]
        if name.split(".")[0] in LOWER_XZ:
            return P["lower_xz"]
        if name.split(".")[0] in LOWER_TR:
            return P["lower_tr"]
        if key in UPPER_ROUND or name.split(".")[0] in UPPER_ROUND:
            return P["upper_round"]
        if name.split(".")[0] in UPPER_DIAGONAL:
            return P["upper_diagonal"]
        if ch.islower():
            return P["lower"]
        if ch.isupper():
            return P["upper"]
        if ch.isdigit():
            return P["figures"]
        return P["other"]

    plans_x, plans_y = {}, {}

    def plan_x(s, lower):
        if (s, lower) not in plans_x:
            boost = {**P["weight_v"], **P["weight_v_lower"]} if lower else P["weight_v"]
            plans_x[(s, lower)] = compensation(font.masters, V_STEMS, s, boost)
        return plans_x[(s, lower)]

    def plan_y(lower):
        if lower not in plans_y:
            plans_y[lower] = compensation(font.masters, H_STEMS, K if lower else 1.0, P["weight_h"])
        return plans_y[lower]

    def compatible(g):
        return len({
            (tuple(len(p.nodes) for p in g.layers[m].paths), len(g.layers[m].components),
             tuple(sorted(a.name for a in g.layers[m].anchors)))
            for m in mids
        }) == 1

    def mixed_coords(g, mid, s, lower):
        """Weight-compensated node and anchor coordinates for one master layer."""
        ok = compatible(g)
        ax, bx, fx = plan_x(s, lower)[mid] if ok else (mid, mid, 0)
        ay, by, fy = plan_y(lower)[mid] if (ok and (lower or P["weight_h"])) else (mid, mid, 0)
        LA, LB, MA, MB = g.layers[ax], g.layers[bx], g.layers[ay], g.layers[by]
        nodes = [
            [(mix(n1.position.x, n2.position.x, fx), mix(n3.position.y, n4.position.y, fy))
             for n1, n2, n3, n4 in zip(p1.nodes, p2.nodes, p3.nodes, p4.nodes)]
            for p1, p2, p3, p4 in zip(LA.paths, LB.paths, MA.paths, MB.paths)
        ]
        def anchor(layer, name):
            return next(a for a in layer.anchors if a.name == name)
        anchors = {
            a.name: (mix(anchor(LA, a.name).position.x, anchor(LB, a.name).position.x, fx),
                     mix(anchor(MA, a.name).position.y, anchor(MB, a.name).position.y, fy))
            for a in g.layers[mid].anchors
        }
        return nodes, anchors

    def oncurve_extent(layer):
        xs = [n.position.x for p in layer.paths for n in p.nodes if n.type != "offcurve"]
        return (min(xs), max(xs)) if xs else None

    # result[(name, mid)] = dict(width, old_width, L_old, L_new, s, anchors_old, anchors_new)
    result = {}

    def sb(v, name, mid):
        factor = opt("spacing_upper" if char_of(name).isupper() else "spacing", mid)
        return v * factor if v > 0 else v

    def process(name):
        g = glyphs[name]
        if (name, mids[0]) in result:
            return
        for c in g.layers[reg].components:
            if c.name in glyphs:
                process(c.name)
        lower = is_lower(name)
        # Read every master before changing any: the mixes look across masters.
        pre = {}
        if not is_mark(name) and g.layers[reg].paths:
            base_reg = next((c for c in g.layers[reg].components if not is_mark(c.name) and c.name in glyphs), None)
            s_of = (lambda mid: ink_factor(name, mid)) if base_reg is None else \
                   (lambda mid: result[(base_reg.name, mid)]["s"])
            pre = {mid: mixed_coords(g, mid, s_of(mid), lower) for mid in mids}
        for mid in mids:
            layer = g.layers[mid]
            old_w = layer.width
            old_anchors = {a.name: (a.position.x, a.position.y) for a in layer.anchors}
            info = {"old_width": old_w, "anchors_old": old_anchors, "lower": lower}
            base = next((c for c in layer.components if not is_mark(c.name) and c.name in glyphs), None)

            if is_mark(name):
                info.update(width=old_w, anchors_new=old_anchors, L_old=0, L_new=0, s=1.0)
                result[(name, mid)] = info
                continue

            if base is None:
                # Simple glyph (paths only, or paths + marks, or whitespace).
                s = ink_factor(name, mid)
                ext = oncurve_extent(layer)
                if ext is None:
                    w = old_w * opt("space", mid) if not layer.components else old_w
                    layer.width = round(w)
                    info.update(width=w, anchors_new=old_anchors, L_old=0, L_new=0, s=1.0)
                    result[(name, mid)] = info
                    continue
                nodes, anchors = pre[mid]
                mxs = [x for p, pth in zip(nodes, layer.paths) for (x, _), n in zip(p, pth.nodes) if n.type != "offcurve"]
                mL, mR = min(mxs), max(mxs)
                L_old, R_old = ext
                ink_w = s * (mR - mL)
                if is_tabular(name):
                    L_new = L_old + ((R_old - L_old) - ink_w) / 2
                    w = old_w
                else:
                    dL, dR = per_glyph("sb", name, mid, (0, 0))
                    L_new = sb(L_old, name, mid) + dL
                    w = L_new + ink_w + sb(old_w - R_old, name, mid) + dR
                fx = lambda x: L_new + s * (x - mL)
                fy = ymap if lower else (lambda y: y)
                for pth, pts in zip(layer.paths, nodes):
                    for n, (x, y) in zip(pth.nodes, pts):
                        n.position = Point(round(fx(x)), round(fy(y)))
                new_anchors = {k: (fx(x), fy(y)) for k, (x, y) in anchors.items()}
                for a in layer.anchors:
                    a.position = Point(round(new_anchors[a.name][0]), round(new_anchors[a.name][1]))
                layer.width = round(w)
                info.update(width=w, anchors_new=new_anchors, L_old=L_old, L_new=L_new, s=s)
                # marks inside a paths glyph follow its anchors
                shift_marks(layer, mid, info, base_comp=None)
                result[(name, mid)] = info
                continue

            # Composite (possibly with extra paths): follow the base component.
            b = result[(base.name, mid)]
            s = b["s"]
            D = 0.0
            for c in layer.components:
                if is_mark(c.name) or c.name not in glyphs:
                    continue
                r = result[(c.name, mid)]
                delta = r["width"] - r["old_width"]
                a, _, _, d, tx, ty = c.transform
                tx_new = tx + D + (delta if a < 0 else 0)
                ty_new = ymap(ty) if (lower and d < 0) else ty
                c.transform = Transform(a, c.transform[1], c.transform[2], d, round(tx_new), round(ty_new))
                D += delta
            w = old_w + D
            fx = lambda x: b["L_new"] + s * (x - b["L_old"])
            fy = ymap if lower else (lambda y: y)
            if layer.paths:
                nodes, _ = pre[mid]
                for pth, pts in zip(layer.paths, nodes):
                    for n, (x, y) in zip(pth.nodes, pts):
                        n.position = Point(round(fx(x)), round(fy(y)))
            new_anchors = {}
            for k, (x, y) in old_anchors.items():
                d = anchor_delta(base, mid, k)
                new_anchors[k] = (x + d[0], y + d[1]) if d else (fx(x), fy(y))
            for an in layer.anchors:
                an.position = Point(round(new_anchors[an.name][0]), round(new_anchors[an.name][1]))
            layer.width = round(w)
            info.update(width=w, anchors_new=new_anchors, L_old=b["L_old"], L_new=b["L_new"], s=s)
            shift_marks(layer, mid, info, base_comp=base)
            result[(name, mid)] = info

    def anchor_delta(comp, mid, name):
        """How far anchor `name` of a placed component moved, in the parent's coordinates."""
        r = result.get((comp.name, mid))
        if r is None:
            return None
        a, _, _, d = comp.transform[:4]
        if name in r["anchors_old"]:
            ox, oy = r["anchors_old"][name]
            nx, ny = r["anchors_new"][name]
            return (a * (nx - ox) + (r["width"] - r["old_width"] if a < 0 else 0), d * (ny - oy))
        # anchor propagated from the component's own base
        sub = next((c for c in glyphs[comp.name].layers[mid].components if not is_mark(c.name)), None)
        if sub is not None:
            inner = anchor_delta(sub, mid, name)
            if inner:
                return (a * inner[0] + (r["width"] - r["old_width"] if a < 0 else 0), d * inner[1])
        return None

    def shift_marks(layer, mid, info, base_comp):
        last = (0.0, 0.0)
        for c in layer.components:
            if not is_mark(c.name):
                continue
            mark = glyphs[c.name].layers[mid]
            attach = next((an.name[1:] for an in mark.anchors if an.name.startswith("_")), None)
            dlt = None
            if attach:
                if base_comp is None:
                    if attach in info["anchors_old"]:
                        ox, oy = info["anchors_old"][attach]
                        nx, ny = info["anchors_new"][attach]
                        dlt = (nx - ox, ny - oy)
                else:
                    dlt = anchor_delta(base_comp, mid, attach)
            if dlt is None:
                dlt = last  # stacked mark: follow the mark below it
            t = list(c.transform)
            t[4] = round(t[4] + dlt[0])
            t[5] = round(t[5] + dlt[1])
            c.transform = Transform(*t)
            last = dlt

    for g in font.glyphs:
        process(g.name)

    font.save(dst)
    print(f"saved {dst}")
    bad = [g.name for g in font.glyphs if not compatible(g)]
    if bad:
        print(f"{len(bad)} glyphs not compatible across masters (no stem compensation):", " ".join(bad[:30]))


if __name__ == "__main__":
    main(*sys.argv[1:4])
