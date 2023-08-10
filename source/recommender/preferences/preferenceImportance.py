from dataclasses import fields
from typing import Type

from recommender.preferences.preferenceBase import PreferenceBase
from recommender.preferences.preferenceMetadata import PreferenceMetadata
from recommender.typedefs.io_types import InputPreferences
from recommender.typedefs.typedef import DominantParent


def extract_importance_input_for_children(child: PreferenceMetadata, demand_values: InputPreferences,
                                          supplier_values: InputPreferences) -> float:
    current_name = child.parent.name
    if child.dominant_side == DominantParent.DEMAND:
        return read_input_value(demand_values, current_name)
    if child.dominant_side == DominantParent.SUPPLIER:
        return read_input_value(supplier_values, current_name)
    if child.dominant_side == DominantParent.BOTH:
        return 0.5 * (read_input_value(demand_values, current_name) + read_input_value(supplier_values, current_name))


def read_input_value(values: InputPreferences, current_name: str) -> float:
    value = getattr(values, current_name)
    return 1.0 if value is None else float(value)


def instantiate_preferences(preference_metadata: Type[PreferenceBase], demand_values: InputPreferences,
                            supplier_values: InputPreferences, production_method: str) -> PreferenceBase:
    preference_metadata_instance = preference_metadata()

    for f in fields(preference_metadata_instance):

        current: PreferenceMetadata = getattr(preference_metadata_instance, f.name)
        if production_method not in current.production_method:
            continue
        if len(current.children) == 0:
            continue

        if not hasattr(current.preference_type, 'deduce_importance'):
            raise RuntimeError(
                f"Preference {current.name} of type {current.preference_type.__name__} does not support dependent"
                f" preferences. Select a different preference type.")

        for child in current.children:
            importance_input = extract_importance_input_for_children(child, demand_values, supplier_values)
            child.preference_type.importance = current.preference_type.deduce_importance(importance_input)

    return preference_metadata_instance
