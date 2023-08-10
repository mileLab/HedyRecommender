from dataclasses import fields, asdict

import pytest
from pytest import approx

from common.typedef import RangeFloat
from recommender.parameters.parameterTypeRegistry import ParameterTypeRegistry
from recommender.preferences.preferenceImportance import instantiate_preferences
from recommender.preferences.preferenceTypeRegistry import PreferenceTypeRegistry
from recommender.recommenderFunctionality import perform_recommendation, additional_validation
from recommender.typedefs.generated_input_types import Parameters, get_parameter_metadata
from recommender.typedefs.io_types import Input, ComponentInformation, SupplierInformation, DemandInformation
from recommender.typedefs.typedef import NO_CATEGORY


def empty_demand_general():
    InputParametersBaseDemand = ParameterTypeRegistry.registry['Demand']["CUTTING"]
    InputPreferencesBase = PreferenceTypeRegistry.registry["CUTTING"]
    param_dem = InputParametersBaseDemand()

    pref_dem = InputPreferencesBase()
    dem_information = DemandInformation("CUTTING", asdict(param_dem), asdict(pref_dem))
    return dem_information


def empty_supplier_general(id: str):
    InputParametersBaseSupplier = ParameterTypeRegistry.registry['Supplier']["CUTTING"]
    InputPreferencesBase = PreferenceTypeRegistry.registry["CUTTING"]
    param_sup = InputParametersBaseSupplier()

    pref_sup = InputPreferencesBase()
    sup_information = SupplierInformation("CUTTING", id, asdict(param_sup),asdict(pref_sup))
    return sup_information


def empty_demand_pcb():
    InputParametersBaseDemand = ParameterTypeRegistry.registry['Demand']["PCB_ASSEMBLY"]
    InputPreferencesBase = PreferenceTypeRegistry.registry["PCB_ASSEMBLY"]
    param_dem = InputParametersBaseDemand()

    pref_dem = InputPreferencesBase()
    dem_information = DemandInformation("PCB_ASSEMBLY", param_dem, pref_dem)
    return dem_information


def empty_supplier_pcb(id: str):
    InputParametersBaseSupplier = ParameterTypeRegistry.registry['Supplier']["PCB_ASSEMBLY"]
    InputPreferencesBase = PreferenceTypeRegistry.registry["PCB_ASSEMBLY"]
    param_sup = InputParametersBaseSupplier()

    pref_sup = InputPreferencesBase()
    sup_information = SupplierInformation("PCB_ASSEMBLY", id, param_sup, pref_sup)
    return sup_information


def test_generic_only_parameters():
    suppliers = [empty_supplier_general("s1"), empty_supplier_general("s2")]
    demand = empty_demand_general()

    suppliers[0].parameters.length = RangeFloat(1.0, 3.0)
    suppliers[0].parameters.width = RangeFloat(10, 100)
    suppliers[1].parameters.length = RangeFloat(4.0, 6.0)
    suppliers[1].parameters.width = RangeFloat(1, 5)

    demand.parameters.length = 2.0
    demand.parameters.width = 20

    # to ensure to have a consistent input
    assert get_parameter_metadata("length").category == get_parameter_metadata("width").category
    test_category = get_parameter_metadata("length").category

    inp = Input(components=[
        ComponentInformation(name="test", type="CUTTING", suppliers=[asdict(s) for s in suppliers], demand=asdict(demand))])

    out = perform_recommendation(inp)
    out_comp = out.components[0]

    GenericPrefType = PreferenceTypeRegistry.registry["CUTTING"]

    for s in out_comp.scores:
        assert len(s.failures.preferences.keys()) >= 1
        assert NO_CATEGORY in s.failures.preferences.keys()
        assert len(s.failures.preferences[NO_CATEGORY].failures.keys()) == 1
        assert "ALL" in s.failures.preferences[NO_CATEGORY].failures.keys()

        if s.supplier_id == "s1":
            assert s.score == 1.0
            total_skipped = sum([len(pref_err.skipped.keys()) for pref_err in s.failures.preferences.values()])
            assert total_skipped == len(fields(GenericPrefType))
            for gn, params in s.failures.parameters.items():
                assert len(params.failures.keys()) == 0
                n_params_per_gn = len([f for f in fields(Parameters)
                                       if get_parameter_metadata(f.name).category == gn
                                       and "CUTTING" in get_parameter_metadata(f.name).production_method])
                if gn == test_category:
                    assert len(params.skipped.keys()) == n_params_per_gn - 2
                else:
                    assert len(params.skipped.keys()) == n_params_per_gn
        elif s.supplier_id == "s2":
            assert s.score == -1.0
            for gn, params in s.failures.parameters.items():
                n_params_per_gn = len([f for f in fields(Parameters)
                                       if get_parameter_metadata(f.name).category == gn
                                       and "CUTTING" in get_parameter_metadata(
                        f.name).production_method])
                if gn == test_category:
                    assert len(params.failures.keys()) == 2
                    assert "smaller than lower bound" in params.failures["length"]
                    assert "larger than upper bound" in params.failures["width"]
                    assert len(params.skipped.keys()) == n_params_per_gn - 2
                else:
                    assert len(params.skipped.keys()) == n_params_per_gn


