from __future__ import annotations

import re
from dataclasses import dataclass

from app.models import FieldValue, ImageInfo, RawOcrLine, RecognitionResult, TableData, TemplateInfo, WarningItem

TEMPLATE_ID = "transformer_short_circuit_test_record"
TEMPLATE_NAME = "变压器短路承受能力试验现场记录"


def _confidence(lines: list[RawOcrLine]) -> float:
    if not lines:
        return 0.0
    return round(sum(line.confidence for line in lines) / len(lines), 4)


def _find_after_label(lines: list[RawOcrLine], label: str) -> FieldValue:
    for line in lines:
        if label in line.text:
            value = line.text.replace(label, "", 1)
            value = value.replace("：", " ").replace(":", " ").strip()
            return FieldValue(label=label, value=value, confidence=line.confidence)
    return FieldValue(label=label, value="", confidence=0.0)


def _find_date(lines: list[RawOcrLine]) -> FieldValue:
    pattern = re.compile(r"(\d{4}\s*年\s*\d{1,2}\s*月\s*\d{1,2}\s*日)")
    for line in lines:
        match = pattern.search(line.text)
        if match:
            return FieldValue(label="日期", value=match.group(1), confidence=line.confidence)
    return FieldValue(label="日期", value="", confidence=0.0)


def _extract_table_rows(lines: list[RawOcrLine], marker: str, columns: list[str]) -> list[dict[str, str]]:
    rows: list[dict[str, str]] = []
    numeric_pattern = re.compile(
        rf"{re.escape(marker)}\s+(\S+)\s+([\d.]+)\s+([\d.]+)\s+([\d.]+)(?:\s+([\d.]+))?"
    )
    for line in lines:
        match = numeric_pattern.search(line.text)
        if not match:
            continue
        values = list(match.groups(default=""))
        row = {columns[index]: values[index] for index in range(min(len(columns), len(values)))}
        rows.append(row)
    return rows


@dataclass(frozen=True)
class TransformerShortCircuitTemplate:
    id: str = TEMPLATE_ID
    name: str = TEMPLATE_NAME

    def info(self) -> TemplateInfo:
        return TemplateInfo(id=self.id, name=self.name)

    def extract(
        self,
        raw_lines: list[RawOcrLine],
        filename: str,
        width: int,
        height: int,
    ) -> RecognitionResult:
        before_columns = ["分接", "AB", "BC", "CA", "电抗(mH)"]
        during_columns = ["分接", "AB", "BC", "CA", "试验次数"]
        after_columns = ["分接", "AB", "BC", "CA"]

        fields = {
            "centerNumber": _find_after_label(raw_lines, "中心编号"),
            "client": _find_after_label(raw_lines, "委托单位"),
            "model": _find_after_label(raw_lines, "型号"),
            "serialNumber": _find_after_label(raw_lines, "序号"),
            "connectionGroup": _find_after_label(raw_lines, "联结组"),
            "date": _find_date(raw_lines),
        }

        tables = [
            TableData(
                id="before_test_reactance",
                title="试验前电抗测量",
                columns=before_columns,
                rows=_extract_table_rows(raw_lines, "试验前", before_columns),
            ),
            TableData(
                id="during_test_reactance",
                title="试验过程中电抗测量",
                columns=during_columns,
                rows=_extract_table_rows(raw_lines, "试验过程中", during_columns),
            ),
            TableData(
                id="after_test_reactance",
                title="试验后电抗测量",
                columns=after_columns,
                rows=_extract_table_rows(raw_lines, "试验后", after_columns),
            ),
        ]

        warnings: list[WarningItem] = []
        if any(value.confidence < 0.7 for value in fields.values()) or _confidence(raw_lines) < 0.8:
            warnings.append(
                WarningItem(
                    code="low_confidence",
                    message="部分识别结果置信度较低，请人工确认后再导出。",
                )
            )

        return RecognitionResult(
            documentType=self.id,
            image=ImageInfo(filename=filename, width=width, height=height),
            fields=fields,
            tables=tables,
            rawOcr=raw_lines,
            warnings=warnings,
        )
