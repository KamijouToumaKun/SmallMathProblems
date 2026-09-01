"""
Critical a* for a_{n+1} = a_n + a_n^2 / n^2 with lim a_n = 1.

The rational barriers are derived (not guessed) in derive_barriers():
  1. Match the critical-track expansion of a_n from the recurrence.
  2. Truncate 1/a_n; invert to a monomial-over-polynomial rational
     (a restricted [d/d] Pade of a_n, equivalently the degree-d
     Taylor polynomial of 1/a_n).
  3. Independently cancel the leading term of the barrier polynomial
     f(n+1) - f(n) - f(n)^2/n^2; for the upper barrier this recovers
     the same last coefficient as step 2.
  4. For a lower barrier, push that last coefficient further negative
     until the difference stays negative for every n >= 1.

Degree is configurable:
    python an+1=an+an^2_n^2.py --degree 3
    python an+1=an+an^2_n^2.py --degree 4 --print-max-degree 5
    python an+1=an+an^2_n^2.py --derive-only --degree 4
    python an+1=an+an^2_n^2.py --degree 3 --lower-c=-1/4
    python an+1=an+an^2_n^2.py --skip-derive

--degree            primary barrier used in the numeric squeeze of a*
--print-max-degree  only expands what is printed / derived for display
                    (1..M); does not change the primary approximation
"""

from __future__ import annotations

import argparse

import sympy as sp
from mpmath import mp, mpf, nstr, sqrt, pi, coth, findroot, digamma

mp.dps = 50


# ---------------------------------------------------------------------------
# Symbolic derivation of the barrier rationals
# ---------------------------------------------------------------------------


def _series_a_of_x(cs, x, order):
    return 1 + sum(cs[i] * x ** (i + 1) for i in range(order))


def critical_asymptotic(order=4):
    """Coefficients in a_n = 1 + c1/n + c2/n^2 + ... for the L = 1 track.

    Substitute into a_{n+1} - a_n = a_n^2/n^2 and equate powers of 1/n.
    Extra dummy terms are kept internally so truncation does not pollute
    the coefficients that we actually report.
    """
    extra = 3
    total = order + extra
    x = sp.symbols("x")
    cs = sp.symbols(f"c1:{total + 1}")
    a = _series_a_of_x(cs, x, total)
    y = sp.series(x / (1 + x), x, 0, total + 3).removeO()
    a_next = 1 + sum(cs[i] * y ** (i + 1) for i in range(total))
    a_next = sp.series(a_next, x, 0, total + 3).removeO()
    residual = sp.series(a_next - a - a**2 * x**2, x, 0, total + 3)
    eqs = [sp.expand(residual.coeff(x, k)) for k in range(2, total + 2)]
    sol = sp.solve(eqs, cs, dict=True)
    if not sol:
        raise RuntimeError("asymptotic matching failed")
    return {cs[i]: sp.simplify(sol[0][cs[i]]) for i in range(order)}


def reciprocal_coeffs(c_map, order):
    """Taylor coefficients of 1/a_n = r0 + r1 x + ... + r_order x^order, x=1/n."""
    x = sp.symbols("x")
    cs = list(c_map.keys())
    a = 1 + sum(c_map[cs[i]] * x ** (i + 1) for i in range(order))
    recip = sp.series(1 / a, x, 0, order + 1).removeO()
    return [sp.together(sp.expand(recip.coeff(x, k))) for k in range(order + 1)], recip, x


def monomial_from_coeffs(coeffs, last=None):
    """f = n^d / (r0 n^d + ... + r_{d-1} n + last), with last defaulting to r_d."""
    n = sp.symbols("n", positive=True)
    degree = len(coeffs) - 1
    den_coeffs = list(coeffs)
    if last is not None:
        den_coeffs[-1] = last
    den = sum(den_coeffs[k] * n ** (degree - k) for k in range(degree + 1))
    return n**degree / sp.together(den), den_coeffs, n


def barrier_fraction(f, n):
    expr = sp.together(f.subs(n, n + 1) - f - f**2 / n**2)
    num, den = sp.fraction(sp.together(expr))
    return sp.expand(num), sp.factor(sp.expand(den))


