from dataclasses import dataclass
from typing import Optional
from dataclasses_json import dataclass_json, Undefined
from enum import Enum


class AttackVector(Enum):
    NETWORK = "NETWORK"


class AttackComplexity(Enum):
    LOW = "LOW"


class BaseSeverity(Enum):
    CRITICAL = "CRITICAL"


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CVSSV2:
    version: str
    vectorString: str
    accessVector: str
    accessComplexity: str
    authentication: str
    confidentialityImpact: str
    integrityImpact: str
    availabilityImpact: str
    baseScore: 7.5


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ImpactMetricV2:
    cvssV2: CVSSV2
    severity: str
    exploitabilityScore: float
    impactScore: float
    acInsufInfo: Optional[bool] = False
    obtainAllPrivilege: Optional[bool] = False
    obtainUserPrivilege: Optional[bool] = False
    obtainOtherPrivilege: Optional[bool] = False
    userInteractionRequired: Optional[bool] = False


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CVSSV3:
    version: str
    vectorString: str
    attackVector: str
    attackComplexity: str
    privilegesRequired: str
    userInteraction: str
    scope: str
    confidentialityImpact: str
    integrityImpact: str
    availabilityImpact: str
    baseScore: float
    baseSeverity: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class ImpactMetricV3:
    cvssV3: CVSSV3
    exploitabilityScore: float
    impactScore: float


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Impact:
    baseMetricV3: Optional[ImpactMetricV3] = None
    baseMetricV2: Optional[ImpactMetricV2] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class Configurations:
    pass


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CVEMetaData:
    ID: str
    ASSIGNER: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CVEDescriptionData:
    lang: str
    value: str


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CVEDescription:
    description_data: list[CVEDescriptionData]


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CVEItem:
    data_type: str
    data_format: str
    data_version: str
    CVE_data_meta: CVEMetaData
    description: CVEDescription


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CVEListItem:
    cve: CVEItem
    configurations: Configurations
    impact: Impact
    publishedDate: str
    lastModifiedDate: str

    @property
    def id(self) -> str:
        return self.cve.CVE_data_meta.ID

    @property
    def description(self) -> str:
        description = next(
            filter(lambda x: x.lang == "en",
                   self.cve.description.description_data),
            None,
        )
        return description.value if description else ""

    @property
    def severity(self) -> str:
        if self.impact.baseMetricV3 is not None:
            return self.impact.baseMetricV3.cvssV3.baseSeverity
        if self.impact.baseMetricV2 is not None:
            return self.impact.baseMetricV2.severity
        return ""

    @property
    def attackVector(self) -> str:
        if self.impact.baseMetricV3 is not None:
            return self.impact.baseMetricV3.cvssV3.attackVector
        if self.impact.baseMetricV2 is not None:
            return self.impact.baseMetricV2.cvssV2.accessVector
        return ""


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CVEResult:
    CVE_data_type: Optional[str] = None
    CVE_data_format: Optional[str] = None
    CVE_data_version: Optional[str] = None
    CVE_data_timestamp: Optional[str] = None
    CVE_Items: list[CVEListItem] = None


@dataclass_json(undefined=Undefined.EXCLUDE)
@dataclass
class CVEResponse:
    result: CVEResult
    resultsPerPage: int
    startIndex: int
    totalResults: int

    @property
    def ids(self) -> list[str]:
        if not self.totalResults:
            return []
        return list(map(lambda x: x.cve.CVE_data_meta.ID,
                        self.result.CVE_Items))
