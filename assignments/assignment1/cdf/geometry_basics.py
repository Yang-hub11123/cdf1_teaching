"""
Geometry basics -- reusable Rhino.Geometry functions for Grasshopper.

Adding a new function with Copilot
-----------------------------------
1. Open this file and select this chat model, then ask Copilot something like:
   "Add a function here, all in Rhino geometry, that builds a <your shape/idea>.
   Follow the same style as create_cone / create_fractal_tree (defaults for
   optional inputs, a docstring listing params, return a Rhino.Geometry object)."
2. Once the function is added, ask Copilot:
   "Give me the Python code to use this function in a Grasshopper GHPython 3
   component, importing it from computational_design_and_fabrication."
3. Copy the snippet Copilot gives you into a GHPython component, wire up the
   inputs as sliders/panels, and set the output variable (e.g. `a`).
"""

import math
import Rhino.Geometry as rg

def create_cone(base_point=None, height=10.0, radius=5.0, cap_bottom=True):
    """
    Build a cone as a Brep.

    base_point : Rhino.Geometry.Point3d -- center of the cone's base circle
    height     : float -- cone height along the base plane's normal (Z by default)
    radius     : float -- base circle radius
    cap_bottom : bool  -- whether to cap the base circle (closed vs open cone)

    Returns a Rhino.Geometry.Brep.
    """
    if base_point is None:
        base_point = rg.Point3d(0, 0, 0)

    plane = rg.Plane(base_point, rg.Vector3d.ZAxis)
    cone = rg.Cone(plane, height, radius)
    return cone.ToBrep(cap_bottom)

def create_sphere(center_point=None, radius=5.0):
    """
    Build a sphere as a Brep.

    center_point : Rhino.Geometry.Point3d -- center of the sphere
    radius       : float -- sphere radius

    Returns a Rhino.Geometry.Brep.
    """
    if center_point is None:
        center_point = rg.Point3d(0, 0, 0)

    sphere = rg.Sphere(center_point, radius)
    return sphere.ToBrep()

def boolean_difference(brep_a, brep_b):
    """
    Perform a boolean difference operation between two Breps.

    brep_a : Rhino.Geometry.Brep -- the first Brep
    brep_b : Rhino.Geometry.Brep -- the second Brep to subtract from the first

    Returns a list of Rhino.Geometry.Brep resulting from the difference.
    """
    if brep_a is None or brep_b is None:
        raise ValueError("Both brep_a and brep_b must be provided.")

    result = rg.Brep.CreateBooleanDifference(brep_a, brep_b, 0.001)
    return result


def copy_brep_along_z(brep, distance, copy_count):
    """
    Create copies of a Brep, each offset in the +Z direction.

    brep : Rhino.Geometry.Brep -- the Brep to copy
    distance : float -- the Z spacing between consecutive copies
    copy_count : int -- the number of copies to create

    Returns a list of Rhino.Geometry.Brep copies; copy i is moved by distance * (i + 1).
    """
    if brep is None:
        raise ValueError("brep must be provided.")
    if copy_count < 0:
        raise ValueError("copy_count must not be negative.")

    copies = []
    for i in range(1, int(copy_count) + 1):
        copy = brep.DuplicateBrep()
        copy.Transform(rg.Transform.Translation(rg.Vector3d(0, 0, distance * i)))
        copies.append(copy)
    return copies


def create_arc(point_a, point_b, point_c):
    """
    Create an arc through three points.

    point_a : Rhino.Geometry.Point3d -- start point
    point_b : Rhino.Geometry.Point3d -- point on the arc
    point_c : Rhino.Geometry.Point3d -- end point

    Returns
    -------
    Rhino.Geometry.ArcCurve
        The generated arc.
    """
    if point_a is None or point_b is None or point_c is None:
        raise ValueError("All three points must be provided.")

    arc = rg.Arc(point_a, point_b, point_c)

    if not arc.IsValid:
        raise ValueError("Invalid arc geometry.")

    return rg.ArcCurve(arc)

def create_polyline(points, closed=False):
    """
    Create a polyline from a list of points.

    points : list[Rhino.Geometry.Point3d]
        Points defining the polyline.
    closed : bool
        Whether to close the polyline.

    Returns
    -------
    Rhino.Geometry.PolylineCurve
        Polyline geometry.
    """
    if points is None or len(points) < 2:
        raise ValueError("At least two points are required.")

    pts = list(points)

    if closed and pts[0].DistanceTo(pts[-1]) > 1e-9:
        pts.append(pts[0])

    return rg.PolylineCurve(pts)

def create_progressive_array(
    geometry,
    count,
    translation=(0, 0, 0),
    scale_step=(0, 0, 0),
    origin=None
):
    """
    Create a progressively scaled geometry array.

    Parameters
    ----------
    geometry : Rhino.Geometry.GeometryBase
        Original geometry.
    count : int
        Number of elements.
    translation : tuple
        Translation increment (dx, dy, dz).
    scale_step : tuple
        Scale-factor increment (sx, sy, sz).
    origin : Rhino.Geometry.Point3d
        Scaling reference point.

    Returns
    -------
    list
        Progressively scaled geometries.
    """

    if geometry is None:
        raise ValueError("Geometry must be provided.")

    count = int(count)

    if count < 1:
        raise ValueError("Count must be at least 1.")

    if origin is None:
        origin = rg.Point3d(0, 0, 0)

    results = []

    for i in range(count):

        # 1. Duplicate original geometry
        new_geometry = geometry.Duplicate()

        # 2. Progressive scaling
        fx = 1.0 + i * scale_step[0]
        fy = 1.0 + i * scale_step[1]
        fz = 1.0 + i * scale_step[2]

        if min(fx, fy, fz) <= 0:
            raise ValueError("Scale factors must be positive.")

        plane = rg.Plane(
            origin,
            rg.Vector3d.ZAxis
        )

        scale_transform = rg.Transform.Scale(
            plane, fx, fy, fz
        )

        new_geometry.Transform(scale_transform)

        # 3. Progressive translation
        move_transform = rg.Transform.Translation(
            i * translation[0],
            i * translation[1],
            i * translation[2]
        )

        new_geometry.Transform(move_transform)

        results.append(new_geometry)

    return results

