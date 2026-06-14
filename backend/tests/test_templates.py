from app.models import RawOcrLine
from app.templates import DEFAULT_TEMPLATE_ID, get_template, list_templates


def line(text: str, top: float, confidence: float = 0.95) -> RawOcrLine:
    return RawOcrLine(
        text=text,
        confidence=confidence,
        box=[[10.0, top], [400.0, top], [400.0, top + 20.0], [10.0, top + 20.0]],
    )


def cell(text: str, center_x: float, center_y: float, confidence: float = 0.95) -> RawOcrLine:
    return RawOcrLine(
        text=text,
        confidence=confidence,
        box=[
            [center_x - 20.0, center_y - 10.0],
            [center_x + 20.0, center_y - 10.0],
            [center_x + 20.0, center_y + 10.0],
            [center_x - 20.0, center_y + 10.0],
        ],
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


def test_transformer_template_extracts_real_ocr_cell_layout() -> None:
    template = get_template(DEFAULT_TEMPLATE_ID)
    raw_lines = [
        cell("中心编号：B260112", 930.8, 349.5),
        cell("序号", 658.0, 390.0),
        cell("LTD-260-0032", 869.0, 387.5),
        cell("委托单位", 140.5, 404.0),
        cell("山东鲁能泰山电力设备有限公司", 397.2, 396.0),
        cell("联结组", 658.0, 438.5),
        cell("YNyn0d11", 877.5, 436.0),
        cell("型号", 140.5, 451.5),
        cell("SSZ22- 63000/110", 343.5, 445.0),
        cell("试验前", 104.5, 660.0),
        cell("1", 150.5, 637.5),
        cell("281.25", 240.0, 637.5),
        cell("281.15", 364.0, 636.0),
        cell("279.05", 504.0, 634.0),
        cell("285.348", 635.5, 632.5),
        cell("17", 151.0, 728.0),
        cell("184.25", 244.0, 729.5),
        cell("184.25", 364.0, 732.0),
        cell("183.15", 496.0, 730.5),
        cell("186.745", 635.0, 726.0),
        cell("分接", 151.0, 821.5),
        cell("AB", 243.0, 822.0),
        cell("BC", 371.5, 822.0),
        cell("CA", 501.0, 822.0),
        cell("试验次数", 641.0, 820.5),
        cell("281.55", 241.0, 966.5),
        cell("281.55", 375.0, 964.5),
        cell("279.55", 494.0, 965.5),
        cell("2", 640.0, 962.5),
        cell("9B", 151.5, 1101.0),
        cell("227.45", 238.0, 1103.0),
        cell("227.55", 370.5, 1104.0),
        cell("226.25", 492.5, 1102.0),
        cell("5", 640.0, 1103.5),
        cell("17", 150.0, 1238.5),
        cell("184.45", 244.0, 1242.5),
        cell("184.55", 368.0, 1240.5),
        cell("183.55", 500.0, 1242.0),
        cell("8", 641.5, 1243.5),
        cell("试验后", 105.0, 1423.5),
        cell("9B", 152.0, 1424.0),
        cell("227.45", 249.0, 1425.0),
        cell("227.45", 423.0, 1429.5),
        cell("226.25", 603.8, 1429.5),
        cell("1", 152.5, 1470.5),
        cell("281.45", 253.0, 1473.0),
        cell("281.45", 426.5, 1477.5),
        cell("279.45", 609.0, 1478.0),
        cell("2026年5月25日", 870.5, 1723.0),
    ]

    result = template.extract(
        raw_lines=raw_lines,
        filename="sample.jpg",
        width=1080,
        height=1920,
    )

    assert result.fields["client"].value == "山东鲁能泰山电力设备有限公司"
    assert result.fields["model"].value == "SSZ22-63000/110"
    assert result.fields["serialNumber"].value == "LTD-260-0032"
    assert result.fields["connectionGroup"].value == "YNyn0d11"
    assert result.fields["date"].value == "2026年5月25日"

    before_rows = result.tables[0].rows
    assert before_rows[0] == {
        "分接": "1",
        "AB": "281.25",
        "BC": "281.15",
        "CA": "279.05",
        "电抗(mH)": "285.348",
    }
    assert before_rows[1]["分接"] == "17"
    assert before_rows[1]["电抗(mH)"] == "186.745"

    during_rows = result.tables[1].rows
    assert during_rows[0]["AB"] == "281.55"
    assert during_rows[0]["试验次数"] == "2"
    assert during_rows[1]["分接"] == "9B"
    assert during_rows[1]["CA"] == "226.25"
    assert during_rows[2]["分接"] == "17"
    assert during_rows[2]["试验次数"] == "8"

    after_rows = result.tables[2].rows
    assert after_rows[0] == {"分接": "9B", "AB": "227.45", "BC": "227.45", "CA": "226.25"}
    assert after_rows[1] == {"分接": "1", "AB": "281.45", "BC": "281.45", "CA": "279.45"}
