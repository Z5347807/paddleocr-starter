from app.models import RawOcrLine
from app.templates import DEFAULT_TEMPLATE_ID, get_template, list_templates


def line(text: str, top: float, confidence: float = 0.95) -> RawOcrLine:
    return RawOcrLine(
        text=text,
        confidence=confidence,
        box=[[10.0, top], [400.0, top], [400.0, top + 20.0], [10.0, top + 20.0]],
    )


def test_list_templates_returns_transformer_template() -> None:
    templates = list_templates()

    assert templates == [
        {
            "id": "transformer_short_circuit_test_record",
            "name": "变压器短路承受能力试验现场记录",
        }
    ]
    assert DEFAULT_TEMPLATE_ID == "transformer_short_circuit_test_record"


def test_transformer_template_extracts_fields_and_tables() -> None:
    template = get_template(DEFAULT_TEMPLATE_ID)
    raw_lines = [
        line("变压器短路承受能力试验现场记录", 10),
        line("中心编号：B260112", 30),
        line("委托单位 山东鲁能泰山电力设备有限公司", 50),
        line("型号 SSZ22-63000/110", 70),
        line("序号 LTD-260-0032", 90),
        line("联结组 YNyn0d11", 110),
        line("试验前 1 281.25 281.15 279.05 285.348", 150),
        line("试验前 9B 227.25 227.25 226.85 230.322", 170),
        line("试验过程中 1 281.45 281.45 279.45 1", 210),
        line("试验后 9B 227.45 227.45 226.25", 260),
        line("2026 年 1 月 25 日", 320),
    ]

    result = template.extract(
        raw_lines=raw_lines,
        filename="sample.jpg",
        width=1080,
        height=1920,
    )

    assert result.documentType == DEFAULT_TEMPLATE_ID
    assert result.fields["centerNumber"].value == "B260112"
    assert result.fields["client"].value == "山东鲁能泰山电力设备有限公司"
    assert result.fields["model"].value == "SSZ22-63000/110"
    assert result.fields["serialNumber"].value == "LTD-260-0032"
    assert result.fields["connectionGroup"].value == "YNyn0d11"
    assert result.fields["date"].value == "2026 年 1 月 25 日"
    assert result.tables[0].id == "before_test_reactance"
    assert result.tables[0].rows[0]["分接"] == "1"
    assert result.tables[0].rows[0]["AB"] == "281.25"
    assert result.tables[1].id == "during_test_reactance"
    assert result.tables[2].id == "after_test_reactance"
    assert result.rawOcr == raw_lines