def barrier_role(num, n):
    """Classify matched truncation: upper / lower / mixed on n=1..check."""
    poly = sp.Poly(num, n)
    lc = poly.LC()
    if lc > 0:
        return "upper"
    if lc < 0:
        return "lower"
    return "degenerate"


def free_last_family(coeffs):
    """Family with last denominator coeff free; earlier coeffs fixed by truncation."""
    n, c = sp.symbols("n c")
    degree = len(coeffs) - 1
    den = sum(coeffs[k] * n ** (degree - k) for k in range(degree)) + c
    f = n**degree / den
    num, den_fact = barrier_fraction(f, n)
    poly = sp.Poly(sp.together(num), n)
    lead_poly = {
        k: sp.simplify(poly.coeff_monomial(n**k))
        for k in range(poly.degree(), -1, -1)
    }
    matched = coeffs[-1]
    # Leading coeff = 0 should recover the matched last coefficient.
    lead = lead_poly[poly.degree()]
    solved = sp.solve(lead, c)
    c_from_barrier = solved[0] if solved else None
    return n, c, f, num, den_fact, lead_poly, matched, c_from_barrier


def barrier_c_candidates(
    n,
    c,
    num,
    den,
    lead_poly,
    c_matched,
    side="lower",
    max_den=16,
    n_check=80,
):
    """Search rationals c for a global upper/lower barrier.

    side='lower': want num <= 0 (and usually c < c_matched).
    side='upper': want num >= 0 (and usually c > c_matched).
    """
    lead_expr = lead_poly[max(lead_poly)]
    found = []
    for q in range(1, max_den + 1):
        for p in range(-6 * q, 6 * q + 1):
            cand = sp.Rational(p, q)
            if side == "lower" and cand >= c_matched:
                continue
            if side == "upper" and cand <= c_matched:
                continue
            if cand in found:
                continue
            lead_val = sp.simplify(lead_expr.subs(c, cand))
            if side == "lower" and lead_val >= 0:
                continue
            if side == "upper" and lead_val <= 0:
                continue
            ok = True
            num_c = sp.expand(num.subs(c, cand))
            den_c = den.subs(c, cand)
            for k in range(1, n_check + 1):
                dv = den_c.subs(n, k)
                nv = num_c.subs(n, k)
                if dv <= 0:
                    ok = False
                    break
                if side == "lower" and nv > 0:
                    ok = False
                    break
                if side == "upper" and nv < 0:
                    ok = False
                    break
            if ok:
                found.append(cand)
    if side == "lower":
        found.sort(reverse=True)  # closest below matched first
    else:
        found.sort()  # closest above matched first
    return found


def pick_c(candidates, prefer=None):
    """Closest candidate; optional preferred rational if it appears near the top."""
    if not candidates:
        return None
    if prefer is not None and prefer in candidates[:8]:
        return prefer
    return candidates[0]


