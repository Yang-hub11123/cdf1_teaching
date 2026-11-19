"""Petal Tiles / 合瓣 · Rhino 8 Grasshopper Python 3 Script.

Inputs (Item Access, str type hint): A, B, C, D.
Outputs: Ivory, Indigo, Terracotta, Gold. Keep 'out' for seam count.

Edge strings use N=up (+Y), E=right (+X), S=down, W=left.
Each tile has two fixed, adjacent connecting edges. The input chooses
where those edges should face in Top view. All instances of that type
turn together in 90-degree steps; the floral motif turns with the edges.
An indigo-and-gold leaf appears only on a mutually connected seam.

Paste the following into the edit window of each Grasshopper Value List:

NE = "NE"
ES = "ES"
SW = "SW"
NW = "NW"

Four clusters: A=ES, B=SW, C=NE, D=NW (all at zero rotation).

Connect each output to G of its own Custom Preview. Set its S input with
a Colour Swatch: Ivory #F3E8D4, Indigo #223C59, Terracotta #AA4836,
Gold #BC843E. Disable the Python component's own preview.
"""

from collections import namedtuple

LAYOUT = ("ABAB", "CDCD", "ABAB", "CDCD")
DEFAULT_EDGES = dict(zip("ABCD", ("ES", "SW", "NE", "NW")))
EDGE_ORDER = "NESW"
CORNER_PAIRS = tuple(frozenset(pair) for pair in ("NE", "ES", "SW", "NW"))
TileLayout = namedtuple("TileLayout", "links turns")
OFFSETS = {"N": (-1, 0), "E": (0, 1), "S": (1, 0), "W": (0, -1)}
OPPOSITE = dict(zip("NESW", "SWNE"))
TILE_SIZE = 40.0
TOLERANCE = 0.001


def collect_connections(settings):
    """Determine each type's rotation and record matching seams."""
    allowed = {}
    turns = {}
    for name, default in DEFAULT_EDGES.items():
        value = settings.get(name)
        text = default if value is None else str(value).strip().upper()
        selected = frozenset(text)
        if len(text) != 2 or selected not in CORNER_PAIRS:
            raise ValueError("{}: select NE, ES, SW, or NW to rotate the tile."
                             .format(name))
        allowed[name] = selected
        original = CORNER_PAIRS.index(frozenset(default))
        turns[name] = (CORNER_PAIRS.index(selected) - original) % 4

    tiles = {
        (row, col): name
        for row, line in enumerate(LAYOUT)
        for col, name in enumerate(line)
    }
    links = {position: set() for position in tiles}
    for (row, col), name in tiles.items():
        for direction in ("E", "S"):
            dr, dc = OFFSETS[direction]
            neighbor = (row + dr, col + dc)
            opposite = OPPOSITE[direction]
            if (neighbor in tiles
                    and direction in allowed[name]
                    and opposite in allowed[tiles[neighbor]]):
                links[row, col].add(direction)
                links[neighbor].add(opposite)
    return TileLayout(links, turns)


# Each mark is (color, layer, geometry kind, local coordinates).
# A path contains straight, quadratic or cubic Bezier segments.
PATTERN_VERSION = "FLORAL-ASYM-05"


def polygon(*vertices):
    return list(zip(vertices, vertices[1:] + vertices[:1]))


IRIS = [
    ("Indigo", 1, "path", [
        ((0, -2), (-10, 5), (0, 19)),
        ((0, 19), (10, 5), (0, -2)),
    ]),
    ("Ivory", 2, "path", [
        ((0, 4), (-3, 9), (0, 15)),
        ((0, 15), (3, 9), (0, 4)),
    ]),
]
CAMELLIA = [
    ("Terracotta", 1, "path", [
        ((0, -2), (-6, 3), (-14, 17), (0, 17)),
        ((0, 17), (14, 17), (6, 3), (0, -2)),
    ]),
]
LAUREL = [
    ("Indigo", 1, "path", [
        ((0, 0), (-13, 1), (-5, 14), (3, 20)),
        ((3, 20), (9, 14), (9, 5), (0, 0)),
    ]),
    ("Ivory", 2, "path", [
        ((0, 3), (0, 11), (3, 16)),
        ((3, 16), (1, 10), (0, 3)),
    ]),
]
LEAF = [
    ("Indigo", 1, "path", [
        ((-13, 50), (-9, 38), (0, 27)),
        ((0, 27), (9, 38), (13, 50)),
        ((13, 50), (-13, 50)),
    ]),
    ("Gold", 2, "path", [
        ((-5, 50), (-3, 45), (0, 41)),
        ((0, 41), (3, 45), (5, 50)),
        ((5, 50), (-5, 50)),
    ]),
]


