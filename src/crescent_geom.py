"""v11 crown geometry shared by build.py and the clearance search (pure python, no bpy).
One crescent: centreline = elliptical arc (semi-axes A horizontal-in-plane, B vertical) in a plane yawed `theta` about Z
(in-plane axis e from the bulge side toward the tip side), optionally leaning `alpha` about e.
The arc runs from the ROOT angle ph_root (inside the tower) round the back (180 deg, the bulge) to the TIP angle ph_tip.
In-plane half-width: smooth taper w(t) = w_max * sin(pi*t^q)^p-shaped profile peaking at t_peak, 0 at the tip,
plus a root flare (the plate widens and thickens where it grows out of the tower)."""
import math

def frame(SG):
    th, al = math.radians(SG["theta"]), math.radians(SG.get("alpha", 0.0))
    e = (math.cos(th), math.sin(th), 0.0); w = (-e[1], e[0], 0.0)
    v = (w[0]*math.sin(al), w[1]*math.sin(al), math.cos(al))
    n = (e[1]*v[2] - e[2]*v[1], e[2]*v[0] - e[0]*v[2], e[0]*v[1] - e[1]*v[0])   # plate normal = e x v
    return e, v, n

def half_width(SG, t):
    tp = SG.get("t_peak", 0.35); wm = SG["w_max"]/2; w0 = SG.get("w_root", SG["w_max"]*0.8)/2
    if t <= tp:
        s = t/tp; base = w0 + (wm - w0)*(0.5 - 0.5*math.cos(math.pi*s))
    else:
        s = (t - tp)/(1 - tp); base = wm*(math.cos(0.5*math.pi*s))**SG.get("tip_p", 1.15)
    return base*(1 + SG.get("flare", 0.8)*math.exp(-t/SG.get("flare_t", 0.05)))

def half_thick(SG, t):
    return SG.get("thick", 1.3)/2*(1 + SG.get("flare_th", 1.2)*math.exp(-t/SG.get("flare_t", 0.05)))

def centreline(SG, TC, N=240):
    e, v, n = frame(SG)
    C0 = (TC[0] + SG["cx_off"], TC[1] + SG["dy"], SG["zc"])
    a0 = math.radians(SG["ph_root"]); a1 = math.radians(SG["ph_tip"])
    while a1 >= a0: a1 -= 2*math.pi          # run root (e.g. -90) -> back (-180 = the bulge, -e side) -> tip (e.g. 30-360)
    A, B = SG["A"], SG["B"]
    pts = []
    for k in range(N + 1):
        t = k/N; a = a0 + (a1 - a0)*t
        s, z = A*math.cos(a), B*math.sin(a)
        pts.append(tuple(C0[i] + e[i]*s + v[i]*z for i in range(3)))
    return pts, e, v, n

def edges(SG, TC, N=120):
    """sample points on the plate (centre + both in-plane edges) for clearance checks"""
    pts, e, v, n = centreline(SG, TC, N)
    out = []
    for k, p in enumerate(pts):
        t = k/N
        q = pts[min(k + 1, N)]; r = pts[max(k - 1, 0)]
        T = [q[i] - r[i] for i in range(3)]; L = math.sqrt(sum(c*c for c in T)) or 1; T = [c/L for c in T]
        U = (n[1]*T[2] - n[2]*T[1], n[2]*T[0] - n[0]*T[2], n[0]*T[1] - n[1]*T[0])
        hw = half_width(SG, t)
        for g in (-1, -0.5, 0, 0.5, 1):
            out.append(tuple(p[i] + U[i]*hw*g for i in range(3)))
    return out, pts[0], pts[-1]
