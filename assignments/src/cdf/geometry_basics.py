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

def courtyard(nx=34, ny=24, size=250., ring_count=3):
    if nx<26 or ny<20 or nx%2 or ny%2 or size<=0 or ring_count not in (2,3,4):
        raise ValueError("Use even dimensions of at least 26 × 20, a positive module and 2–4 rings.")
    cx,cy=(nx-2)/2,(ny-2)/2
    masks=set()
    for i in range(1,nx-2):
        for j in range(1,ny-2):
            x,y=abs(i-cx),abs(j-cy)
            d=min(i,j,nx-2-i,ny-2-j)
            rhombus=x/(nx*.255)+y/(ny*.40)
            campus = (x-nx*.35)**2/(nx*.112)**2 + (y-ny*.17)**2/(ny*.161)**2
            is_band=1<=d<2
            is_center=rhombus<1 and int(rhombus*ring_count*2)%2==0
            is_side=campus<1 and (campus<.18 or campus>.53)
            is_weave=(abs(x-nx*.255)+abs(y-ny*.32))<3 and (i+j)%2==0
            if is_band or is_center or is_side or is_weave:
                masks.add((i,j))

    tiles,segments=[],[]
    lookup=defaultdict(list)
    ports=[(1,0),(0,1),(-1,0),(0,-1)] # E, N, W, S in counter-clockwise order
    for i in range(nx):
        for j in range(ny):
            corners=[(i,j-1),(i,j),(i-1,j),(i-1,j-1)]
            occupied=[p in masks for p in corners]
            active=[k for k in range(4) if occupied[k]!=occupied[(k+1)%4]]
            # The doubled coordinates make the shared ports exact.
            keys=[(2*i+1+dx,2*j+1+dy) for dx,dy in ports]
            if len(active)==0:
                family,pairs="bud",[]
            elif len(active)==2:
                family="pass" if (active[1]-active[0])==2 else "turn"
                pairs=[tuple(active)]
            else:
                family="split"
                pairs=[(0,1),(2,3)] if occupied[1] else [(1,2),(3,0)]

            x,y=abs(i-(nx-1)/2),abs(j-(ny-1)/2)
            if min(i,j,nx-1-i,ny-1-j)<3:
                zone="frame"
            elif x/(nx*.28)+y/(ny*.46)<1.16:
                zone="medallion"
            else:
                zone="field"
            tiles.append((i,j,zone,family,sum(occupied)))

            center=((i+.5)*size,(j+.5)*size)
            for u,v in pairs:
                a,b=[tuple(k*size/2 for k in keys[index]) for index in (u,v)]
                if family=="pass":
                    handles=[tuple(.61*p+.39*c for p,c in zip(q,center)) for q in (a,b)]
                else:
                    handles=[tuple(.448*p+.552*c for p,c in zip(q,center)) for q in (a,b)]
                idx=len(segments)
                segments.append(dict(keys=(keys[u],keys[v]), control=[a,*handles,b], zone=zone))
                lookup[keys[u]].append((idx,0))
                lookup[keys[v]].append((idx,1))

    # Each segment acts as a local agent. It reads only its two neighbours.
    neighbours=[tuple(next(j for j,_ in lookup[key] if j!=i) for key in seg["keys"])
                for i,seg in enumerate(segments)]
    labels=list(range(len(segments)))
    while True:
        updated=[min(labels[i],labels[left],labels[right])
                 for i,(left,right) in enumerate(neighbours)]
        if updated==labels:
            break
        labels=updated
    # The converged label is the smallest segment ID in a circuit.
    cycles=[]
    for root in sorted(set(labels)):
        cycle=[]
        node=(root,0)
        while not cycle or node[0]!=root:
            idx,entry=node
            cycle.append(node)
            exit_port=segments[idx]["keys"][1-entry]
            node=next(port for port in lookup[exit_port] if port[0]!=idx)
        cycles.append(cycle)
    families={family for _,_,_,family,_ in tiles}
    return dict(nx=nx,ny=ny,size=size,tiles=tiles,segments=segments,cycles=cycles,families=families)


PALETTE = {
    "frame": ((28,48,53),(37,60,63)),
    "medallion": ((36,67,65),(50,84,77)),
    "field": ((218,203,174),(237,222,192)),
}
INK=((223,158,89),(250,218,147),(136,88,55))


def tile_color(zone,count):
    return PALETTE[zone][int(count>=2)]


def loop_color(data, cycle):
    zones=[data["segments"][index]["zone"] for index,_ in cycle]
    return INK[0 if all(z=="frame" for z in zones) else 1 if "medallion" in zones else 2]