def test_generic_preferences_single_choice():
    suppliers = [empty_supplier_general("s1"), empty_supplier_general("s2"), empty_supplier_general("s3")]
    demand = empty_demand_general()

    suppliers[0].preferences.environmental_tech = [True, False, False]
    suppliers[1].preferences.environmental_tech = [True, False, False]
    suppliers[2].preferences.environmental_tech = [False, True, False]
    suppliers[0].preferences.working_method = [True, False, False]
    suppliers[1].preferences.working_method = [False, True, False]
    suppliers[2].preferences.working_method = [False, True, False]

    suppliers[0].preferences.sustainability_time_price = 1.0
    suppliers[1].preferences.sustainability_time_price = 1.0
    suppliers[2].preferences.sustainability_time_price = 1.0

    demand.preferences.environmental_tech = [True, False, False]
    demand.preferences.working_method = [True, False, False]

    inp = Input(components=[
        ComponentInformation(name="test", type="CUTTING", suppliers=suppliers, demand=demand)])

    out = perform_recommendation(inp)
    out_comp = out.components[0]

    assert out_comp.scores[0].supplier_id == "s1"
    assert out_comp.scores[0].score == 1.0

    assert out_comp.scores[1].supplier_id == "s2"
    assert 0.0 < out_comp.scores[1].score < 1.0

    assert out_comp.scores[2].supplier_id == "s3"
    assert out_comp.scores[2].score == 0.0


def test_generic_preferences_range():
    suppliers = [empty_supplier_general("s1"), empty_supplier_general("s2"), empty_supplier_general("s3")]
    demand = empty_demand_general()

    suppliers[0].preferences.strategic_cooperation = 4.0 / 5
    suppliers[1].preferences.strategic_cooperation = 2.0 / 5
    suppliers[2].preferences.strategic_cooperation = 1.0 / 5

    demand.preferences.strategic_cooperation = 0.0

    inp = Input(components=[
        ComponentInformation(name="test", type="CUTTING", suppliers=suppliers, demand=demand)])

    out = perform_recommendation(inp)
    out_comp = out.components[0]

    assert out_comp.scores[0].supplier_id == "s3"
    assert out_comp.scores[0].score == approx(4.0 / 5)

    assert out_comp.scores[1].supplier_id == "s2"
    assert out_comp.scores[1].score == approx(3.0 / 5)

    assert out_comp.scores[2].supplier_id == "s1"
    assert out_comp.scores[2].score == approx(1 / 5)