def derive_barriers(degree=3, print_max_degree=None):
    """Derive barriers; `degree` is primary for numerics, `print_max_degree` for display.

    print_max_degree only controls how many degrees are printed/derived for
    comparison.  The numeric sandwich of a* always uses `degree`.
    """
    if print_max_degree is None:
        print_max_degree = max(degree, 3)
    if degree < 1 or print_max_degree < degree:
        raise ValueError("need 1 <= degree <= print_max_degree")

    print("=" * 72)
    print(f"How the barrier rationals are obtained  (primary degree d = {degree})")
    print("=" * 72)
    print()
    print("Not a generic Pade of a_n.  Two steps, and they happen to agree")
    print("on the upper barrier:")
    print("  (i)  truncate the series of 1/a_n, then invert  (restricted Pade)")
    print("  (ii) cancel the leading coefficient of the barrier polynomial")
    print("The lower barrier is (i) with the last coefficient pushed past")
    print("the matching value, so the inequality flips.")
    print("Primary approx: --degree.  Extra printed degrees: --print-max-degree.")
    print()

    # Need one extra reciprocal coeff beyond print_max_degree for display.
    order = print_max_degree + 1
    c_map = critical_asymptotic(order)
    print("Step 1.  Critical-track expansion, L = 1")
    print("         Plug a_n = 1 + c1/n + c2/n^2 + ... into")
    print("         a_{n+1} - a_n = a_n^2 / n^2 and equate powers of 1/n.")
    bits = ", ".join(f"{v} = {c_map[v]}" for v in c_map)
    print(f"         {bits}")
    pieces = ["1"]
    for i, v in enumerate(c_map):
        coef = sp.together(c_map[v])
        p = i + 1
        mag = -coef if coef < 0 else coef
        unit = "1" if mag == 1 else f"({mag})"
        term = f"{unit}/n^{p}"
        pieces.append((" - " if coef < 0 else " + ") + term)
    print("         a_n = " + "".join(pieces))
    print()

    r_coeffs, recip, x = reciprocal_coeffs(c_map, order)
    print("Step 2.  Reciprocal series  1/a_n  (x = 1/n)")
    print(f"         1/a_n = {recip}")
    print("         Truncate at degree d and invert:  that is the rational")
    print("         with numerator n^d  (Pade [d/d] of a_n with monomial")
    print("         numerator).")
    print()

    derived = {"by_degree": {}, "r_coeffs": r_coeffs}
    for d in range(1, print_max_degree + 1):
        f, coeffs_d, n = monomial_from_coeffs(r_coeffs[: d + 1])
        f = sp.simplify(f)
        num, den = barrier_fraction(f, n)
        role = barrier_role(num, n)
        mark = "  [PRIMARY]" if d == degree else ""
        print(f"  d = {d}:  f(n) = {f}{mark}")
        print(f"         1/a_n truncated as {coeffs_d}")
        print(f"         barrier numerator = {sp.factor(num)}")
        print(f"         leading-coeff sign => {role} barrier")
        print()
        derived["by_degree"][d] = {
            "f_matched": f,
            "coeffs": coeffs_d,
            "role": role,
            "num": num,
            "den": den,
        }

    print("Step 3.  Same last coefficient from the barrier polynomial")
    print(f"         Family with degrees 2..{print_max_degree}: fix all but the")
    print("         constant term from truncation, set leading barrier")
    print("         coefficient to zero.")
    print()
    for d in range(2, print_max_degree + 1):
        n, c, f, num, den, lead_poly, matched, c_from_barrier = free_last_family(
            r_coeffs[: d + 1]
        )
        print(f"  d = {d}: matched last coeff from 1/a_n = {matched}")
        print(f"         leading barrier coeff = {lead_poly[max(lead_poly)]}")
        print(f"         set to 0 => c = {c_from_barrier}")
        if c_from_barrier is not None and sp.simplify(c_from_barrier - matched) == 0:
            print("         Agrees with truncation.")
        else:
            print("         WARNING: disagrees with truncation.")
        derived["by_degree"][d].update(
            {
                "n": n,
                "c": c,
                "num_free": num,
                "den_free": den,
                "lead_poly": lead_poly,
                "c_matched": matched,
                "c_from_barrier": c_from_barrier,
            }
        )
        print()

    print("Step 4.  Choose upper / lower barriers at the primary degree")
    primary = derived["by_degree"][degree]
    prefer_lower = sp.Rational(-1, 4) if degree == 3 else None
    prefer_upper = sp.Rational(-1, 6) if degree >= 3 else None

    if degree == 1:
        c_lower = primary["coeffs"][-1]
        f_lower = primary["f_matched"]
        # Need an upper barrier from a higher degree.
        up = derived["by_degree"][2]
        c_upper = up["coeffs"][-1]
        f_upper = up["f_matched"]
        print("         d = 1 matched truncation is already a lower barrier.")
        print(f"         g(n) = {f_lower}")
        print(f"         Companion upper barrier from d = 2: {f_upper}")
    else:
        info = derived["by_degree"][degree]
        n, c = info["n"], info["c"]
        c_matched = info["c_matched"]
        print(f"         Matched last coeff c = {c_matched}, role = {info['role']}")

        if info["role"] == "upper":
            c_upper = c_matched
            f_upper = info["f_matched"]
            candidates = barrier_c_candidates(
                n, c, info["num_free"], info["den_free"], info["lead_poly"], c_matched, side="lower"
            )
            print("         Lower-barrier candidates c < matched (closest first):")
            print("          ", ", ".join(str(v) for v in candidates[:16]) or "(none)")
            c_lower = pick_c(candidates, prefer=prefer_lower)
            if c_lower is None:
                raise RuntimeError(
                    f"no lower-barrier rational found at degree {degree}; try another --degree"
                )
            f_lower, _, _ = monomial_from_coeffs(info["coeffs"], last=c_lower)
            f_lower = sp.simplify(f_lower)
            print(f"         Chosen lower c = {c_lower}")
            print(f"         g(n) = {f_lower}")
        else:
            # Matched truncation already a lower barrier.
            c_lower = c_matched
            f_lower = info["f_matched"]
            candidates = barrier_c_candidates(
                n, c, info["num_free"], info["den_free"], info["lead_poly"], c_matched, side="upper"
            )
            print("         Matched truncation is already lower.")
            print("         Upper-barrier candidates c > matched (closest first):")
            print("          ", ", ".join(str(v) for v in candidates[:16]) or "(none)")
            c_upper = pick_c(candidates, prefer=prefer_upper)
            if c_upper is None:
                # Fall back to previous upper-capable degree.
                c_upper = None
                f_upper = None
                for d in range(degree - 1, 1, -1):
                    if derived["by_degree"][d]["role"] == "upper":
                        c_upper = derived["by_degree"][d]["coeffs"][-1]
                        f_upper = derived["by_degree"][d]["f_matched"]
                        print(f"         No d={degree} upper candidate; fall back to d={d}.")
                        break
                if f_upper is None:
                    raise RuntimeError("could not find an upper barrier")
            else:
                f_upper, _, _ = monomial_from_coeffs(info["coeffs"], last=c_upper)
                f_upper = sp.simplify(f_upper)
                print(f"         Chosen upper c = {c_upper}")
                print(f"         f(n) = {f_upper}")
            print(f"         g(n) = {f_lower}")

    nsym = sp.symbols("n", positive=True)
    f1 = sp.simplify(f_upper.subs(nsym, 1))
    g1 = sp.simplify(f_lower.subs(nsym, 1))
    print()
    print(f"Elementary sandwich from N = 1 at primary d = {degree}:")
    # Upper barrier f => lower bound for a*; lower barrier g => upper bound for a*.
    print(f"         upper-barrier f(1) = {f1}  =>  a* > {f1}")
    print(f"         lower-barrier g(1) = {g1}  =>  a* < {g1}")
    print(f"         so  {f1} < a* < {g1}")
    print("=" * 72)
    print()

    derived.update(
        {
            "degree": degree,
            "print_max_degree": print_max_degree,
            "c_upper": c_upper,
            "c_lower": c_lower,
            "f_upper": f_upper,
            "f_lower": f_lower,
            "upper_den_coeffs": _den_coeffs_of(sp.together(f_upper), nsym),
            "lower_den_coeffs": _den_coeffs_of(sp.together(f_lower), nsym),
        }
    )
    return derived


