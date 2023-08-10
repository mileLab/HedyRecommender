import dataclasses

from recommender.preferences.preferenceBase import PreferenceBase
from recommender.preferences.preferenceGeneration import generate_preference_dataclass
from recommender.preferences.preferenceMetadata import PreferenceMetadata
from recommender.preferences.preferenceTypes import BoolPreference, RangePreference, SingleChoicePreference, \
    MultipleChoicePreference
from recommender.typedefs.typedef import ComparisonType, DominantParent
from tests.recommender.meta_informations.typedefs import all_methods


@dataclasses.dataclass
class Preferences(PreferenceBase):
    communication_types: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY", "GENERIC"], "PRINCIPLE_OPERATION",
                                                                 SingleChoicePreference(ordered=False))
    meeting_types: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY", "GENERIC"], "PRINCIPLE_OPERATION",
                                                           SingleChoicePreference(ordered=False))
    quality_price: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY", "GENERIC"], "QUALITY_AWARENESS",
                                                           BoolPreference(),
                                                           depends_on="low_price", dominant_side=DominantParent.DEMAND)
    quality_importance: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY", "GENERIC"], "QUALITY_AWARENESS",
                                                                RangePreference(),
                                                                depends_on="low_price",
                                                                dominant_side=DominantParent.DEMAND)
    quality_standards: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY", "GENERIC"], "QUALITY_AWARENESS",
                                                               RangePreference(),
                                                               depends_on="low_price",
                                                               dominant_side=DominantParent.DEMAND)
    quality_assurance_program: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY", "GENERIC"], "QUALITY_AWARENESS",
                                                                       BoolPreference(
                                                                           comparison_type=ComparisonType.INCLUSIVE),
                                                                       depends_on="low_price",
                                                                       dominant_side=DominantParent.DEMAND)
    low_price: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY", "GENERIC"], "PRICE",
                                                       BoolPreference(comparison_type=ComparisonType.EXACT_MATCH),
                                                       depends_on="working_method", dominant_side=DominantParent.DEMAND)
    price_sustainability: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "PRICE", RangePreference())
    budget_acceptance_order: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "PRICE", RangePreference())
    price_importance: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "PRICE", RangePreference())
    product_footprint: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "ENVIRONMENTAL_AWARENESS",
                                                               RangePreference())
    regionalism: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "REGIONALISM", RangePreference())
    obligatory_promise: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "RELIABILITY", RangePreference())
    reschedule_important_order: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "RELIABILITY", BoolPreference(
        comparison_type=ComparisonType.INCLUSIVE))
    delivery_guarantee: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "RELIABILITY", RangePreference())
    domain_knowledge: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "SPECIAL_KNOWLEDGE", RangePreference())
    support_customer: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "COLLABORATION", BoolPreference(
        comparison_type=ComparisonType.EXACT_MATCH))
    feedback_customer: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "COLLABORATION", RangePreference())
    delayed_delivery: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "DELIVERY_TIME", RangePreference())
    delivery_assurance_program: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "DELIVERY_TIME",
                                                                        BoolPreference(
                                                                            comparison_type=ComparisonType.EXACT_MATCH))
    sustainability_time_price: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "MOTIVES_VALUES",
                                                                       RangePreference())
    sustainability_efficiency_price: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "MOTIVES_VALUES",
                                                                             RangePreference())
    adaptions_process: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "METHODOLOGY", RangePreference())
    adaptions_orders: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "METHODOLOGY", RangePreference())
    strategic_cooperation: PreferenceMetadata = PreferenceMetadata(["PCB_ASSEMBLY"], "EXPECTATIONS_PARTNER",
                                                                   BoolPreference(
                                                                       comparison_type=ComparisonType.EXACT_MATCH))
    working_method: PreferenceMetadata = PreferenceMetadata(all_methods, "EXPECTATIONS_PARTNER", RangePreference())
    sdg1: PreferenceMetadata = PreferenceMetadata(all_methods, "SUSTAINABILITY_PROFILE",
                                                  MultipleChoicePreference(comparison_type=ComparisonType.EXACT_MATCH))


# generate all possible preference categories
preference_categories = list({getattr(Preferences, f.name).category for f in dataclasses.fields(Preferences)})

# generate the preference input types for all production methods
preference_input_types = generate_preference_dataclass(Preferences, all_methods)

pass
