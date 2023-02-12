from enum import StrEnum
from pydantic import BaseModel, Extra
from datetime import datetime
from typing import Optional


class AttackVector(StrEnum):
    NETWORK = "NETWORK"


class AttackComplexity(StrEnum):
    LOW = "LOW"


class BaseSeverity(StrEnum):
    CRITICAL = "CRITICAL"


class CVEReference(BaseModel, extra=Extra.ignore):
    url: str
    source: str


class CVSSV2Data(BaseModel, extra=Extra.ignore):
    version: str
    vectorString: str
    accessVector: str
    accessComplexity: str
    authentication: str
    confidentialityImpact: str
    integrityImpact: str
    availabilityImpact: str
    baseScore: float


class CVSSV2(BaseModel, extra=Extra.ignore):
    source: str
    type: str
    cvssData: CVSSV2Data
    baseSeverity: str
    exploitabilityScore: float
    impactScore: float
    acInsufInfo: bool
    obtainAllPrivilege: bool
    obtainUserPrivilege: bool
    obtainOtherPrivilege: bool
    userInteractionRequired: bool


class CVSSV31Data(BaseModel, extra=Extra.ignore):
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


class CVSSV31(BaseModel, extra=Extra.ignore):
    source: str
    type: Optional[str]
    cvssData: CVSSV31Data
    exploitabilityScore: float
    impactScore: float


class CVEDescription(BaseModel, extra=Extra.ignore):
    lang: str
    value: str


class CVEMetrics(BaseModel, extra=Extra.ignore):
    cvssMetricV31: Optional[list[CVSSV31]]
    cvssMetricV2: Optional[list[CVSSV2]]


class CVEItem(BaseModel, extra=Extra.ignore):
    id: str
    sourceIdentifier: str
    descriptions: list[CVEDescription]
    metrics: CVEMetrics
    references: list[CVEReference]
    published: datetime
    lastModified: datetime

    @property
    def description(self) -> str:
        description = next(
            filter(lambda x: x.lang == "en", self.descriptions),
            None,
        )
        return description.value if description else ""

    @property
    def severity(self) -> str:
        if self.metrics.cvssMetricV31 is not None:
            return ",".join(
                [x.cvssData.baseSeverity for x in self.metrics.cvssMetricV31]
            )
        if self.metrics.cvssMetricV2 is not None:
            return ",".join(
                [x.baseSeverity for x in self.metrics.cvssMetricV2]
            )
        return ""

    @property
    def attackVector(self) -> str:
        if self.metrics.cvssMetricV31 is not None:
            return ",".join(
                [x.cvssData.attackVector for x in self.metrics.cvssMetricV31]
            )
        if self.metrics.cvssMetricV2 is not None:
            return ",".join(
                [x.cvssData.accessVector for x in self.metrics.cvssMetricV2]
            )
        return ""


class Vulnerability(BaseModel, extra=Extra.ignore):
    cve: CVEItem


class CVEResponse(BaseModel, extra=Extra.ignore):
    vulnerabilities: list[Vulnerability]
    resultsPerPage: int
    startIndex: int
    totalResults: int

    @property
    def ids(self) -> list[str]:
        if not self.totalResults:
            return []
        return list(map(lambda x: x.cve.id, self.vulnerabilities))
