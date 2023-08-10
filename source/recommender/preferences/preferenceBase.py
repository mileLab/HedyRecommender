import dataclasses

from recommender.preferences.preferenceGeneration import complete_preference_namings, complete_preference_dependencies


@dataclasses.dataclass
class PreferenceBase:
    def __post_init__(self):
        complete_preference_namings(self)
        complete_preference_dependencies(self)

    @classmethod
    def keys(cls) -> set:
        return {f.name for f in dataclasses.fields(cls)}
