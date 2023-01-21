from typing import Optional
from enum import StrEnum
from pydantic import BaseModel, Extra, Field


class AttackVector(StrEnum):
    NETWORK = "NETWORK"


class AttackComplexity(StrEnum):
    LOW = "LOW"


class BaseSeverity(StrEnum):
    CRITICAL = "CRITICAL"


class CVSSV2(BaseModel):
    version: str
    vectorString: str
    accessVector: str
    accessComplexity: str
    authentication: str
    confidentialityImpact: str
    integrityImpact: str
    availabilityImpact: str
    baseScore: float = Field(default=7.5)


class ImpactMetricV2(BaseModel, extra=Extra.ignore):
    cvssV2: CVSSV2
    severity: str
    exploitabilityScore: float
    impactScore: float
    acInsufInfo: Optional[bool] = False
    obtainAllPrivilege: Optional[bool] = False
    obtainUserPrivilege: Optional[bool] = False
    obtainOtherPrivilege: Optional[bool] = False
    userInteractionRequired: Optional[bool] = False


class CVSSV3(BaseModel, extra=Extra.ignore):
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


class ImpactMetricV3(BaseModel, extra=Extra.ignore):
    cvssV3: CVSSV3
    exploitabilityScore: float
    impactScore: float


class Impact(BaseModel, extra=Extra.ignore):
    baseMetricV3: Optional[ImpactMetricV3] = None
    baseMetricV2: Optional[ImpactMetricV2] = None


class Configurations(BaseModel, extra=Extra.ignore):
    pass


class CVEMetaData(BaseModel, extra=Extra.ignore):
    ID: str
    ASSIGNER: str


class CVEDescriptionData(BaseModel, extra=Extra.ignore):
    lang: str
    value: str


class CVEDescription(BaseModel, extra=Extra.ignore):
    description_data: list[CVEDescriptionData]


class CVEItem(BaseModel, extra=Extra.ignore):
    data_type: str
    data_format: str
    data_version: str
    CVE_data_meta: CVEMetaData
    description: CVEDescription


class CVEListItem(BaseModel, extra=Extra.ignore):
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
            filter(lambda x: x.lang == "en", self.cve.description.description_data),
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


class CVEResult(BaseModel, extra=Extra.ignore):
    CVE_data_type: Optional[str] = None
    CVE_data_format: Optional[str] = None
    CVE_data_version: Optional[str] = None
    CVE_data_timestamp: Optional[str] = None
    CVE_Items: list[CVEListItem] = None


class CVEResponse(BaseModel, extra=Extra.ignore):
    result: CVEResult
    resultsPerPage: int
    startIndex: int
    totalResults: int

    @property
    def ids(self) -> list[str]:
        if not self.totalResults:
            return []
        return list(map(lambda x: x.cve.CVE_data_meta.ID, self.result.CVE_Items))
