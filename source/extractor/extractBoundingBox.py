from OCC.Core.BRepBndLib import brepbndlib_AddOBB, brepbndlib_Add
from OCC.Core.BRepPrimAPI import BRepPrimAPI_MakeBox
from OCC.Core.Bnd import Bnd_OBB, Bnd_Box
from OCC.Core.TopoDS import TopoDS_Shape
from OCC.Core.gp import gp_Pnt, gp_Ax2, gp_Dir, gp_XYZ


def extract_bounding_box_dimensions(shape: TopoDS_Shape, alignment: bool, sort: bool = False) -> list[float]:
    if alignment:
        aabb = _calculate_aabb(shape)
        # aabb_shape = _convert_AABB_box_to_shape(aabb)
        extent = _get_dimensions(aabb)
    else:
        obb = _calculate_obb(shape)
        # obb_shape = _convert_bnd_to_shape(obb)

        extent = [obb.XHSize() * 2., obb.YHSize() * 2., obb.ZHSize() * 2.]

    if sort:
        extent.sort(reverse=True)

    return extent


def _calculate_obb(shape: TopoDS_Shape) -> Bnd_OBB:
    obb = Bnd_OBB()
    brepbndlib_AddOBB(shape, obb, True, True)
    # print(f"calculated OBB: {obb.XHSize() * 2.}, {obb.YHSize() * 2.},{obb.ZHSize() * 2.}")
    return obb


def _calculate_aabb(shape: TopoDS_Shape) -> Bnd_Box:
    aabb = Bnd_Box()
    aabb.SetGap(1e-6)
    brepbndlib_Add(shape, aabb, True)
    dims = _get_dimensions(aabb)
    # print(f"calculated AABB: {dims}")
    return aabb


def _convert_AABB_box_to_shape(bbox: Bnd_Box) -> TopoDS_Shape:
    XMin, YMin, ZMin, XMax, YMax, ZMax = bbox.Get()
    return BRepPrimAPI_MakeBox(gp_Pnt(XMin, YMin, ZMin), gp_Pnt(XMax, YMax, ZMax)).Shape()


def _get_dimensions(bbox: Bnd_Box) -> list[float]:
    XMin, YMin, ZMin, XMax, YMax, ZMax = bbox.Get()
    return [XMax - XMin, YMax - YMin, ZMax - ZMin]


def _convert_bnd_to_shape(theBox: Bnd_OBB) -> TopoDS_Shape:
    aBaryCenter = theBox.Center()
    aXDir = theBox.XDirection()
    aYDir = theBox.YDirection()
    aZDir = theBox.ZDirection()
    aHalfX = theBox.XHSize()
    aHalfY = theBox.YHSize()
    aHalfZ = theBox.ZHSize()

    ax = gp_XYZ(aXDir.X(), aXDir.Y(), aXDir.Z())
    ay = gp_XYZ(aYDir.X(), aYDir.Y(), aYDir.Z())
    az = gp_XYZ(aZDir.X(), aZDir.Y(), aZDir.Z())
    p = gp_Pnt(aBaryCenter.X(), aBaryCenter.Y(), aBaryCenter.Z())
    anAxes = gp_Ax2(p, gp_Dir(aZDir), gp_Dir(aXDir))
    anAxes.SetLocation(gp_Pnt(p.XYZ() - ax * aHalfX - ay * aHalfY - az * aHalfZ))
    aBox = BRepPrimAPI_MakeBox(anAxes, 2.0 * aHalfX, 2.0 * aHalfY, 2.0 * aHalfZ).Shape()
    return aBox
