import math

def heading_error(current, target):
    return (target - current + math.pi) % (2 * math.pi) - math.pi

tests = [
    # (current, target, expected, description)
    (0,              0,               0,           "same heading"),
    (0,              math.pi/2,       math.pi/2,   "90° left turn"),
    (0,             -math.pi/2,      -math.pi/2,   "90° right turn"),
    (0,              math.pi*0.99,    math.pi*0.99, "nearly 180° left"),
    (0,             -math.pi*0.99,   -math.pi*0.99, "nearly 180° right"),
    (math.pi*0.9,  -math.pi*0.9,    -math.pi*0.2,  "wrap-around right"),
    (-math.pi*0.9,  math.pi*0.9,     math.pi*0.2,  "wrap-around left"),
    (math.pi - 0.01, -math.pi + 0.01, 0.02,        "crossing ±π boundary"),
    (0,              math.pi,         math.pi,      "exact 180°"),
    (2.5,            -2.5,           -1.283,        "arbitrary values"),
]

for current, target, expected, desc in tests:
    result = heading_error(current, target)
    ok = math.isclose(result, expected, abs_tol=1e-3)
    print(f"{'PASS' if ok else 'FAIL'}  {desc:35s}  got {result:+.4f}  expected {expected:+.4f}")