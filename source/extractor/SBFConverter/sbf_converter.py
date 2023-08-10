import json
import sys
import traceback

try:
    import pcbnew
except ImportError as e:
    print(f"Could not import pcbnew, check environment. Error {e}. Traceback: {traceback.format_exc()}",
          file=sys.stderr)
    sys.exit(1)

# shortcut
ToMM = pcbnew.ToMM

# pad type mapping
pad_types = {pcbnew.PAD_ATTRIB_NPTH: "NPTH", pcbnew.PAD_ATTRIB_PTH: "PTH", pcbnew.PAD_ATTRIB_SMD: "SMD",
             pcbnew.PAD_ATTRIB_CONN: "SMD"}


def get_board_information(board):
    bb = board.ComputeBoundingBox(aBoardEdgesOnly=True)
    w = ToMM(bb.GetWidth())
    h = ToMM(bb.GetHeight())

    return {"width": w, "height": h}


def get_layer_information(board):
    layers = []
    # layerTypes = {pcbnew.LT_POWER: "power", pcbnew.LT_SIGNAL: "signal", pcbnew.LT_MIXED: "mixed",
    #               pcbnew.LT_JUMPER: "jumper", pcbnew.LT_UNDEFINED: "undef"}

    nLayers = pcbnew.PCB_LAYER_ID_COUNT
    for lay in range(0, nLayers):
        if not board.IsLayerEnabled(lay):
            continue

        layer_info = {'is_cu': pcbnew.LSET.AllCuMask().Contains(lay),
                      'is_internal_Cu': pcbnew.LSET.InternalCuMask().Contains(lay),
                      'is_board_tech': pcbnew.LSET.AllBoardTechMask().Contains(lay),
                      'is_tech': pcbnew.LSET.AllTechMask().Contains(lay),
                      'is_front_assembly': pcbnew.LSET.FrontAssembly().Contains(lay),
                      'is_back_assembly': pcbnew.LSET.BackAssembly().Contains(lay),
                      'is_front': pcbnew.LSET.FrontMask().Contains(lay),
                      'is_back': pcbnew.LSET.BackMask().Contains(lay),
                      'is_user': pcbnew.LSET.UserMask().Contains(lay),
                      'is_user_defined': pcbnew.LSET.UserDefinedLayers().Contains(lay),
                      'is_physical': pcbnew.LSET.PhysicalLayersMask().Contains(lay),
                      'id': lay,
                      'name': board.GetLayerName(lay),
                      'name_def': board.GetStandardLayerName(lay),
                      'visible': board.IsLayerVisible(lay)}

        layers.append(layer_info)
    return layers


def get_track_information(board):
    tracks = []
    for item in board.GetTracks():
        if type(item) is pcbnew.PCB_VIA:
            continue
        elif type(item) is pcbnew.PCB_TRACK:
            start = ToMM(item.GetStart())
            end = ToMM(item.GetEnd())
            width = ToMM(item.GetWidth())
            t = "line"
            if type(item) is pcbnew.PCB_ARC:
                t = "arc"

            # print(f" Track {t}: {start} to {end}, width {width} on layer: {item.GetLayer()}")
            tracks.append(
                {"start": [start[0], start[1]],
                 "end": [end[0], end[1]],
                 "width": width, "type": t,
                 "layer": item.GetLayer(),
                 "net": item.GetNetname()
                 }
            )
        else:
            print("Unknown track type    %s" % type(item), file=sys.stderr)
    return tracks


def get_drill_information(board):
    drills = []
    via_types = {pcbnew.VIATYPE_MICROVIA: "via_micro", pcbnew.VIATYPE_THROUGH: "via_through",
                 pcbnew.VIATYPE_BLIND_BURIED: "via_blind_buried"}
    for item in board.GetTracks():
        if type(item) is pcbnew.PCB_VIA:

            pos = ToMM(item.GetPosition())
            diam = ToMM(item.GetDrillValue())
            width = ToMM(item.GetWidth())
            try:
                t = via_types[item.GetViaType()]
            except KeyError:
                t = "undef"

            drills.append(
                {"position": [pos[0], pos[1]],
                 "diameter": diam,
                 "width": width,
                 "type": t,
                 "layers": [item.TopLayer(), item.BottomLayer()],
                 "net": item.GetNetname()}
            )
        elif type(item) is pcbnew.PCB_TRACK:
            continue
        else:
            print("Unknown drill type    %s" % type(item), file=sys.stderr)

    for pad in board.GetPads():
        if pad.GetAttribute() == pcbnew.PAD_ATTRIB_NPTH or pad.GetAttribute() == pcbnew.PAD_ATTRIB_PTH:
            pos = ToMM(pad.GetPosition())
            diam = ToMM(pad.GetDrillSize())
            width = ToMM(pad.GetBoundingBox().GetSize())  # more robust than ToMM(pad.GetSize())
            solderMaskMargin = ToMM(pad.GetSolderMaskMargin())
            try:
                t = pad_types[pad.GetAttribute()]
            except KeyError:
                t = "undef"
            a = ""
            clearance = [ToMM(pad.GetOwnClearance(i, a)) for i in pad.GetLayerSet().Seq()]
            netname = pad.GetNetname()
            drills.append(
                {"position": [pos[0], pos[1]],
                 "diameter": diam,
                 "width": width,
                 "type": t,
                 "net": netname,
                 "solder_mask_margin": solderMaskMargin,
                 "trace_clearance": [min(clearance), max(clearance)]
                 }
            )
    return drills


