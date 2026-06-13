from pydantic import BaseModel, Field


class ImageInfo(BaseModel):
    filename: str
    width: int
    height: int


class FieldValue(BaseModel):
    label: str
    value: str
    confidence: float = 0.0
    edited: bool = False


class TableData(BaseModel):
    id: str
    title: str
    columns: list[str]
    rows: list[dict[str, str]]


class RawOcrLine(BaseModel):
    text: str
    confidence: float
    box: list[list[float]]


class WarningItem(BaseModel):
    code: str
    message: str


class RecognitionResult(BaseModel):
    documentType: str
    image: ImageInfo
    fields: dict[str, FieldValue]
    tables: list[TableData]
    rawOcr: list[RawOcrLine]
    warnings: list[WarningItem] = Field(default_factory=list)


class TemplateInfo(BaseModel):
    id: str
    name: str
