import dataclasses

from common.typedef import Range
from recommender.parameters.parameterGeneration import generate_demand_supplier_dataclass
from recommender.parameters.parameterMetadata import ParameterMetadata
from recommender.typedefs.typedef import ComparisonType
from tests.recommender.meta_informations.typedefs import all_methods, bool_inclusive_all, value_to_range, \
    bool_exclusive_all, \
    range_to_value, ProductionMethod

_packaging_field = dataclasses.field(
    default=ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                              comparison=ComparisonType.INCLUSIVE,
                              demand_type=bool, supplier_type=bool, category="PCBComponents"))
_packaging_size_field = dataclasses.field(
    default=ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value, comparison=ComparisonType.IS_IN,
                              demand_type=Range[float], supplier_type=Range[float], category="PCBComponents"))


@dataclasses.dataclass
class Parameters:
    material: ParameterMetadata = ParameterMetadata(production_method=all_methods, comparison=ComparisonType.IS_IN,
                                                    demand_type=str, supplier_type=list[str], category="GeneralOrder")
    packaging: ParameterMetadata = bool_inclusive_all(category="GeneralOrder")
    amount: ParameterMetadata = value_to_range(int, category="GeneralOrder")
    component_material_procurement: ParameterMetadata = bool_inclusive_all(category="GeneralOrder")
    length: ParameterMetadata = value_to_range(float, category="GeneralOrder")
    width: ParameterMetadata = value_to_range(float, category="GeneralOrder")
    height: ParameterMetadata = value_to_range(float, category="GeneralOrder")
    tolerance: ParameterMetadata = ParameterMetadata(production_method=all_methods,
                                                     comparison=ComparisonType.GREATER_EQU,
                                                     demand_type=float, supplier_type=float, category="GeneralOrder")
    surface_quality: ParameterMetadata = bool_inclusive_all(category="GeneralOrder")
    price_volatility: ParameterMetadata = bool_exclusive_all(category="GeneralOrder")
    amount_order: ParameterMetadata = ParameterMetadata(production_method=all_methods, comparison=ComparisonType.IS_IN,
                                                        demand_type=Range[int],
                                                        supplier_type=Range[int], category="GeneralOrder")
    single_order: ParameterMetadata = bool_inclusive_all(category="GeneralOrder")
    serial_production: ParameterMetadata = bool_inclusive_all(category="GeneralOrder")
    prototype: ParameterMetadata = bool_inclusive_all(category="GeneralOrder")
    new_product: ParameterMetadata = bool_inclusive_all(category="GeneralOrder")
    reference_offer: ParameterMetadata = bool_inclusive_all(category="GeneralOrder")
    supplier_failure: ParameterMetadata = bool_inclusive_all(category="GeneralOrder")
    benchmarking: ParameterMetadata = bool_inclusive_all(category="GeneralOrder")

    employees_total: ParameterMetadata = range_to_value(int, category="CustomerProfile")
    employees_production: ParameterMetadata = range_to_value(int, category="CustomerProfile")
    employees_development: ParameterMetadata = range_to_value(int, category="CustomerProfile")
    employees_qs_qm: ParameterMetadata = range_to_value(int, category="CustomerProfile")
    sales: ParameterMetadata = range_to_value(int, category="CustomerProfile")
    balance: ParameterMetadata = range_to_value(int, category="CustomerProfile")

    control_after_production: ParameterMetadata = bool_inclusive_all(category="TermsAndConditions")
    overdelivery: ParameterMetadata = bool_inclusive_all(category="TermsAndConditions")
    validity_of_quotation: ParameterMetadata = ParameterMetadata(production_method=all_methods,
                                                                 comparison=ComparisonType.LESS_EQU,
                                                                 demand_type=int,
                                                                 supplier_type=int,
                                                                 category="TermsAndConditions")  # Offer must be valid at least for 14 days
    contract_volume: ParameterMetadata = value_to_range(int, category="TermsAndConditions")
    reservation_rights: ParameterMetadata = bool_exclusive_all(category="TermsAndConditions")
    change_requests: ParameterMetadata = bool_inclusive_all(category="TermsAndConditions")
    outline_agreement: ParameterMetadata = bool_inclusive_all(category="TermsAndConditions")
    outline_agreement_take_ordered_amount: ParameterMetadata = bool_exclusive_all(
        category="TermsAndConditions")  # I do not want to take the ordered amount per year
    outline_agreement_minimal_amount: ParameterMetadata = bool_exclusive_all(
        category="TermsAndConditions")  # I dont want to have a minimal amount
    low_amount_addition: ParameterMetadata = bool_exclusive_all(
        category="TermsAndConditions")  # I dont want to have a low amount price addition
    long_term_cooperation: ParameterMetadata = bool_inclusive_all(category="TermsAndConditions")

    ce: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    ul: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    weee: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    sampling: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    sample_amount: ParameterMetadata = ParameterMetadata(production_method=all_methods,
                                                         comparison=ComparisonType.LESS_EQU,
                                                         demand_type=int,
                                                         supplier_type=int,
                                                         category="QualityAndCertification")  # supplier needs to do more samples than demand requests
    ce_conformity: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    adherence_to_schedules: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    production_functioning_test: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    inspection_equipment: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    zero_error_strategy: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    quality_management_system: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    quality_management_system_improvements: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    checking_of_outgoing_goods: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    aoi_check: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                     comparison=ComparisonType.INCLUSIVE, demand_type=bool,
                                                     supplier_type=bool, category="QualityAndCertification")
    time_archiving: ParameterMetadata = ParameterMetadata(production_method=all_methods,
                                                          comparison=ComparisonType.LESS_EQU,
                                                          demand_type=int,
                                                          supplier_type=int,
                                                          category="QualityAndCertification")  # supplier needs keep more years than demand requests
    checks_with_proper_tools: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    test_marking: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    audit_system: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    audit_process: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    audit_product: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    quality_management_handbook: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    additional_audits: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    deviation_quality: ParameterMetadata = bool_exclusive_all(
        category="QualityAndCertification")  # I dont want to accept deviation of quality
    rework: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    objection_8D_report: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    calculation_dependent_on_customersegment: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")

    technical_meeting: ParameterMetadata = bool_inclusive_all(category="ExtraServices")
    contact_preference: ParameterMetadata = ParameterMetadata(production_method=all_methods,
                                                              comparison=ComparisonType.IS_IN,
                                                              demand_type=str, supplier_type=list[str],
                                                              category="ExtraServices")
    optimization_manufactoring: ParameterMetadata = bool_inclusive_all(category="ExtraServices")
    design_check_error_correction: ParameterMetadata = bool_inclusive_all(category="ExtraServices")
    certification: ParameterMetadata = bool_inclusive_all(category="ExtraServices")
    consulting_material: ParameterMetadata = bool_inclusive_all(category="ExtraServices")
    consulting_production_method: ParameterMetadata = bool_inclusive_all(category="ExtraServices")
    PCB_supply: ParameterMetadata = bool_inclusive_all(category="QualityAndCertification")
    mold_accuracy: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.MACHINING_GEOM_CUT.value,
                                                         comparison=ComparisonType.LESS_EQU, demand_type=float,
                                                         supplier_type=float,
                                                         category="MachiningGeomCut")  # supplier requires this accuracy
    solder_paste_mask: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                             comparison=ComparisonType.INV_INCLUSIVE, demand_type=bool,
                                                             supplier_type=bool,
                                                             category="PCBGeneral")  # supplier requires this
    assembly_sides: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                          comparison=ComparisonType.LESS_EQU, demand_type=int,
                                                          supplier_type=int, category="PCBGeneral")
    xray_check: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                      comparison=ComparisonType.INCLUSIVE, demand_type=bool,
                                                      supplier_type=bool, category="PCBGeneral")
    etest_check: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                       comparison=ComparisonType.INCLUSIVE, demand_type=bool,
                                                       supplier_type=bool, category="PCBGeneral")
    netlist: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                   comparison=ComparisonType.INV_INCLUSIVE, demand_type=bool,
                                                   supplier_type=bool, category="PCBGeneral")
    rohs_conformity: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                           comparison=ComparisonType.INCLUSIVE, demand_type=bool,
                                                           supplier_type=bool, category="PCBGeneral")
    rfid_embedded: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                         comparison=ComparisonType.INV_INCLUSIVE, demand_type=bool,
                                                         supplier_type=bool, category="PCBGeneral")
    impedance_control: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                             comparison=ComparisonType.INCLUSIVE, demand_type=bool,
                                                             supplier_type=bool, category="PCBGeneral")
    number_layers: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                         comparison=ComparisonType.LESS_EQU, demand_type=int,
                                                         supplier_type=int, category="PCBGeneral")
    single_panel: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                        comparison=ComparisonType.INCLUSIVE, demand_type=bool,
                                                        supplier_type=bool, category="PCBPanel")
    multiple_panel: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                          comparison=ComparisonType.INCLUSIVE, demand_type=bool,
                                                          supplier_type=bool, category="PCBPanel")
    mixed_panel: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                       comparison=ComparisonType.INCLUSIVE, demand_type=bool,
                                                       supplier_type=bool, category="PCBPanel")
    inner_milling: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                         comparison=ComparisonType.INCLUSIVE, demand_type=bool,
                                                         supplier_type=bool, category="PCBPanel")
    panel_boundary: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                          comparison=ComparisonType.GREATER_EQU, demand_type=float,
                                                          supplier_type=float, category="PCBPanel")
    board_contour_type: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                              comparison=ComparisonType.IS_IN, demand_type=str,
                                                              supplier_type=list[str], category="PCBPanel")
    beveling_type: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                         comparison=ComparisonType.IS_IN, demand_type=str,
                                                         supplier_type=list[str], category="PCBPanel")
    edge_plating: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                        comparison=ComparisonType.INCLUSIVE, demand_type=bool,
                                                        supplier_type=bool, category="PCBPanel")

    drill_sizes: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                       comparison=ComparisonType.IS_IN, demand_type=Range[float],
                                                       supplier_type=Range[float], category="PCBDrills")
    drill_size_PTH: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                          comparison=ComparisonType.IS_IN, demand_type=Range[float],
                                                          supplier_type=Range[float], category="PCBDrills")
    drill_size_NPTH: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                           comparison=ComparisonType.IS_IN, demand_type=Range[float],
                                                           supplier_type=Range[float], category="PCBDrills")
    drill_size_via: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                          comparison=ComparisonType.IS_IN, demand_type=Range[float],
                                                          supplier_type=Range[float], category="PCBDrills")
    n_NPTH: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                  comparison=ComparisonType.LESS_EQU, demand_type=int,
                                                  supplier_type=int, category="PCBDrills")

    board_type: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                      comparison=ComparisonType.IS_IN, demand_type=str,
                                                      supplier_type=list[str], category="PCBMaterial")
    copper_layer_material: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                                 comparison=ComparisonType.IS_IN, demand_type=str,
                                                                 supplier_type=list[str], category="PCBMaterial")
    copper_layer_thickness: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                                  comparison=ComparisonType.IS_IN,
                                                                  demand_type=Range[float], supplier_type=Range[float],
                                                                  category="PCBMaterial")
    trace_width: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                       comparison=ComparisonType.IS_IN, demand_type=Range[float],
                                                       supplier_type=Range[float], category="PCBMaterial")
    clearance: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                     comparison=ComparisonType.GREATER_EQU, demand_type=float,
                                                     supplier_type=float, category="PCBMaterial")
    prepreg_material: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                            comparison=ComparisonType.IS_IN, demand_type=str,
                                                            supplier_type=list[str], category="PCBMaterial")
    prepreg_thickness: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                             comparison=ComparisonType.IS_IN, demand_type=Range[float],
                                                             supplier_type=Range[float], category="PCBMaterial")
    core_material: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                         comparison=ComparisonType.IS_IN, demand_type=str,
                                                         supplier_type=list[str], category="PCBMaterial")
    core_thickness: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                          comparison=ComparisonType.IS_IN, demand_type=Range[float],
                                                          supplier_type=Range[float], category="PCBMaterial")
    cti_value: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                     comparison=ComparisonType.IS_IN, demand_type=Range[float],
                                                     supplier_type=Range[float], category="PCBMaterial")
    solder_mask: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                       comparison=ComparisonType.INCLUSIVE, demand_type=bool,
                                                       supplier_type=bool, category="PCBMaterial")
    solder_color: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                        comparison=ComparisonType.IS_IN, demand_type=str,
                                                        supplier_type=list[str], category="PCBMaterial")
    solder_mask_method: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                              comparison=ComparisonType.IS_IN, demand_type=str,
                                                              supplier_type=list[str], category="PCBMaterial")
    solder_mask_clearance: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                                 comparison=ComparisonType.GREATER_EQU,
                                                                 demand_type=float, supplier_type=float,
                                                                 category="PCBMaterial")
    legend_printing: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                           comparison=ComparisonType.INCLUSIVE, demand_type=bool,
                                                           supplier_type=bool, category="PCBMaterial")
    board_surface: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                         comparison=ComparisonType.IS_IN, demand_type=str,
                                                         supplier_type=list[str], category="PCBMaterial")
    service_print: ParameterMetadata = ParameterMetadata(production_method=ProductionMethod.PCB_ASSEMBLY.value,
                                                         comparison=ComparisonType.IS_IN, demand_type=str,
                                                         supplier_type=list[str], category="PCBMaterial")

    two_terminal: ParameterMetadata = _packaging_field
    through_hole: ParameterMetadata = _packaging_field
    surface_mount: ParameterMetadata = _packaging_field
    chip_carrier: ParameterMetadata = _packaging_field
    pin_grid_array: ParameterMetadata = _packaging_field
    flat_package: ParameterMetadata = _packaging_field
    small_outline_ic: ParameterMetadata = _packaging_field
    chip_scale: ParameterMetadata = _packaging_field
    ball_grid_array: ParameterMetadata = _packaging_field
    small_count: ParameterMetadata = _packaging_field
    multi_chip: ParameterMetadata = _packaging_field
    t_capacitor: ParameterMetadata = _packaging_field
    a_capacitor: ParameterMetadata = _packaging_field
    non_packaged: ParameterMetadata = _packaging_field
    two_terminal_size: ParameterMetadata = _packaging_size_field
    through_hole_size: ParameterMetadata = _packaging_size_field
    surface_mount_size: ParameterMetadata = _packaging_size_field
    chip_carrier_size: ParameterMetadata = _packaging_size_field
    pin_grid_array_size: ParameterMetadata = _packaging_size_field
    flat_package_size: ParameterMetadata = _packaging_size_field
    small_outline_ic_size: ParameterMetadata = _packaging_size_field
    chip_scale_size: ParameterMetadata = _packaging_size_field
    ball_grid_array_size: ParameterMetadata = _packaging_size_field
    small_count_size: ParameterMetadata = _packaging_size_field
    multi_chip_size: ParameterMetadata = _packaging_size_field
    t_capacitor_size: ParameterMetadata = _packaging_size_field
    a_capacitor_size: ParameterMetadata = _packaging_size_field
    non_packaged_size: ParameterMetadata = _packaging_size_field
    component_size: ParameterMetadata = _packaging_size_field


# generate all possible preference categories
parameter_categories = list({getattr(Parameters, f.name).category for f in dataclasses.fields(Parameters)})

# generate the preference input types for all production methods
parameter_input_types_demand, parameter_input_types_supplier = generate_demand_supplier_dataclass(Parameters,
                                                                                                  production_methods=all_methods)