def _den_coeffs_of(f, n):
    num, den = sp.fraction(sp.together(f))
    # Expect num = const * n^d
    poly = sp.Poly(sp.expand(den), n)
    # Normalize so leading den coeff matches leading num coeff ratio = 1 for n^d/den
    lead_num = sp.Poly(sp.expand(num), n).LC()
    coeffs = [sp.together(poly.coeff_monomial(n**k) / lead_num) for k in range(poly.degree(), -1, -1)]
    return coeffs


# ---------------------------------------------------------------------------
# High-precision sandwich
# ---------------------------------------------------------------------------


def rational_from_den_coeffs(n, den_coeffs):
    """Evaluate n^{d} / (c0 n^d + c1 n^{d-1} + ... + cd)."""
    n = mpf(n)
    d = len(den_coeffs) - 1
    den = mpf(0)
    for k, ck in enumerate(den_coeffs):
        den += mpf(ck) * n ** (d - k)
    return n**d / den


def backward(a_N, N):
    """Invert a_{k+1} = a_k + a_k^2/k^2 from index N down to a_1."""
    a = mpf(a_N)
    for k in range(N - 1, 0, -1):
        k2 = mpf(k) ** 2
        a = (2 * a) / (1 + sqrt(1 + 4 * a / k2))
    return a


def f_quad(n):
    n = mpf(n)
    return n**2 / (n**2 + n + mpf("0.5"))


def g_linear(n):
    n = mpf(n)
    return n / (n + 1)