def create_pipe(curves, radius, cap_mode=rg.PipeCapMode.Flat):
    """
    Create pipes along one or multiple curves.

    Parameters
    ----------
    curves : Rhino.Geometry.Curve or list[Curve]
        One curve or a list of curves.
    radius : float
        Pipe radius.
    cap_mode : Rhino.Geometry.PipeCapMode
        End cap style.

    Returns
    -------
    list[Rhino.Geometry.Brep]
        Generated pipe geometries.
    """
    if curves is None:
        raise ValueError("Curves must be provided.")

    if radius <= 0:
        raise ValueError("Radius must be positive.")

    if isinstance(curves, rg.Curve):
        curves = [curves]

    results = []

    for curve in curves:
        if curve is None or not curve.IsValid:
            raise ValueError("Invalid input curve.")

        pipes = rg.Brep.CreatePipe(
            curve,
            float(radius),
            False,
            cap_mode,
            True,
            0.001,
            0.001
        )

        if pipes:
            results.extend(pipes)

    return results

def create_interpolated_curve(points, degree=3):
    """
    Create a smooth curve passing through given points.

    Parameters
    ----------
    points : list[Rhino.Geometry.Point3d]
        Control points.
    degree : int
        Curve degree (default 3).

    Returns
    -------
    Rhino.Geometry.Curve
    """
    if points is None or len(points) < degree + 1:
        raise ValueError("Not enough points.")

    return rg.Curve.CreateInterpolatedCurve(
        points,
        degree
    )

import Rhino.Geometry as rg


def create_ribbon(
    curve,
    width=6.0,
    thickness=0.8,
    trim_z=0.0,
    tolerance=0.001
):
    """
    Create a solid ribbon and trim everything below a given Z height.

    Parameters
    ----------
    curve : Rhino.Geometry.Curve
        Centerline of the ribbon.
    width : float
        Ribbon width.
    thickness : float
        Ribbon thickness.
    trim_z : float
        Cutting height. Everything below this height is removed.
    tolerance : float
        Geometry tolerance.

    Returns
    -------
    list[Rhino.Geometry.Brep]
        Trimmed ribbon geometries.
    """

    # 1. Validate inputs
    if curve is None or not curve.IsValid:
        raise ValueError("A valid curve is required.")

    width = float(width)
    thickness = float(thickness)
    trim_z = float(trim_z)

    if width <= 0 or thickness <= 0:
        raise ValueError("Width and thickness must be positive.")

    # 2. Create perpendicular frame
    success, frame = curve.PerpendicularFrameAt(
        curve.Domain.T0
    )

    if not success:
        raise ValueError("Cannot create perpendicular frame.")

    # 3. Create rectangular section
    rectangle = rg.Rectangle3d(
        frame,
        rg.Interval(-width / 2.0, width / 2.0),
        rg.Interval(-thickness / 2.0, thickness / 2.0)
    )

    section_curve = rectangle.ToNurbsCurve()

    # 4. Sweep the section along the curve
    sweep = rg.SweepOneRail()
    sweep.ClosedSweep = False

    swept_breps = sweep.PerformSweep(
        curve,
        section_curve
    )

    if not swept_breps:
        raise ValueError("Ribbon sweep failed.")

    # 5. Close ribbon ends
    solids = []

    for brep in swept_breps:

        if brep.IsSolid:
            solid = brep
        else:
            solid = brep.CapPlanarHoles(tolerance)

        if solid is None or not solid.IsValid or not solid.IsSolid:
            raise ValueError("Cannot create a closed ribbon solid.")

        solids.append(solid)

    # 6. Trim ribbon at Z = trim_z
    results = []

    for solid in solids:

        bbox = solid.GetBoundingBox(True)

        # Entirely above the cutting plane
        if bbox.Min.Z >= trim_z - tolerance:
            results.append(solid)
            continue

        # Entirely below the cutting plane
        if bbox.Max.Z <= trim_z + tolerance:
            continue

        # Create a horizontal cutting surface
        padding = 10.0

        plane = rg.Plane(
            rg.Point3d(0, 0, trim_z),
            rg.Vector3d.ZAxis
        )

        cutter = rg.PlaneSurface(
            plane,
            rg.Interval(
                bbox.Min.X - padding,
                bbox.Max.X + padding
            ),
            rg.Interval(
                bbox.Min.Y - padding,
                bbox.Max.Y + padding
            )
        ).ToBrep()

        # Split ribbon into upper and lower parts
        pieces = solid.Split(cutter, tolerance)

        if not pieces:
            raise ValueError(
                "Ribbon intersects the cutting plane, "
                "but splitting failed."
            )

        # Keep only pieces above the plane
        upper_count = 0

        for piece in pieces:

            piece_bbox = piece.GetBoundingBox(True)

            if piece_bbox.Min.Z >= trim_z - tolerance:

                # Close the newly cut surface if possible
                if not piece.IsSolid:
                    capped = piece.CapPlanarHoles(tolerance)

                    if capped is not None:
                        piece = capped

                if piece.IsValid:
                    results.append(piece)
                    upper_count += 1

        if upper_count == 0:
            raise ValueError(
                "No upper ribbon section was produced. "
                "Check the cutting plane and geometry."
            )

    return results