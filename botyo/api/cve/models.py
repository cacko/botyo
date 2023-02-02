from typing import Optional
from enum import StrEnum
from pydantic import BaseModel, Extra, Field
from datetime import datetime

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


class CVEReference(BaseModel, extra=Extra.ignore):
    url: str
    source: str

class CVSSV31Data(BaseModel, extra=Extra.ignore):
    version:str
    vectorString:str
    attackVector:str
    attackComplexity:str
    privilegesRequired:str
    userInteraction:str
    scope:str
    confidentialityImpact:str
    integrityImpact:str
    availabilityImpact:str
    baseScore:float
    baseSeverity:str


class CVSSV31(BaseModel, extra=Extra.ignore):
    source: str
    type: str
    cvssData: CVSSV31Data
    exploitabilityScore: float
    impactScore: float

class CVEDescription(BaseModel, extra=Extra.ignore):
    lang: str
    value: str

class CVEMetrics(BaseModel, extra=Extra.ignore):
    cvssMetricV31: list[CVSSV31]

class CVEItem(BaseModel, extra=Extra.ignore):
    id: str
    sourceIdentifier: str
    descriptions: list[CVEDescription]
    metrics: CVEMetrics
    references = list[CVEReference]
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
            return ",".join([x.cvssData.baseSeverity for x in self.metrics.cvssMetricV31])
        return ""

    @property
    def attackVector(self) -> str:
        if self.metrics.cvssMetricV31 is not None:
            return ",".join([x.cvssData.attackVector for x in self.metrics.cvssMetricV31])
        return ""


class Vulnerabilities(BaseModel, extra=Extra.ignore):
    cve: CVEItem


class CVEResponse(BaseModel, extra=Extra.ignore):
    vulnerabilities: list[Vulnerabilities]
    resultsPerPage: int
    startIndex: int
    totalResults: int

    @property
    def ids(self) -> list[str]:
        if not self.totalResults:
            return []
        return list(map(lambda x: x.cve.id, self.vulnerabilities))
