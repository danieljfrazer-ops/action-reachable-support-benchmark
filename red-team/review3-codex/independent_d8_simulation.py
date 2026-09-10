"""Independent simulation for the D-8 review.

This file was written from the frozen contract v3.3 and sequential-IBD draft 2.
It does not import or read review-ibd-spec/sim_ibd_review.py.

The CUSUM support output is necessarily an explicit interpretation because the
frozen text does not define its per-channel innovation-to-support statistic.
Here it is baseline observational action sensitivity minus a two-sided
standardised innovation shift, followed by the same *protocol* (not the same
fitted knots) of isotonic calibration used for sequential IBD.
"""
from __future__ import annotations

import argparse
import csv
import json
import math
from dataclasses import dataclass
from pathlib import Path

import numpy as np


HSET = (1, 2, 3)
EVENT_T = 1000
T = 2000
PI = 20
W = 500
N_MIN = 10
ZCAP = 8.0
P_EPOCH = 3
OFFSETS = (200, 500, 1000)


def pava_fit(x: np.ndarray, y: np.ndarray):
    order = np.argsort(x, kind="mergesort")
    xs, ys = x[order], y[order]
    # Aggregate exact ties before PAVA.
    ux, inv = np.unique(xs, return_inverse=True)
    sy = np.bincount(inv, weights=ys)
    sw = np.bincount(inv).astype(float)
    means = sy / sw
    blocks = []
    for i, (m, wt) in enumerate(zip(means, sw)):
        blocks.append([i, i, float(wt), float(m)])
        while len(blocks) >= 2 and blocks[-2][3] > blocks[-1][3]:
            b = blocks.pop(); a = blocks.pop()
            wt2 = a[2] + b[2]
            blocks.append([a[0], b[1], wt2, (a[2] * a[3] + b[2] * b[3]) / wt2])
    vals = np.empty(len(ux))
    for lo, hi, _, m in blocks:
        vals[lo:hi + 1] = m
    return ux, vals


def pava_predict(model, x):
    knots, vals = model
    idx = np.searchsorted(knots, x, side="right") - 1
    idx = np.clip(idx, 0, len(vals) - 1)
    return vals[idx]


def rank_z(a: np.ndarray, b: np.ndarray) -> float:
    """Mann-Whitney z with average ranks and the usual tie correction."""
    n1, n2 = len(a), len(b)
    v = np.concatenate([a, b])
    order = np.argsort(v, kind="mergesort")
    ranks = np.empty(len(v), float)
    ties = []
    i = 0
    while i < len(v):
        j = i + 1
        while j < len(v) and v[order[j]] == v[order[i]]:
            j += 1
        ranks[order[i:j]] = 0.5 * (i + 1 + j)
        ties.append(j - i)
        i = j
    u = ranks[:n1].sum() - n1 * (n1 + 1) / 2
    n = n1 + n2
    tie_factor = 1.0 - sum(q**3 - q for q in ties) / (n**3 - n) if n > 1 else 0.0
    var = n1 * n2 * (n + 1) * tie_factor / 12.0
    if var <= 0:
        return -ZCAP
    return float(np.clip((u - n1 * n2 / 2) / math.sqrt(var), -ZCAP, ZCAP))


@dataclass
class Instance:
    A: np.ndarray
    B: np.ndarray
    Ad: np.ndarray
    Cd: np.ndarray
    Aw: np.ndarray
    Ax: np.ndarray
    G: np.ndarray
    Wo: np.ndarray
    Wu: np.ndarray
    support_pre: np.ndarray
    support_post: np.ndarray
    conf_mask: np.ndarray


