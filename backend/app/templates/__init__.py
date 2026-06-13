from app.models import TemplateInfo
from app.templates.transformer_short_circuit import TEMPLATE_ID, TransformerShortCircuitTemplate

DEFAULT_TEMPLATE_ID = TEMPLATE_ID

_TEMPLATES = {
    TEMPLATE_ID: TransformerShortCircuitTemplate(),
}


def list_templates() -> list[dict[str, str]]:
    return [template.info().model_dump() for template in _TEMPLATES.values()]


def get_template(template_id: str = DEFAULT_TEMPLATE_ID) -> TransformerShortCircuitTemplate:
    return _TEMPLATES[template_id]


def template_infos() -> list[TemplateInfo]:
    return [template.info() for template in _TEMPLATES.values()]