def get_board_footprints(board):
    footprints = []
    for fp in board.GetFootprints():
        libid = fp.GetFPID().GetUniStringLibId()
        orient = fp.GetOrientationDegrees()
        lay = fp.GetLayer()
        bb_size = ToMM(fp.GetBoundingBox().GetWidth()), ToMM(fp.GetBoundingBox().GetHeight())
        ref = fp.GetReference()
        val = fp.GetValue()
        nets = [p.GetNetname() for p in fp.Pads()]
        drawings = []
        contacts = []
        pos = ToMM(fp.GetPosition())
        orient_rad = fp.GetOrientationRadians()
        for d in fp.GraphicalItems():
            i = d.GetLayer()
            if i < 0:
                continue  # unknown layer
            name = str(d.GetLayerName())
            if isinstance(d, pcbnew.FP_SHAPE) and ("Fab" in name or "Silkscreen" in name):
                # print( d.SHAPE_T_asString() , " -- ")
                s = str(d.SHAPE_T_asString()).lower()
                if "segment" in s:
                    start = ToMM(d.GetStart())
                    end = ToMM(d.GetEnd())
                    drawings.append({"type": "segment", "start": start, "end": end})
                elif "rect" in s:
                    start = ToMM(d.GetStart())
                    end = ToMM(d.GetEnd())
                    drawings.append({"type": "rectangle", "start": start, "end": end})
                elif "arc" in s:
                    start = ToMM(d.GetStart())
                    end = ToMM(d.GetEnd())
                    angle = d.GetArcAngle() / 10.0  # kicad returns the degree in degree*10
                    drawings.append({"type": "arc", "start": start, "end": end, "angle": angle})
                elif "circle" in s:
                    center = ToMM(d.GetCenter())
                    radius = ToMM(d.GetRadius())
                    drawings.append({"type": "circle", "center": center, "radius": radius})
                elif "poly" in s:
                    points = []

                    ps = d.GetPolyShape()
                    for i_outline in range(0, ps.OutlineCount()):
                        outline = ps.Outline(i_outline)
                        for i_point in range(0, outline.PointCount()):
                            points.append(ToMM(outline.GetPoint(i_point).Rotate(-orient_rad)))

                    points = [(p[0] + pos[0], p[1] + pos[1]) for p in points]
                    drawings.append({"type": "polygon", "points": points})
                else:
                    print(f"Unknown shape type {s}!")

        for pad in fp.Pads():
            pad_type = pad_types[pad.GetAttribute()]
            center = ToMM(pad.GetCenter())
            size = [ToMM(pad.GetSizeX()), ToMM(pad.GetSizeY())]
            orientation = pad.GetOrientationDegrees()
            solder_mask_clearance = ToMM(pad.GetSolderMaskMargin()) if pad.IsOnLayer(pcbnew.F_Mask) else None

            contacts.append(
                {"type": pad_type, "center": [center[0], center[1]], "size": size, "orientation": orientation,
                 "solder_mask_clearance": solder_mask_clearance})

        footprints.append({
            "package": libid,
            "orientation": orient,
            "position": pos,
            "layer": lay,
            "dimensions": [bb_size[0], bb_size[1]],
            "reference_name": ref,
            "value_name": val,
            "nets": nets,
            "drawings": drawings,
            "contacts": contacts
        })
    # print(f"id: {id} -- orient: {orient} -- position: {pos} -- layer: {lay} -- area: {area} -- bb_size: {bb_size} -- refName: {ref} -- valueName: {val} -- nPads: {n_pads}")
    return footprints


if len(sys.argv) != 2:
    print("Only a single argument is expected: <path_to_file>", file=sys.stderr)
    sys.exit(-1)

# read in filename from cmd
filename = sys.argv[1]

# load file with pcbnew
try:
    board = pcbnew.LoadBoard(filename, pcbnew.IO_MGR.EAGLE)
except (OSError, FileNotFoundError, FileExistsError, RuntimeError) as e:
    print(f"Could not import Eagle board file. Maybe old binary format?  Error {e}. Traceback {traceback.format_exc()}",
          file=sys.stderr)
    sys.exit(2)

try:
    drills = get_drill_information(board)
except RuntimeError as e:
    print(f"Failed to get drill information. Error {e}. Traceback {traceback.format_exc()}", file=sys.stderr)
    drills = []

try:
    tracks = get_track_information(board)
except RuntimeError as e:
    print(f"Failed to get track information. Error {e}. Traceback {traceback.format_exc()}", file=sys.stderr)
    tracks = []

try:
    layers = get_layer_information(board)
except RuntimeError as e:
    print(f"Failed to get layer information. Error {e}. Traceback {traceback.format_exc()}", file=sys.stderr)
    layers = []

try:
    board_info = get_board_information(board)
except RuntimeError as e:
    print(f"Failed to get board information. Error {e}. Traceback {traceback.format_exc()}", file=sys.stderr)
    board_info = {}

try:
    footprints = get_board_footprints(board)
except RuntimeError as e:
    print(f"Failed to get footprint information. Error {e}. Traceback {traceback.format_exc()}", file=sys.stderr)
    footprints = []

sbf = {'drills': drills,
       'tracks': tracks,
       'layers': layers,
       'board': board_info,
       'footprints': footprints}

# print the result to stdout
print(json.dumps(sbf), file=sys.stdout)
sys.exit(0)
