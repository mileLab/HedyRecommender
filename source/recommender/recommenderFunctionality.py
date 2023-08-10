from dataclasses import asdict, fields, is_dataclass

from common.typedef import Range
from common.typedef import RangeInt, RangeFloat
from recommender.parameters.parameterMetadata import ParameterMetadata
from recommender.parameters.parameterTypeRegistry import ParameterTypeRegistry
from recommender.preferences.preferenceBase import PreferenceBase
from recommender.preferences.preferenceComparison import distance_preference
from recommender.preferences.preferenceImportance import instantiate_preferences
from recommender.preferences.preferenceMetadata import PreferenceMetadata
from recommender.preferences.preferenceTypeRegistry import PreferenceTypeRegistry
from recommender.preferences.preferenceTypes import CustomType, CustomTypeInstance, PreferenceTypes
from recommender.typedefs.generated_input_types import Preferences, all_categories, InputParametersDemand, \
    InputParametersSupplier
from recommender.typedefs.io_types import Input, Output, Score, ComponentScore, InputPreferences
from recommender.typedefs.typedef import ScoreErrors, ParameterErrors, ComparisonErrors, PreferenceErrors, NO_CATEGORY


# this function is used to evaluate the input and perform some preprocessing. Especially convert the input fields to the
# appropriate python classes.
def additional_validation(inp: Input) -> Input:
    for component in inp.components:
        method = component.type
        par_inp_type_d = ParameterTypeRegistry.registry['Demand'][method]
        try:
            component.demand.parameters = par_inp_type_d(**asdict(component.demand.parameters))
        except TypeError as e:
            raise RuntimeError(
                f"Could not convert demand parameter input for component '{component.name}' using production method '{method}' to the desired input class '{par_inp_type_d.__name__}'") from e

        par_inp_type_s = ParameterTypeRegistry.registry['Supplier'][method]
        for supplier in component.suppliers:
            try:
                supplier.parameters = par_inp_type_s(**asdict(supplier.parameters))
            except TypeError as e:
                raise RuntimeError(
                    f"Could not convert supplier parameter input ({supplier.id}) for component '{component.name}' using production method '{method}' to the desired input class '{par_inp_type_s.__name__}'") from e

        pref_inp_type = PreferenceTypeRegistry.registry[method]
        try:
            component.demand.preferences = pref_inp_type(**asdict(component.demand.preferences))
        except TypeError as e:
            raise RuntimeError(
                f"Could not convert demand preference input for component '{component.name}' using production method '{method}' to the desired input class '{pref_inp_type.__name__}'") from e

        for supplier in component.suppliers:
            try:
                supplier.preferences = pref_inp_type(**asdict(supplier.preferences))
            except TypeError as e:
                raise RuntimeError(
                    f"Could not convert supplier preference input ({supplier.id}) for component '{component.name}' using production method '{method}' to the desired input class '{pref_inp_type.__name__}'") from e

    return inp


# main routine for performing the recommendation
def perform_recommendation(inp: Input) -> Output:
    output = Output()
    for component in inp.components:

        scores: list[Score] = []
        for supplier in component.suppliers:
            # evaluate parameters
            validity_parameters, errors_parameters = compare_parameters_demand_supplier(component.demand.parameters,
                                                                                        supplier.parameters,
                                                                                        component.type)

            # evaluate preferences
            score_preferences, score_category, errors_preferences = compare_preferences_demand_supplier(
                component.demand.preferences,
                supplier.preferences,
                component.type)

            # set final score  (-1 for invalid parameters)
            score = score_preferences if validity_parameters else -1.0

            scores.append(Score(score=score, supplier_id=supplier.id, scores_per_category=score_category,
                                failures=ScoreErrors(parameters=errors_parameters, preferences=errors_preferences)))

        # sort each supplier descending by the score
        scores.sort(key=lambda x: x.score, reverse=True)
        output.components.append(ComponentScore(name=component.name, scores=scores))

    return output


def compare_parameters_demand_supplier(demand_parameters: InputParametersDemand,
                                       supplier_parameters: InputParametersSupplier,
                                       production_method: str) -> tuple[bool, ParameterErrors]:
    if not is_dataclass(demand_parameters):
        raise RuntimeError("demand_parameters must be a dataclass")
    if not is_dataclass(supplier_parameters):
        raise RuntimeError("supplier_parameter must be a dataclass")

    metadata_instance = demand_parameters.derived_from()
    parameters = list(asdict(demand_parameters).keys())

    # check if supplier and demand parameters coincide
    if asdict(demand_parameters).keys() != asdict(supplier_parameters).keys():
        raise RuntimeError(f"Parameters of demand datastructure {type(demand_parameters).__name__} "
                           f"and supplier {type(supplier_parameters).__name__} do not match. "
                           f"Got d: {asdict(demand_parameters).keys()} and s: {asdict(supplier_parameters).keys()}")

    # check if metadata_instance is a subset of demand_parameters
    if not all(k in asdict(metadata_instance).keys() for k in parameters):
        raise RuntimeError(f"Parameters of demand/supplier datastructure {type(demand_parameters).__name__} "
                           f"and metadata_class {type(metadata_instance).__name__} do not match."
                           f"Got d/s: {asdict(demand_parameters).keys()} and metadata: {asdict(metadata_instance).keys()}")

    errors: ParameterErrors = {c: ComparisonErrors() for c in all_categories}
    valid = True
    #  evaluate the parameters from a given category
    for p in parameters:

        meta_info: ParameterMetadata = getattr(metadata_instance, p)
        demand = getattr(demand_parameters, p)
        supplier = getattr(supplier_parameters, p)

        # convert RangeInt/RangeFloat to internal Range
        if isinstance(demand, (RangeInt, RangeFloat)):
            demand = Range(**asdict(demand))
        if isinstance(supplier, (RangeInt, RangeFloat)):
            supplier = Range(**asdict(supplier))

        if demand is None or supplier is None:
            errors[meta_info.category].skipped[
                p] = f"Skipped, since either demand or supplier parameter is not provided, got demand: {demand} and suppler: {supplier}"
            continue

        # evaluate
        if production_method not in meta_info.production_method:
            errors[meta_info.category].skipped[
                p] = f"Skipped, since parameter is not applicable for production method '{production_method}', however values are provided."
            continue

        try:
            result = meta_info.cmp_fnc(demand, supplier)

            valid = valid and result.valid
            if result.error is not None:
                errors[meta_info.category].failures[p] = result.error
        except RuntimeError as e:
            errors[meta_info.category].failures[p] = f"Failed to evaluate parameter, error: {e}"
            continue

    # remove error free dicts, note empty dicts evaluate to False
    empty_categories = [c for c in errors.keys() if not bool(errors[c].skipped) and not bool(errors[c].failures)]
    for c in empty_categories:
        errors.pop(c)

    return valid, errors


