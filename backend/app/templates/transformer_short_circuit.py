from __future__ import annotations

import re
from dataclasses import dataclass

from app.models import FieldValue, ImageInfo, RawOcrLine, RecognitionResult, TableData, TemplateInfo, WarningItem

TEMPLATE_ID = "transformer_short_circuit_test_record"
TEMPLATE_NAME = "变压器短路承受能力试验现场记录"
HEADER_TEXT = {
    "分接",
    "AB",
    "BC",
    "CA",
    "电抗（mH）",
    "电抗(mH)",
    "试验次数",
    "调试",
    "试验前",
    "试验后",
    "试",
    "验",
    "过",
    "程",
    "中",
}
VALUE_PATTERN = re.compile(r"^(?:\d{1,3}[A-Z]?|[A-Z0-9-]+|\d+(?:\.\d+)?(?:\s*kV)?)$")


def _confidence(lines: list[RawOcrLine]) -> float:
    if not lines:
        return 0.0
    return round(sum(line.confidence for line in lines) / len(lines), 4)


def _center(line: RawOcrLine) -> tuple[float, float]:
    xs = [point[0] for point in line.box]
    ys = [point[1] for point in line.box]
    return sum(xs) / len(xs), sum(ys) / len(ys)


def _normalize_value(value: str) -> str:
    value = value.strip()
    value = re.sub(r"\s*-\s*", "-", value)
    return value


def _find_after_label(lines: list[RawOcrLine], label: str) -> FieldValue:
    for line in lines:
        if label in line.text:
            value = line.text.replace(label, "", 1)
            value = value.replace("：", " ").replace(":", " ").strip()
            if value:
                return FieldValue(label=label, value=_normalize_value(value), confidence=line.confidence)

            label_x, label_y = _center(line)
            same_row_values = [
                candidate
                for candidate in lines
                if candidate is not line
                and label not in candidate.text
                and abs(_center(candidate)[1] - label_y) <= 20
                and _center(candidate)[0] > label_x
            ]
            if same_row_values:
                candidate = min(same_row_values, key=lambda item: _center(item)[0] - label_x)
                return FieldValue(label=label, value=_normalize_value(candidate.text), confidence=candidate.confidence)
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


def _nearest_column(center_x: float, column_centers: dict[str, float]) -> str | None:
    column, distance = min(
        ((name, abs(center_x - expected_x)) for name, expected_x in column_centers.items()),
        key=lambda item: item[1],
    )
    if distance > 65:
        return None
    return column


def _is_table_value(text: str) -> bool:
    if text in HEADER_TEXT:
        return False
    return bool(VALUE_PATTERN.match(text.strip()))


def _extract_rows_by_position(
    lines: list[RawOcrLine],
    y_min: float,
    y_max: float,
    columns: list[str],
    column_centers: dict[str, float],
    row_tolerance: float = 24.0,
) -> list[dict[str, str]]:
    positioned_cells: list[tuple[float, str, str]] = []
    for line in lines:
        center_x, center_y = _center(line)
        if not (y_min <= center_y <= y_max):
            continue
        column = _nearest_column(center_x, column_centers)
        if column is None or not _is_table_value(line.text):
            continue
        positioned_cells.append((center_y, column, _normalize_value(line.text)))

    groups: list[list[tuple[float, str, str]]] = []
    for cell in sorted(positioned_cells, key=lambda item: item[0]):
        if not groups or abs(cell[0] - (sum(item[0] for item in groups[-1]) / len(groups[-1]))) > row_tolerance:
            groups.append([cell])
        else:
            groups[-1].append(cell)

    rows: list[dict[str, str]] = []
    for group in groups:
        row = {column: "" for column in columns}
        for _, column, value in sorted(group, key=lambda item: column_centers[item[1]]):
            row[column] = value
        non_empty_values = [value for value in row.values() if value]
        if len(non_empty_values) >= 2:
            rows.append(row)
    return rows


def _extract_template_table_rows(lines: list[RawOcrLine], table_id: str, columns: list[str]) -> list[dict[str, str]]:
    if table_id == "before_test_reactance":
        return _extract_rows_by_position(
            lines,
            y_min=610,
            y_max=750,
            columns=columns,
            column_centers={"分接": 150, "AB": 240, "BC": 365, "CA": 500, "电抗(mH)": 635},
        )
    if table_id == "during_test_reactance":
        return _extract_rows_by_position(
            lines,
            y_min=900,
            y_max=1310,
            columns=columns,
            column_centers={"分接": 150, "AB": 240, "BC": 370, "CA": 500, "试验次数": 640},
        )
    if table_id == "after_test_reactance":
        return _extract_rows_by_position(
            lines,
            y_min=1410,
            y_max=1495,
            columns=columns,
            column_centers={"分接": 152, "AB": 250, "BC": 425, "CA": 608},
        )
    return []


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
                rows=_extract_table_rows(raw_lines, "试验前", before_columns)
                or _extract_template_table_rows(raw_lines, "before_test_reactance", before_columns),
            ),
            TableData(
                id="during_test_reactance",
                title="试验过程中电抗测量",
                columns=during_columns,
                rows=_extract_table_rows(raw_lines, "试验过程中", during_columns)
                or _extract_template_table_rows(raw_lines, "during_test_reactance", during_columns),
            ),
            TableData(
                id="after_test_reactance",
                title="试验后电抗测量",
                columns=after_columns,
                rows=_extract_table_rows(raw_lines, "试验后", after_columns)
                or _extract_template_table_rows(raw_lines, "after_test_reactance", after_columns),
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