def sprig(size):
    """Recursive tip growth with rotated, scaled children and a clearance check."""
    nodes=[((0.,-.25*size),.027*size)]
    stems=[]
    def grow(parent, heading, step, generation):
        if generation==0:
            return
        x,y=nodes[parent][0]
        end=(x+step*cos(heading),y+step*sin(heading))
        radius=.027*size*(.75**(4-generation))
        if max(abs(c) for c in end)+radius>.40*size:
            return
        if any(dist(end,point)<radius+r+.012*size for point,r in nodes):
            return
        child=len(nodes)
        nodes.append((end,radius))
        stems.append(((x,y),end))
        for turn in (-.65,.65):
            grow(child,heading+turn,step*.64,generation-1)
    grow(0,pi/2,.21*size,4)
    return stems,nodes


def select_plan(target=40):
    """Compare three ring counts by proximity to a target circuit count."""
    candidates=[courtyard(ring_count=k) for k in (2,3,4)]
    return min(candidates,key=lambda design:abs(len(design["cycles"])-target))


def add_floor(doc, geo, attr, ring_count=None):
    data=select_plan() if ring_count is None else courtyard(ring_count=ring_count)
    size=data["size"]
    def p(x,y,z=0):
        return geo.Point3d(x,y,z)
    for i,j,zone,family,count in data["tiles"]:
        x,y=i*size,j*size
        tile=geo.NurbsSurface.Create(3,False,2,2,2,2)
        tile.KnotsU.CreateUniformKnots(1.)
        tile.KnotsV.CreateUniformKnots(1.)
        joint=size*.006
        for u in range(2):
            for v in range(2):
                a=x+joint+(size-2*joint)*u
                b=y+joint+(size-2*joint)*v
                if hasattr(tile.Points,"SetPoint"):
                    tile.Points.SetPoint(u,v,p(a,b))
                else:
                    tile.Points[u,v]=geo.Point4d(a,b,0.,1.)
        doc.Objects.AddSurface(tile,attr("{} • {} • {},{}".format(zone,family,i,j),tile_color(zone,count),zone))
        if family=="bud" and (zone!="field" or (i+j)%2==0):
            radius=size*(.145 if zone=="medallion" else .072)
            circle=geo.Circle(p(x+size/2,y+size/2,1.),radius)
            color=INK[2] if zone=="field" else INK[0]
            if zone=="field" and i%3==1 and j%3==1:
                stems,nodes=sprig(size)
                def local(xy):
                    return p(x+size/2+xy[0],y+size/2+xy[1],1.)
                for a,b in stems:
                    doc.Objects.AddLine(local(a),local(b),attr("Recursive sprig",color,"Inlay ornaments"))
                for xy,r in nodes:
                    doc.Objects.AddCircle(geo.Circle(local(xy),r),attr("Dendritic tip",color,"Inlay ornaments"))
            else:
                doc.Objects.AddCircle(circle,attr("Closed bud",color,"Inlay ornaments"))
    for number,cycle in enumerate(data["cycles"],1):
        curve=geo.PolyCurve()
        for index,entry in cycle:
            control=data["segments"][index]["control"]
            if entry:
                control=control[::-1]
            curve.Append(geo.NurbsCurve.Create(False,3,[p(x,y,1.) for x,y in control]))
        doc.Objects.AddCurve(curve,attr("Inlay circuit {:02d}".format(number),loop_color(data,cycle),"Inlay routes"))


if __name__=="__main__":
    try:
        import Rhino
        import scriptcontext as sc
        from System.Drawing import Color
    except ImportError:
        import sys
        import rhino3dm as rh
        doc=rh.File3dm()
        doc.Settings.ModelUnitSystem=rh.UnitSystem.Millimeters
        doc.Strings["Python source"]=Path(__file__).read_text(encoding="utf-8")
        layers={}
        def attr(name,color,layer):
            if layer not in layers:
                obj=rh.Layer()
                obj.Name=layer
                layers[layer]=doc.Layers.Add(obj)
            a=rh.ObjectAttributes()
            a.Name=name
            a.LayerIndex=layers[layer]
            a.ColorSource=rh.ObjectColorSource.ColorFromObject
            a.ObjectColor=(*color,255)
            return a
        add_floor(doc,rh,attr)
        if not doc.Write(sys.argv[1] if len(sys.argv)>1 else "Courtyard_Inlay.3dm",8):
            raise IOError("Could not save the Rhino model.")
    else:
        layers={}
        def attr(name,color,layer):
            if layer not in layers:
                index=sc.doc.Layers.FindByFullPath(layer,-1)
                if index<0:
                    index=sc.doc.Layers.Add(layer,Color.FromArgb(*color))
                layers[layer]=index
            a=Rhino.DocObjects.ObjectAttributes()
            a.LayerIndex=layers[layer]
            a.Name=name
            a.ColorSource=Rhino.DocObjects.ObjectColorSource.ColorFromObject
            a.ObjectColor=Color.FromArgb(*color)
            return a
        add_floor(sc.doc,Rhino.Geometry,attr)
        sc.doc.Views.Redraw()