def test_pcb_input():
    suppliers = [empty_supplier_pcb("s1"), empty_supplier_pcb("s2")]
    demand = empty_demand_pcb()

    inp = Input(components=[
        ComponentInformation(name="test", type="PCB_ASSEMBLY", suppliers=suppliers, demand=demand)])
    valid_inp = additional_validation(inp)

    assert type(valid_inp.components[0].demand.parameters) == ParameterTypeRegistry.registry['Demand']["PCB_ASSEMBLY"].__dataclass__
    assert type(valid_inp.components[0].suppliers[0].parameters) == ParameterTypeRegistry.registry['Supplier']["PCB_ASSEMBLY"].__dataclass__
    assert type(valid_inp.components[0].suppliers[1].parameters) == ParameterTypeRegistry.registry['Supplier']["PCB_ASSEMBLY"].__dataclass__
    assert type(valid_inp.components[0].demand.preferences) == PreferenceTypeRegistry.registry["PCB_ASSEMBLY"].__dataclass__
    assert type(valid_inp.components[0].suppliers[0].preferences) == PreferenceTypeRegistry.registry["PCB_ASSEMBLY"].__dataclass__
    assert type(valid_inp.components[0].suppliers[1].preferences) == PreferenceTypeRegistry.registry["PCB_ASSEMBLY"].__dataclass__


@pytest.mark.parametrize("range_value,expected", [(0.0, 0.0), (0.3, 0.3), (1.0, 1.0)])
def test_importance_value(range_value, expected):
    suppliers = [empty_supplier_general("s1")]
    demand = empty_demand_general()

    suppliers[0].preferences.sustainability_time_price = range_value

    dependent_parameters = ["environmental_tech", "balance", "interest_arrears", "inspection_record",
                            "cancellation_conditions", "domain_knowledge"]

    preference_metadata_instance = instantiate_preferences(preference_metadata=demand.preferences.derived_from,
                                                           demand_values=demand.preferences,
                                                           supplier_values=suppliers[0].preferences,
                                                           production_method="CUTTING")

    for dp in dependent_parameters:
        assert getattr(preference_metadata_instance, dp).preference_type.importance == expected

    assert getattr(preference_metadata_instance, "contract_volume").preference_type.importance == 1.0


def test_single_choice_preference_ordered():
    suppliers = [empty_supplier_general("s1")]
    demand = empty_demand_general()

    preference_metadata_instance = instantiate_preferences(preference_metadata=demand.preferences.derived_from,
                                                           demand_values=demand.preferences,
                                                           supplier_values=suppliers[0].preferences,
                                                           production_method="CUTTING")

    assert getattr(preference_metadata_instance, "advanced_measurement").preference_type.ordered
    assert not getattr(preference_metadata_instance, "environmental_tech").preference_type.ordered


def test_dependencies_0():
    suppliers = [empty_supplier_general("s1")]
    demand = empty_demand_general()

    suppliers[0].preferences.sustainability_time_price = 0.0
    suppliers[0].preferences.environmental_tech = [True, False]
    suppliers[0].preferences.balance = 1000
    suppliers[0].preferences.interest_arrears = RangeFloat(1, 10)
    suppliers[0].preferences.inspection_record = False
    suppliers[0].preferences.cancellation_conditions = [False, True, True]
    suppliers[0].preferences.domain_knowledge = 0.0

    demand.preferences.sustainability_time_price = 1.0
    demand.preferences.environmental_tech = [False, True]
    demand.preferences.balance = 100
    demand.preferences.interest_arrears = 12
    demand.preferences.inspection_record = True
    demand.preferences.cancellation_conditions = [False, False, False]
    demand.preferences.domain_knowledge = 1.0

    inp = Input(components=[
        ComponentInformation(name="test", type="CUTTING", suppliers=suppliers, demand=demand)])

    out = perform_recommendation(inp)
    out_comp = out.components[0]

    scores_per_category = out_comp.scores[0].scores_per_category

    assert scores_per_category["TECHNOLOGY"] == 1.0
    assert scores_per_category["SPECIAL_KNOWLEDGE"] == 1.0
    assert scores_per_category['ADDITIONAL SERVICES'] == 1.0
    assert scores_per_category['GENERELL_ORDER_PARAMETER'] == 1.0
    assert scores_per_category["MOTIVES_VALUES"] == 0.0  # sustainability_time_price
    assert scores_per_category["FINANCE"] == 0.8333333333333334
    assert scores_per_category["COMPANY_PROFILE"] == 0.800966757837188


