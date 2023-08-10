from typing import Union

from pydantic import Field, validator
from pydantic.dataclasses import dataclass

from recommender.parameters.parameterTypeRegistry import ParameterTypeRegistry
from recommender.preferences.preferenceTypeRegistry import PreferenceTypeRegistry
from recommender.typedefs.generated_input_types import InputPreferences, InputParametersDemand, InputParametersSupplier, \
    ProductionMethods, all_production_methods
from recommender.typedefs.typedef import ScoreErrors


@dataclass(init=False)
class SupplierInformation:
    id: str = Field(description="Name/ID of the supplier")
    parameters: InputParametersSupplier = Field(description="Parameters from the supplier")
    preferences: InputPreferences = Field(description="Preferences from the supplier")

    def __init__(self, pm_type: str, id: str, parameters: Union[dict, InputParametersDemand],
                 preferences: Union[dict, InputPreferences]):
        self.id = id
        par_inp_type_s = ParameterTypeRegistry.registry['Supplier'][pm_type]
        pref_inp_type = PreferenceTypeRegistry.registry[pm_type]
        self.parameters = par_inp_type_s(**parameters) if isinstance(parameters, dict) else parameters
        self.preferences = pref_inp_type(**preferences) if isinstance(preferences, dict) else preferences


@dataclass(init=False)
class DemandInformation:
    parameters: InputParametersDemand = Field(description="Parameters from the demand")
    preferences: InputPreferences = Field(description="Preferences from the demand")

    def __init__(self, pm_type: str, parameters: Union[dict, InputParametersDemand],
                 preferences: Union[dict, InputPreferences]):
        par_inp_type_d = ParameterTypeRegistry.registry['Demand'][pm_type]
        pref_inp_type = PreferenceTypeRegistry.registry[pm_type]
        self.parameters = par_inp_type_d(**parameters) if isinstance(parameters, dict) else parameters
        self.preferences = pref_inp_type(**preferences) if isinstance(preferences, dict) else preferences


@dataclass(init=False)
class ComponentInformation:
    name: str = Field(description="Name of the component")
    type: ProductionMethods = Field(description="Type of the production method")
    suppliers: list[SupplierInformation] = Field(description="List of all appropriate supplier parameters")
    demand: DemandInformation = Field(description="Demand information")

    def __init__(self, name: str, type: ProductionMethods, suppliers: Union[list[dict], list[SupplierInformation]],
                 demand: Union[dict, DemandInformation]):
        self.name = name
        self.type = type
        if type not in all_production_methods:
            raise ValueError(f'type must be one of {all_production_methods}, got {type}')

        self.suppliers = [s if isinstance(s, SupplierInformation) else SupplierInformation(type, **s) for s in
                          suppliers]
        self.demand = demand if isinstance(demand, DemandInformation) else DemandInformation(type, **demand)


@dataclass
class Score:
    supplier_id: str = Field(description="Name/ID of the supplier")
    score: float = Field(description="matching score, between 0 and 1")
    failures: ScoreErrors = Field(description="Mapping of parameter to occurred errors")
    scores_per_category: dict[str, float] = Field(description="score for each preference category")


@dataclass
class ComponentScore:
    name: str = Field(description="name of the component")
    scores: list[Score] = Field(description="score for each supplier for this component")


@dataclass
class Input:
    components: list[ComponentInformation] = Field(description="List of all parameters from all components")


@dataclass
class Output:
    components: list[ComponentScore] = Field(default_factory=list,
                                             description="Scores for each component for each supplier")
