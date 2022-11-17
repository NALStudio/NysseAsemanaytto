from core import debug, renderer

_custom: list[tuple[str, object]] = []
def add_custom_field(field_name: str, field_value: object):
    _custom.append((field_name, field_value))

def get_fields(*custom_fields: tuple[str, object]) -> list[tuple[str, object]]:
    global _custom
    fields = [
        ("FPS", renderer.get_fps(3)),
        *custom_fields,
        *_custom,
        ("Profiler", "enabled" if debug.profiler.is_enabled() else "disabled")
    ]
    _custom.clear()
    return fields
