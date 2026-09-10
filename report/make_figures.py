"""Writes figures/plant.svg, the plant diagram of Section 3.1 (hand-authored; checked against contract v3.9 §B and the
report's Section 4.4 equations on 10 September 2026). Usage: python3 make_figures.py"""
import pathlib
W, H = 760, 360
def node(x, y, w, h, label, sub="", fill="#ffffff"):
    s = f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{fill}" stroke="#222" stroke-width="1.2"/>'
    s += f'<text x="{x+w/2}" y="{y+h/2+(0 if sub else 5)}" text-anchor="middle" font-size="14" font-weight="600">{label}</text>'
    if sub: s += f'<text x="{x+w/2}" y="{y+h/2+16}" text-anchor="middle" font-size="10.5" fill="#333">{sub}</text>'
    return s
def edge(x1, y1, x2, y2, label="", dashed=False, color="#222", lx=None, ly=None, curve=None, anchor="middle"):
    d = ' stroke-dasharray="6,4"' if dashed else ""
    path = f'M{x1},{y1} L{x2},{y2}' if curve is None else f'M{x1},{y1} Q{curve[0]},{curve[1]} {x2},{y2}'
    s = f'<path d="{path}" fill="none" stroke="{color}" stroke-width="1.4"{d} marker-end="url(#arr)"/>'
    if label:
        lx = lx if lx is not None else (x1+x2)/2; ly = ly if ly is not None else (y1+y2)/2 - 6
        s += f'<text x="{lx}" y="{ly}" text-anchor="{anchor}" font-size="11" fill="{color}">{label}</text>'
    return s
p = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {W} {H}" style="max-width:100%;height:auto" font-family="Charter, Georgia, serif">',
     '<defs><marker id="arr" markerWidth="8" markerHeight="8" refX="7" refY="4" orient="auto"><path d="M0,0 L8,4 L0,8 z" fill="#222"/></marker></defs>']
# nodes: row 1 (y=50): a, b, d ; u at left middle ; row 2 (y=210): x, w
p.append(node(30, 130, 120, 46, "u", "context, AR(1), latent"))
p.append(node(220, 50, 90, 46, "a", "actions, K = 2"))
p.append(node(400, 50, 90, 46, "b", "body, 4"))
p.append(node(570, 50, 100, 46, "d", "downstream, 2"))
p.append(node(200, 210, 150, 46, "x", "distractors, 10 or 30", fill="#f6f6f6"))
p.append(node(570, 210, 100, 46, "w", "world, 4"))
# action noise (instrument) into a
p.append('<text x="200" y="22" text-anchor="middle" font-size="11.5">ε<tspan baseline-shift="super" font-size="8">a</tspan> action noise (the instrument of Section 4.4)</text>')
p.append(edge(200, 28, 250, 50, color="#444"))
# structural edges
p.append(edge(150, 148, 222, 80, "W_u", lx=172, ly=104))                          # u -> a
p.append(edge(150, 160, 222, 222, "G_x, to half of x", lx=150, ly=205, anchor="start"))   # u -> half of x
p.append(edge(310, 73, 398, 73, "B, delay τ", ly=45))                             # a -> b
p.append(edge(490, 73, 568, 73, "C_d", ly=64))                                    # b -> d
# event mark on a -> b
p.append('<line x1="349" y1="63" x2="361" y2="83" stroke="#a00" stroke-width="2"/><line x1="361" y1="63" x2="349" y2="83" stroke="#a00" stroke-width="2"/>')
p.append('<text x="355" y="34" text-anchor="middle" font-size="10.5" fill="#a00">event: column 0 of B set to zero</text>')
# feedback edge below the row: b bottom -> a bottom
p.append(edge(430, 96, 280, 96, "W_o feedback, reads the body channels", dashed=True, color="#555", lx=355, ly=140, curve=(355, 135)))
# option-C dashed red edge: u -> b, routed under the feedback
p.append(edge(150, 170, 420, 96, "G_b: body-confounded plant of Section 4.4 only, never built", dashed=True, color="#a00", lx=330, ly=200, curve=(300, 185)))
# observation layer
p.append('<rect x="30" y="292" width="700" height="46" rx="6" fill="#eef3f8" stroke="#222" stroke-width="1.2"/>')
p.append('<text x="380" y="311" text-anchor="middle" font-size="12" font-weight="600">o = [b, d, w, x, four padding channels] + ε<tspan baseline-shift="super" font-size="8">o</tspan>    (observation layer; all channels noisy; the estimators see o and a only)</text>')
p.append('<text x="380" y="328" text-anchor="middle" font-size="10.5" fill="#333">pre-event support = the b and d channels (b only at delay 2); confounded channels = half of x; the two sets are disjoint</text>')
p.append(edge(445, 96, 445, 290, color="#888"))     # b -> o
p.append(edge(640, 96, 640, 208, color="#888"))     # d -> o passes to w? no: d -> o at x=640 must avoid w; route at x=690
p[-1] = edge(660, 96, 700, 290, color="#888")
p.append(edge(620, 256, 620, 290, color="#888"))    # w -> o
p.append(edge(275, 256, 275, 290, color="#888"))    # x -> o
p.append('</svg>')
pathlib.Path(__file__).with_name("figures").joinpath("plant.svg").write_text("\n".join(p))
print("figures/plant.svg written")