def tail_upper(n):
    """Upper bound for a_n on any trajectory with L <= 1."""
    n = mpf(n)
    s = (digamma(n + 1j) - digamma(n - 1j)) / (2j)
    return 1 / (1 + s.real)


def frozen_coth_lower():
    def f(a):
        s = sqrt(a)
        return 2 * a + pi * s * coth(pi * s) - 3

    return findroot(f, mpf("0.43"))


def coth_one_upper():
    return 2 / (pi * coth(pi) + 1)


def barrier_delta(h, n):
    n = mpf(n)
    return h(n + 1) - h(n) - (h(n) / n) ** 2


def verify_barriers(f_upper, g_lower, N=200):
    f_pos = min(barrier_delta(f_upper, k) for k in range(1, N + 1))
    g_neg = max(barrier_delta(g_lower, k) for k in range(1, N + 1))
    q_pos = min(barrier_delta(f_quad, k) for k in range(1, N + 1))
    lin_neg = max(barrier_delta(g_linear, k) for k in range(1, N + 1))
    assert f_pos > 0, f_pos
    assert g_neg < 0, g_neg
    assert q_pos > 0, q_pos
    assert lin_neg < 0, lin_neg
    return f_pos, g_neg


def limit_from_a1(a1, N=10000):
    a = mpf(a1)
    for k in range(1, N):
        a = a + (a / k) ** 2
    return a * N / (N - a)


def run_numeric(upper_den_coeffs, lower_den_coeffs, degree):
    f_upper = lambda n: rational_from_den_coeffs(n, upper_den_coeffs)
    g_lower = lambda n: rational_from_den_coeffs(n, lower_den_coeffs)
    verify_barriers(f_upper, g_lower)

    alpha = frozen_coth_lower()
    elementary_lo = f_upper(1)  # lower bound for a*
    elementary_hi = g_lower(1)  # upper bound for a*

    print(f"Closed-form bounds for a* = L^{{-1}}(1)  [primary degree d = {degree}]")
    print(f"  d=2 upper f(1)=2/5               {nstr(f_quad(1), 20)}")
    print(f"  d={degree} upper-barrier f(1)      {nstr(elementary_lo, 20)}")
    print(f"  frozen coth (a_k == a1)           {nstr(alpha, 20)}")
    print(f"  d={degree} lower-barrier g(1)      {nstr(elementary_hi, 20)}")
    print(f"  d=1 lower g(1)=1/2                {nstr(mpf('0.5'), 20)}")
    print(f"  2/(pi coth(pi)+1)                 {nstr(coth_one_upper(), 20)}")
    print()
    print(f"Elementary sandwich:  {nstr(elementary_lo, 12)} < a* < {nstr(elementary_hi, 12)}")
    print()

    Ns = [1, 10, 100, 1000, 10000, 30000]
    header = (
        f"{'N':>6}  {'quad lower':>22}  {'d-upper->lo':>22}  "
        f"{'d-lower->hi':>22}  {'tail upper':>22}  {'width':>10}"
    )
    print(header)
    print("-" * len(header))

    best_lo = elementary_lo
    best_hi = elementary_hi
    rows = []
    for N in Ns:
        lo_q = backward(f_quad(N), N)
        lo_d = backward(f_upper(N), N)
        hi_d = backward(g_lower(N), N)
        hi_t = backward(tail_upper(N), N)
        lo = max(lo_q, lo_d)
        hi = min(hi_d, hi_t)
        best_lo = max(best_lo, lo)
        best_hi = min(best_hi, hi)
        width = hi - lo
        rows.append((N, lo_q, lo_d, hi_d, hi_t, width))
        print(
            f"{N:6d}  {nstr(lo_q, 20):>22}  {nstr(lo_d, 20):>22}  "
            f"{nstr(hi_d, 20):>22}  {nstr(hi_t, 20):>22}  {nstr(width, 6):>10}"
        )

    print()
    print(f"Best squeeze  {nstr(best_lo, 25)}  <  a*  <  {nstr(best_hi, 25)}")
    print(f"Width         {nstr(best_hi - best_lo, 8)}")
    print()
    print("Check of the 2023 contest value a1 = 2/5:")
    L = limit_from_a1(mpf(2) / 5)
    print(f"  L(2/5) ~ {nstr(L, 12)}  (strictly less than 1)")

    csv_path = __file__.replace(".py", ".csv")
    with open(csv_path, "w", encoding="utf-8") as fh:
        fh.write("N,quad_lower,degree_upper_lower,degree_lower_upper,tail_upper,width\n")
        for N, lo_q, lo_d, hi_d, hi_t, width in rows:
            fh.write(
                f"{N},{nstr(lo_q, 20)},{nstr(lo_d, 20)},"
                f"{nstr(hi_d, 20)},{nstr(hi_t, 20)},{nstr(width, 6)}\n"
            )
    print(f"\nWrote {csv_path}")


