def xgcd(x: int, y: int):
    old_r, r = (x, y)
    old_s, s = (1, 0)
    old_t, t = (0, 1)

    while r != 0:
        quo = old_r // r
        old_r, r = (r, old_r - quo * r)
        old_s, s = (s, old_s - quo * s)
        old_t, t = (t, old_t - quo * t)
    (a, b, d) = (old_s, old_t, old_r)
    return a, b, d  # a,b are Bezout coefficient and d is the GCD