def make_instance(nx=10):
    A = np.array([[.62, 0, 0, 0], [0, .62, 0, 0], [.24, 0, .55, 0], [0, .24, 0, .55]])
    B = np.array([[.35, 0], [0, .35], [0, 0], [0, 0]])
    Ad = np.diag([.55, .55]); Cd = np.array([[.25, 0, 0, 0], [0, .25, 0, 0]])
    Aw = np.eye(4) * .70; Ax = np.eye(nx) * .80
    G = np.zeros((nx, 1)); G[: nx // 2, 0] = np.linspace(.35, .55, nx // 2)
    c = 4 + 2 + 4 + nx + 4  # four assigned-empty padding channels, matching the CSV channel count
    Wo = np.zeros((2, c)); Wo[0, 0] = -.18; Wo[1, 1] = -.18
    Wu = np.array([[.45], [-.40]])
    pre = np.zeros(c, bool); pre[:6] = True
    post = np.zeros(c, bool); post[[1, 3, 5]] = True
    conf = np.zeros(c, bool); conf[10:10 + nx // 2] = True
    return Instance(A, B, Ad, Cd, Aw, Ax, G, Wo, Wu, pre, post, conf)


def noises(seed, nx):
    rng = np.random.default_rng(seed)
    return dict(u=rng.normal(size=(T + 1, 1)), b=.1*rng.normal(size=(T + 1, 4)),
                d=.1*rng.normal(size=(T + 1, 2)), w=.1*rng.normal(size=(T + 1, 4)),
                x=.1*rng.normal(size=(T + 1, nx)), a=.1*rng.normal(size=(T + 1, 2)),
                o=.05*rng.normal(size=(T + 1, 14 + nx)),
                probe=rng.integers(0, 4, size=T + 1))


def simulate(inst: Instance, seed: int, event: bool, probed: bool):
    nx = inst.Ax.shape[0]; nz = noises(seed, nx)
    b=np.zeros((T+1,4)); d=np.zeros((T+1,2)); w=np.zeros((T+1,4)); x=np.zeros((T+1,nx)); u=np.zeros((T+1,1))
    o=np.zeros((T+1,14+nx)); a=np.zeros((T,2)); probe=np.zeros(T,bool)
    for t in range(T):
        u[t] = .8 * (u[t-1] if t else 0) + nz['u'][t]
        o[t] = np.concatenate([b[t],d[t],w[t],x[t],np.zeros(4)]) + nz['o'][t]
        act = np.clip(inst.Wo @ o[t] + inst.Wu @ u[t] + nz['a'][t], -2, 2)
        if probed and t > 0 and t % PI == 0 and t <= T-3:
            k = nz['probe'][t] // 2; sign = 1 if nz['probe'][t] % 2 == 0 else -1
            act = np.zeros(2); act[k] = sign; probe[t] = True
        a[t] = act
        Bt = inst.B.copy()
        if event and t >= EVENT_T: Bt[:,0] = 0
        b[t+1] = inst.A@b[t] + Bt@act + nz['b'][t]
        d[t+1] = inst.Ad@d[t] + inst.Cd@b[t] + nz['d'][t]
        w[t+1] = inst.Aw@w[t] + nz['w'][t]
        x[t+1] = inst.Ax@x[t] + inst.G@u[t] + nz['x'][t]
    o[T] = np.concatenate([b[T],d[T],w[T],x[T],np.zeros(4)]) + nz['o'][T]
    return o, a, probe


def ibd_trace(o, probe):
    c=o.shape[1]; times=np.flatnonzero(probe)
    out_t=[]; out=[]
    for now in times:
        if now + 3 > T: continue
        active=times[(times <= now) & (times > now+3-W)]
        active=active[active >= 13]
        if len(active) < N_MIN:
            out.append(np.zeros(c)); out_t.append(now+3); continue
        z=np.empty((len(HSET),c))
        for hi,h in enumerate(HSET):
            pv=np.abs(o[active+h]-o[active])
            nv=np.concatenate([np.abs(o[active-3*m+h]-o[active-3*m]) for m in range(1,5)],axis=0)
            for ch in range(c): z[hi,ch]=rank_z(pv[:,ch],nv[:,ch])
        pick=np.argmax(np.abs(z),axis=0)
        out.append(z[pick,np.arange(c)]); out_t.append(now+3)
    return np.asarray(out_t),np.asarray(out)


def fit_predictor(inst, seeds=range(7000,7010)):
    X=[]; Y=[]
    for s in seeds:
        o,a,_=simulate(inst,s,event=False,probed=False)
        X.append(np.column_stack([o[:-1],a,np.ones(T)])); Y.append(o[1:])
    X=np.concatenate(X);Y=np.concatenate(Y)
    coef=np.linalg.lstsq(X,Y,rcond=None)[0]
    pred=X@coef; sd=np.maximum((Y-pred).std(0),1e-3)
    action_sens=np.linalg.norm(coef[-3:-1,:],axis=0)/sd
    return coef,sd,action_sens


def cusum_support_trace(o,a,model,mode="two_sided"):
    coef,sd,sens=model; X=np.column_stack([o[:-1],a,np.ones(T)])
    res=(o[1:]-X@coef)/sd
    ts=np.arange(203,T+1,PI); vals=[]
    for now in ts:
        recent=res[max(0,now-100):now]
        if mode == "two_sided":
            # Two-sided channel innovation change penalty.
            change=np.abs(recent.mean(0)) + np.abs(np.log(np.maximum(recent.std(0),1e-3)))
            raw=sens-change
        elif mode == "signed_alignment":
            # Innovation aligned with the predictor's action contribution.  A
            # lost actuator produces residual ~= -q and drives the estimated
            # retained action sensitivity toward zero; shared-cause x can keep
            # a spurious fitted action coefficient.
            qa=(a[max(0,now-100):now] @ coef[-3:-1,:]) / sd
            den=np.maximum(np.mean(qa*qa,axis=0),1e-6)
            retained=1.0 + np.mean(recent*qa,axis=0)/den
            raw=sens*np.clip(retained,-1,2)
        else: raise ValueError(mode)
        vals.append(np.clip(raw,-ZCAP,ZCAP))
    return ts,np.asarray(vals)


def label_at(inst,t,event):
    return inst.support_post if event and t > EVENT_T else inst.support_pre


def value_at(ts,trace,t):
    i=np.searchsorted(ts,t,side='right')-1
    return trace[max(i,0)]


def f1(pred,y):
    tp=np.sum(pred & y); fp=np.sum(pred & ~y); fn=np.sum(~pred & y)
    return float(2*tp/(2*tp+fp+fn)) if 2*tp+fp+fn else 1.0


def calibrate_maps(inst, predictor, n=40, cusum_mode="two_sided"):
    xi=[];yi=[];xc=[];yc=[]
    for j in range(n):
        event=j < n//2; seed=1000+j
        oi,ai,pi=simulate(inst,seed,event,True); ti,zi=ibd_trace(oi,pi)
        oc,ac,_=simulate(inst,seed,event,False); tc,zc=cusum_support_trace(oc,ac,predictor,cusum_mode)
        for ts,z,X,Y in ((ti,zi,xi,yi),(tc,zc,xc,yc)):
            # One sample per channel at each epoch, as draft 2 specifies.
            X.extend(z.ravel()); Y.extend(np.concatenate([label_at(inst,int(t),event) for t in ts]).astype(float))
    return pava_fit(np.asarray(xi),np.asarray(yi)),pava_fit(np.asarray(xc),np.asarray(yc))


def fit_alarm_reference(inst,n=40):
    traces=[]
    for j in range(n):
        event=j<n//2
        o,a,p=simulate(inst,3000+j,event,True); ts,z=ibd_trace(o,p)
        traces.append((ts,z))
    pre=np.concatenate([z[ts<=EVENT_T] for ts,z in traces],axis=0)
    bar=np.median(pre,axis=0); mad=np.median(np.abs(pre-bar),axis=0); scale=np.maximum(1.4826*mad,.5)
    return bar,scale


def first_alarm(ts,stat,h,start=0,end=T):
    run=0
    for t,s in zip(ts,stat):
        if t<=start: continue
        if t>end: break
        run=run+1 if s>h else 0
        if run>=P_EPOCH:return int(t)
    return end+1


def calibrate_h(inst,ref,n=80):
    bar,scale=ref; traces=[]
    for j in range(n):
        o,a,p=simulate(inst,4000+j,False,True);ts,z=ibd_trace(o,p)
        traces.append((ts,np.max(np.abs(z-bar)/scale,axis=1)))
    grid=np.linspace(1,12,221); best=None
    for h in grid:
        rl=np.array([first_alarm(ts,st,h) for ts,st in traces])
        err=abs(rl.mean()-1000)
        if best is None or err<best[0]:best=(err,float(h),float(rl.mean()))
    return best[1],best[2]


def run(n_test=100, nx=10, cusum_mode="two_sided", skip_alarm=False):
    inst=make_instance(nx); predictor=fit_predictor(inst); g_i,g_c=calibrate_maps(inst,predictor,cusum_mode=cusum_mode)
    ref=None if skip_alarm else fit_alarm_reference(inst)
    h,arl=(None,None) if skip_alarm else calibrate_h(inst,ref)
    rows=[]; event_detect=[]; null_detect=[]
    for j in range(n_test):
        seed=5000+j
        oi,ai,pi=simulate(inst,seed,True,True);ti,zi=ibd_trace(oi,pi)
        oc,ac,_=simulate(inst,seed,True,False);tc,zc=cusum_support_trace(oc,ac,predictor,cusum_mode)
        for off in OFFSETS:
            y=inst.support_post
            pii=pava_predict(g_i,value_at(ti,zi,EVENT_T+off))>=.5
            pic=pava_predict(g_c,value_at(tc,zc,EVENT_T+off))>=.5
            rows.append(dict(seed=seed,offset=off,ibd_f1=f1(pii,y),cusum_f1=f1(pic,y),delta=f1(pii,y)-f1(pic,y),
                             ibd_positive_fraction=float(pii.mean()),cusum_positive_fraction=float(pic.mean()),
                             ibd_conf_false=float(pava_predict(g_i,value_at(ti,zi,EVENT_T+off))[inst.conf_mask].mean()),
                             cusum_conf_false=float(pava_predict(g_c,value_at(tc,zc,EVENT_T+off))[inst.conf_mask].mean())))
        if not skip_alarm:
            stat=np.max(np.abs(zi-ref[0])/ref[1],axis=1)
            event_detect.append(first_alarm(ti,stat,h,EVENT_T,EVENT_T+200)<=EVENT_T+200)
            on,an,pn=simulate(inst,seed,False,True);tn,zn=ibd_trace(on,pn)
            sn=np.max(np.abs(zn-ref[0])/ref[1],axis=1)
            null_detect.append(first_alarm(tn,sn,h,EVENT_T,EVENT_T+200)<=EVENT_T+200)
    summary={"n_test":n_test,"n_distractors":nx,"cusum_support_mapping":cusum_mode,"ibd_alarm_h":h,"approx_no_event_mean_run_length":arl,
             "calibrator_max_probability":{"ibd":float(np.max(g_i[1])),"cusum":float(np.max(g_c[1]))},
             "event_alarm_probability_200":None if skip_alarm else float(np.mean(event_detect)),"no_event_alarm_probability_same_window":None if skip_alarm else float(np.mean(null_detect)),
             "f1":{}}
    for off in OFFSETS:
        q=[r for r in rows if r['offset']==off]
        summary['f1'][str(off)]={k:float(np.mean([r[k] for r in q])) for k in ('ibd_f1','cusum_f1','delta','ibd_positive_fraction','cusum_positive_fraction','ibd_conf_false','cusum_conf_false')}
        summary['f1'][str(off)]['delta_se']=float(np.std([r['delta'] for r in q],ddof=1)/math.sqrt(n_test))
    return summary,rows


if __name__ == '__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--n-test',type=int,default=100);ap.add_argument('--nx',type=int,default=10);ap.add_argument('--cusum-map',choices=('two_sided','signed_alignment'),default='two_sided');ap.add_argument('--skip-alarm',action='store_true');ap.add_argument('--out',type=Path)
    a=ap.parse_args(); summary,rows=run(a.n_test,a.nx,a.cusum_map,a.skip_alarm)
    print(json.dumps(summary,indent=2))
    if a.out:
        a.out.mkdir(parents=True,exist_ok=True)
        suffix=f'nx{a.nx}_{a.cusum_map}_{"f1only" if a.skip_alarm else "with_alarm"}'
        (a.out/f'independent_d8_summary_{suffix}.json').write_text(json.dumps(summary,indent=2)+'\n')
        with (a.out/f'independent_d8_rows_{suffix}.csv').open('w',newline='') as f:
            w=csv.DictWriter(f,fieldnames=list(rows[0]));w.writeheader();w.writerows(rows)
