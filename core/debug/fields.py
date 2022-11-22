from core import debug, renderer

_custom: dict[str, tuple[str, object]] = {}
def set_custom_field(safename: str, field_name: str, field_value: object):
    _custom[safename] = (field_name, field_value)

def get_fields(*custom_fields: tuple[str, object]) -> list[tuple[str, object]]:
    global _custom
    fields = [
        ("FPS", renderer.get_fps(3)),
        *custom_fields,
        *sorted(_custom.values(), key=lambda fld: fld[0]),
        ("Profiler", "enabled" if debug.profiler.is_enabled() else "disabled")
    ]
    _custom.clear()
    return fields