def tile_marks(name, turns, connected):
    """Rotate the floral motif and add marks at the connected world edges."""
    import math

    marks = []
    if name == "C":
        for layer, (radius, color) in enumerate(
            [(19, "Indigo"), (13, "Ivory"), (9, "Gold"), (4, "Indigo")], 1
        ):
            shape = polygon((0.22 * radius, 1.17 * radius),
                            (1.13 * radius, -0.08 * radius),
                            (-0.14 * radius, -0.89 * radius),
                            (-0.97 * radius, 0.18 * radius))
            marks.append((color, layer, "path", shape, 0))
        for x, y, radius in [(-16, 13, 2.6), (16, 15, 1.5),
                             (18, -15, 2.1), (-14, -17, 1.2)]:
            marks.append(("Terracotta", 1, "disk", (x, y, radius), 0))
    else:
        petals = {"A": IRIS, "B": CAMELLIA, "D": LAUREL}[name]
        arrangement = {
            "A": ((7, 1.17), (-86, 0.89), (-182, 0.97), (-273, 0.80)),
            "B": ((-13, 1.04), (-103, 1.18), (-198, 0.78), (-284, 0.92)),
            "D": ((-41, 1.14), (-128, 0.83), (-229, 0.99), (-309, 0.74)),
        }[name]
        for degrees, scale in arrangement:
            for color, layer, kind, segments in petals:
                shape = [tuple((x * scale, y * scale) for x, y in segment)
                         for segment in segments]
                marks.append((color, layer, kind, shape, math.radians(degrees)))
        center_color = "Terracotta" if name == "A" else "Gold"
        radius = 4.5 if name == "B" else 3.5
        marks.append((center_color, 2, "disk", (0, 0, radius), 0))

    # The corner dots turn with the center motif.
    marks.append(("Gold", 1, "disk", (27, 31, 3.0), 0))
    marks.append(("Gold", 1, "disk", (35, 31, 1.7), 0))
    spin = -turns * math.pi / 2
    rotated = [(color, layer, kind, shape, angle + spin)
               for color, layer, kind, shape, angle in marks]

    # The layout has already checked opposite edges in world coordinates.
    for i, direction in enumerate(EDGE_ORDER):
        if direction in connected:
            rotated.extend((*mark, -i * math.pi / 2) for mark in LEAF)
    return rotated


def build_floor(layout):
    """Turn the motif outlines into Rhino planar Breps grouped by color."""
    import math
    from System import Array
    import Rhino.Geometry as rg

    print("Petal Tiles " + PATTERN_VERSION)
    print("Clockwise rotation: " + ", ".join(
        "{} = {} deg".format(name, turns * 90) for name, turns in layout.turns.items()
    ))
    print("Connected seams: {}".format(sum(map(len, layout.links.values())) // 2))
    colors = {name: [] for name in ("Ivory", "Indigo", "Terracotta", "Gold")}
    unit = TILE_SIZE / 100.0

    for row, line in enumerate(LAYOUT):
        for col, name in enumerate(line):
            cx = (col + 0.5) * TILE_SIZE
            cy = (len(LAYOUT) - row - 0.5) * TILE_SIZE
            corners = [(-50, -50), (50, -50), (50, 50), (-50, 50)]
            boundary = list(zip(corners, corners[1:] + corners[:1]))
            marks = [("Ivory", 0, "path", boundary, 0)]
            marks.extend(tile_marks(name, layout.turns[name], layout.links[row, col]))

            for color, layer, kind, shape, angle in marks:
                cos_a, sin_a = math.cos(angle), math.sin(angle)
                z = 0.05 * layer

                def point(x, y):
                    return rg.Point3d(
                        cx + unit * (cos_a*x - sin_a*y),
                        cy + unit * (sin_a*x + cos_a*y), z
                    )

                if kind == "disk":
                    x, y, radius = shape
                    outline = rg.Circle(point(x, y), radius * unit).ToNurbsCurve()
                else:
                    outline = rg.PolyCurve()
                    for segment in shape:
                        points = [point(x,y) for x,y in segment]
                        if len(points) == 2:
                            curve = rg.LineCurve(points[0], points[1])
                        else:
                            curve = rg.NurbsCurve.Create(
                                False, len(points) - 1, Array[rg.Point3d](points)
                            )
                            if curve is None:
                                raise RuntimeError("Could not create a motif curve.")
                        if not outline.Append(curve):
                            raise RuntimeError("Could not join a motif outline.")
                faces = rg.Brep.CreatePlanarBreps(outline, TOLERANCE)
                if faces is None or len(faces) == 0:
                    raise RuntimeError("Could not fill a motif on tile {}.".format(name))
                colors[color].extend(faces)
    return tuple(colors[name] for name in ("Ivory", "Indigo", "Terracotta", "Gold"))


# The same file can be imported to test the rule without loading Rhino.
if "ghenv" in globals() or any(name in globals() for name in DEFAULT_EDGES):
    tile_layout = collect_connections({name: globals().get(name) for name in DEFAULT_EDGES})
    Ivory, Indigo, Terracotta, Gold = build_floor(tile_layout)