def compare_preferences_demand_supplier(demand_preferences: InputPreferences, supplier_preferences: InputPreferences,
                                        production_method: str) -> tuple[float, dict[str, float], PreferenceErrors]:
    if not is_dataclass(demand_preferences):
        raise RuntimeError("demand_preferences must be a dataclass")
    if not is_dataclass(supplier_preferences):
        raise RuntimeError("supplier_preferences must be a dataclass")

    # check if supplier and demand parameters coincide
    if asdict(demand_preferences).keys() != asdict(supplier_preferences).keys():
        raise RuntimeError(f"Preferences of demand datastructure {demand_preferences.__name__} "
                           f"and supplier {supplier_preferences.__name__} do not match."
                           f"Got d: {asdict(demand_preferences).keys()} and s: {asdict(supplier_preferences).keys()}")

    # check if metadata_instance is a subset of demand_parameters (additional dummy variable!)
    if not all(k in Preferences.keys() for k in asdict(demand_preferences).keys()):
        raise RuntimeError(f"Preferences of demand/supplier datastructure {demand_preferences.__name__} "
                           f"and metadata_class {Preferences.__name__} do not match."
                           f"Got d/s: {asdict(demand_preferences).keys()} and metadata: {Preferences.keys()}")

    preference_metadata_instance = instantiate_preferences(preference_metadata=demand_preferences.derived_from,
                                                           demand_values=demand_preferences,
                                                           supplier_values=supplier_preferences,
                                                           production_method=production_method)
    errors: PreferenceErrors = {c: ComparisonErrors() for c in all_categories}
    scores_category = evaluate_preference_scores(demand_preferences, supplier_preferences, preference_metadata_instance,
                                                 production_method, errors)

    n_active_category = len(list(filter(lambda x: (x > 0), [len(scores_category[c]) for c in all_categories])))
    if n_active_category == 0:
        errors[NO_CATEGORY].failures["ALL"] = f"No preferences given, returning valid 1.0 for preferences"
        score = 1.0
        score_per_category = {}
    else:
        # value of category is average scores in this category
        score_per_category = {c: sum(scores_category[c]) / len(scores_category[c]) for c in all_categories if
                              len(scores_category[c]) > 0}

        # final value is average of each category
        score = sum(score_per_category.values()) / n_active_category

    # remove error free dicts, note empty dicts evaluate to False
    empty_categories = [c for c in errors.keys() if not bool(errors[c].skipped) and not bool(errors[c].failures)]
    for c in empty_categories:
        errors.pop(c)

    return score, score_per_category, errors


def evaluate_preference_scores(demand_preferences: InputPreferences, supplier_preferences: InputPreferences,
                               preference_metadata_instance: PreferenceBase, production_method: str,
                               errors: PreferenceErrors):
    scores_category: dict[str, list[float]] = {c: [] for c in all_categories}
    for f in fields(demand_preferences):
        p = f.name

        # fetch preference meta information
        meta: PreferenceMetadata = getattr(preference_metadata_instance, p)
        if meta is None:
            raise RuntimeError(f"Metadata is None for parameter {p}, something went terribly wrong")

        # if production method is not applicable skip this entry
        if production_method not in meta.production_method:
            if hasattr(demand_preferences, p) or hasattr(supplier_preferences, p):
                errors[meta.category].skipped[
                    p] = f"Skipped, since preference is not applicable for production method '{production_method}', however values are provided."
            continue

        # create appropriate type for preference evaluation
        if isinstance(meta.preference_type, CustomType):
            demand: PreferenceTypes = CustomTypeInstance(value=getattr(demand_preferences, p),
                                                         base_type=meta.preference_type)
            supplier: PreferenceTypes = CustomTypeInstance(value=getattr(supplier_preferences, p),
                                                           base_type=meta.preference_type)
        else:
            raise RuntimeError("Unknown preference type, must be derived from CustomType")

        if demand.value is None or supplier.value is None:
            errors[meta.category].skipped[
                p] = f"Skipped, since either demand or supplier preference is not provided, got demand: {demand.value} and suppler: {supplier.value}"
            continue

        # evaluate preference and go from distance to similarity
        try:
            score_preference = 1 - distance_preference(demand, supplier)
        except RuntimeError as e:
            errors[meta.category].failures[p] = f"Error in computing preference distance: {e}"
            continue

        # collect individual scores
        scores_category[meta.category].append(score_preference)

    return scores_category
