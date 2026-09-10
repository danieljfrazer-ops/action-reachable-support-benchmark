import numpy as np
np.set_printoptions(precision=4, suppress=True)
rng = np.random.default_rng(0)

# ---- G1: does closed-loop policy feedback make R depend on the sensor map P? ----
K, Nb = 2, 2
A_b = np.diag([0.9, 0.9]); B = np.eye(2)
# observation: channels [b0, b1, w0, x0, pad]; take only body channels for policy feedback
def assign_matrix(order):  # order: which latent each of 2 body-reading channels sees
    M = np.zeros((2, 2)); 
    for ch, lat in enumerate(order): M[ch, lat] = 1
    return M
W_o = np.array([[0.3, -0.2],[0.1, 0.4]])  # policy reads the two body channels
def response(h, assign, closed_loop, a):
    """E[b_{t+h}|do(a_t=a)] - E[b_{t+h}|do(a_t=0)], zero noise, z̄=0."""
    def roll(a0):
        b = np.zeros(2); act = a0.copy()
        for step in range(h):
            b = A_b @ b + B @ act
            if closed_loop:
                o = assign @ b            # channel readings
                act = W_o @ o             # default policy acts on observation
            else:
                act = np.zeros(2)         # open-loop clamp
        return b
    return roll(a) - roll(np.zeros(2))
a = np.array([1.0, 0.0])
for h in (1, 2, 3):
    r_id_cl = response(h, assign_matrix([0,1]), True, a)
    r_sw_cl = response(h, assign_matrix([1,0]), True, a)   # sensor swap
    r_id_ol = response(h, assign_matrix([0,1]), False, a)
    r_sw_ol = response(h, assign_matrix([1,0]), False, a)
    print(f"G1 h={h}  closed-loop: identity {r_id_cl}  swapped {r_sw_cl}  differ={not np.allclose(r_id_cl, r_sw_cl)}")
    print(f"G1 h={h}  open-loop : identity {r_id_ol}  swapped {r_sw_ol}  differ={not np.allclose(r_id_ol, r_sw_ol)}")

# ---- G2: negative exponent for h <= tau ----
tau, h = 1, 1
try:
    M = np.linalg.matrix_power(A_b, h-1-tau) @ B
    print("G2 A_b^(h-1-tau) with h=1,tau=1 computed as:", M, "(acausal: true response should be 0)")
except Exception as e:
    print("G2 error:", e)
A_sing = np.array([[0.9, 0.0],[0.0, 0.0]])
try:
    np.linalg.matrix_power(A_sing, -1)
except np.linalg.LinAlgError as e:
    print("G2 singular A_b raises:", e)

# ---- G3: correlation under a constant probe ----
T = 5000
u = rng.normal(size=T); x_next = 0.8*u + rng.normal(size=T)*0.3
a_obs = 0.7*u + rng.normal(size=T)*0.3            # default policy correlated with u
a_const = np.full(T, 1.0)                          # do(a = a*)
a_rand = rng.uniform(-1, 1, size=T)                # randomized do(a)
with np.errstate(invalid='ignore', divide='ignore'):
    print("G3 corr(obs policy, x_next) =", np.corrcoef(a_obs, x_next)[0,1].round(3))
    print("G3 corr(constant probe, x_next) =", np.corrcoef(a_const, x_next)[0,1])
    print("G3 corr(randomized do(a), x_next) =", np.corrcoef(a_rand, x_next)[0,1].round(3))