def default_den_coeffs(degree=3):
    """Hard-coded defaults when --skip-derive is used (degree 3 only)."""
    if degree != 3:
        raise ValueError("--skip-derive only supports the default --degree 3")
    # n^3 / (n^3 + n^2 + n/2 - 1/6) and n^3 / (n^3 + n^2 + n/2 - 1/4)
    upper = [1, 1, sp.Rational(1, 2), sp.Rational(-1, 6)]
    lower = [1, 1, sp.Rational(1, 2), sp.Rational(-1, 4)]
    return upper, lower


def main(argv=None):
    parser = argparse.ArgumentParser(
        description="Derive and squeeze the critical a* for a_{n+1}=a_n+a_n^2/n^2"
    )
    parser.add_argument(
        "--degree",
        type=int,
        default=3,
        help="primary fitting degree d for the monomial barrier (default: 3)",
    )
    parser.add_argument(
        "--print-max-degree",
        type=int,
        default=None,
        dest="print_max_degree",
        help="print/derive degrees 1..M for comparison only; "
        "does not change the primary numeric squeeze (default: max(degree, 3))",
    )
    parser.add_argument(
        "--max-degree",
        type=int,
        default=None,
        dest="print_max_degree",
        help=argparse.SUPPRESS,  # deprecated alias of --print-max-degree
    )
    parser.add_argument("--derive-only", action="store_true")
    parser.add_argument(
        "--skip-derive",
        action="store_true",
        help="skip sympy derivation; only works with --degree 3",
    )
    parser.add_argument(
        "--lower-c",
        type=str,
        default=None,
        help="optional override of lower-barrier last denom coeff "
        "(code already auto-picks the closest valid rational; "
        "use this for a preferred simple fraction like -1/4)",
    )
    parser.add_argument(
        "--upper-c",
        type=str,
        default=None,
        help="optional override of upper-barrier last denom coeff",
    )
    args = parser.parse_args(argv)

    if args.skip_derive:
        upper_den, lower_den = default_den_coeffs(args.degree)
        degree = args.degree
    else:
        derived = derive_barriers(
            degree=args.degree, print_max_degree=args.print_max_degree
        )
        if args.upper_c is not None or args.lower_c is not None:
            info = derived["by_degree"][args.degree]
            coeffs = info["coeffs"]
            if args.upper_c is not None:
                cu = sp.Rational(args.upper_c)
                fu, _, _ = monomial_from_coeffs(coeffs, last=cu)
                derived["f_upper"] = sp.simplify(fu)
                derived["c_upper"] = cu
                derived["upper_den_coeffs"] = _den_coeffs_of(
                    sp.together(derived["f_upper"]), sp.symbols("n", positive=True)
                )
                print(f"Override upper last coeff c = {cu}")
                print(f"  f(n) = {derived['f_upper']}")
            if args.lower_c is not None:
                cl = sp.Rational(args.lower_c)
                fl, _, _ = monomial_from_coeffs(coeffs, last=cl)
                derived["f_lower"] = sp.simplify(fl)
                derived["c_lower"] = cl
                derived["lower_den_coeffs"] = _den_coeffs_of(
                    sp.together(derived["f_lower"]), sp.symbols("n", positive=True)
                )
                print(f"Override lower last coeff c = {cl}")
                print(f"  g(n) = {derived['f_lower']}")
        upper_den = derived["upper_den_coeffs"]
        lower_den = derived["lower_den_coeffs"]
        degree = derived["degree"]

    if args.derive_only:
        return
    run_numeric(upper_den, lower_den, degree)


if __name__ == "__main__":
    main()
