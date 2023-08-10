import itertools

from bokeh.palettes import Paired, Accent3

from extractor.plotting.wktplot import WKTPlot, WKTLayout


def generate_plots(cleaned_closed_geometries, closed_assignment_map, closed_geometries, final_shape,
                   final_shape_with_pads, fp, geometric_objects_initial, obb_all, obb_all_with_pads, open_geometries,
                   removed_rectangles, unassigned_pads):
    plot_before = WKTPlot(title="Input plot_" + fp.package)
    colors = itertools.cycle(Paired[12])
    for shape in geometric_objects_initial:
        plot_before.add_shape(shape, line_color=next(colors))
    for category in closed_geometries.keys():
        for shape in closed_geometries[category]:
            plot_before.add_shape(shape.boundary, line_color=next(colors))
    plot_after = WKTPlot(title="Merged plot_" + fp.package)
    colors = itertools.cycle(Paired[12])
    for category, color in zip(closed_geometries.keys(), Accent3):
        for shape in closed_geometries[category]:
            plot_after.add_shape(shape.boundary, line_color=color, line_width=5)
    for shape in open_geometries:
        plot_after.add_shape(shape, line_color=next(colors), line_width=2)
    plot_final = WKTPlot(title="Final plot_" + fp.package)
    plot_final_with_pads = WKTPlot(title="Final plot_with_pads_" + fp.package)
    colors = itertools.cycle(Paired[12])
    for sublist in cleaned_closed_geometries.values():
        for shape in sublist:
            if shape.boundary != final_shape:
                plot_final.add_shape(shape.boundary, line_color="blue", line_width=5)
    for shape in open_geometries:
        plot_final.add_shape(shape, line_color=next(colors), line_width=3)
        plot_final_with_pads.add_shape(shape, line_color=next(colors), line_width=3)
    for r in removed_rectangles:
        plot_final.add_shape(r.boundary, line_color="green", line_width=5)
    for p in closed_assignment_map.values():
        plot_final.add_shape(p, fill_color="cyan", fill_alpha=0.5)
        plot_final_with_pads.add_shape(p, fill_color="cyan", fill_alpha=0.5)
    for p in unassigned_pads:
        plot_final.add_shape(p, fill_color="orange", fill_alpha=0.5)
        plot_final_with_pads.add_shape(p, fill_color="orange", fill_alpha=0.5)
    plot_final.add_shape(final_shape.boundary, line_color="red", line_width=7)
    plot_final.add_shape(obb_all.boundary, line_color="red", line_width=5, line_dash="dashed")
    for sublist in closed_geometries.values():
        for shape in sublist:
            if shape.boundary != final_shape:
                plot_final_with_pads.add_shape(shape.boundary, line_color="blue", line_width=5)
    plot_final_with_pads.add_shape(final_shape_with_pads.boundary, line_color="red", line_width=7)
    plot_final_with_pads.add_shape(obb_all_with_pads.boundary, line_color="red", line_width=5, line_dash="dashed")
    plot = WKTLayout(title="Package " + fp.package, save_dir="./plots", grid_size=(1, 4))
    plot.add_figure(plot_before.figure, (0, 0))
    plot.add_figure(plot_after.figure, (0, 1))
    plot.add_figure(plot_final.figure, (0, 2))
    plot.add_figure(plot_final_with_pads.figure, (0, 3))
    plot.save()
