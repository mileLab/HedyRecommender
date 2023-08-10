import dataclasses
from typing import Optional

from recommender.preferences.preferenceTypes import PreferenceTypesTypes
from recommender.typedefs.typedef import DominantParent


@dataclasses.dataclass
class PreferenceMetadata:
    production_method: list[str]
    category: str
    preference_type: PreferenceTypesTypes

    depends_on: Optional[str] = None
    dominant_side: Optional[DominantParent] = None
    description: Optional[str] = None
    parent: Optional["PreferenceMetadata"] = dataclasses.field(default=None, init=False)
    children: Optional[list["PreferenceMetadata"]] = dataclasses.field(default_factory=list, init=False)
    name: Optional[str] = dataclasses.field(default=None, init=False)

    def __post_init__(self):
        if self.depends_on is not None and self.dominant_side is None:
            raise ValueError(
                f"'depends_on' is specified as {self.depends_on}, the 'dominant_side' needs to be specified as well, got 'None'")

        if isinstance(self.production_method, str):
            self.production_method = [self.production_method]