def test_dependencies_0_5():
    suppliers = [empty_supplier_general("s1")]
    demand = empty_demand_general()

    suppliers[0].preferences.sustainability_time_price = 0.5
    suppliers[0].preferences.environmental_tech = [True, False]
    suppliers[0].preferences.balance = 1000
    suppliers[0].preferences.interest_arrears = RangeFloat(1, 10)
    suppliers[0].preferences.inspection_record = False
    suppliers[0].preferences.cancellation_conditions = [False, True, True]
    suppliers[0].preferences.domain_knowledge = 0.0

    demand.preferences.sustainability_time_price = 1.0
    demand.preferences.environmental_tech = [False, True]
    demand.preferences.balance = 100
    demand.preferences.interest_arrears = 12
    demand.preferences.inspection_record = True
    demand.preferences.cancellation_conditions = [False, False, False]
    demand.preferences.domain_knowledge = 1.0

    inp = Input(components=[
        ComponentInformation(name="test", type="CUTTING", suppliers=suppliers, demand=demand)])

    out = perform_recommendation(inp)
    out_comp = out.components[0]

    scores_per_category = out_comp.scores[0].scores_per_category

    assert scores_per_category["TECHNOLOGY"] == 0.25
    assert scores_per_category["SPECIAL_KNOWLEDGE"] == 0.5
    assert scores_per_category['ADDITIONAL SERVICES'] == 0.25
    assert scores_per_category['GENERELL_ORDER_PARAMETER'] == 0.5
    assert scores_per_category["MOTIVES_VALUES"] == 0.5  # sustainability_time_price
    assert scores_per_category["FINANCE"] == 0.7607257743127308
    assert scores_per_category["COMPANY_PROFILE"] == 0.7063202766025848


def test_dependencies_1():
    suppliers = [empty_supplier_general("s1")]
    demand = empty_demand_general()

    suppliers[0].preferences.sustainability_time_price = 1
    suppliers[0].preferences.environmental_tech = [True, False]
    suppliers[0].preferences.balance = 1000
    suppliers[0].preferences.interest_arrears = RangeFloat(1, 10)
    suppliers[0].preferences.inspection_record = False
    suppliers[0].preferences.cancellation_conditions = [False, True, True]
    suppliers[0].preferences.domain_knowledge = 0.0

    demand.preferences.sustainability_time_price = 1.0
    demand.preferences.environmental_tech = [False, True]
    demand.preferences.balance = 100
    demand.preferences.interest_arrears = 12
    demand.preferences.inspection_record = True
    demand.preferences.cancellation_conditions = [False, False, False]
    demand.preferences.domain_knowledge = 1.0

    inp = Input(components=[
        ComponentInformation(name="test", type="CUTTING", suppliers=suppliers, demand=demand)])

    out = perform_recommendation(inp)
    out_comp = out.components[0]

    scores_per_category = out_comp.scores[0].scores_per_category

    assert scores_per_category["TECHNOLOGY"] == 0.0
    assert scores_per_category["SPECIAL_KNOWLEDGE"] == 0.0
    assert scores_per_category['ADDITIONAL SERVICES'] == 0.0
    assert scores_per_category['GENERELL_ORDER_PARAMETER'] == 0.0
    assert scores_per_category["MOTIVES_VALUES"] == 1.0  # sustainability_time_price
    assert scores_per_category["FINANCE"] == 0.6944444444444444
    assert scores_per_category["COMPANY_PROFILE"] == 0.6171017361346637
