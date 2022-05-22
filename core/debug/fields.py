from core import clock, debug

_custom: list[tuple[str, object]] = []
def add_custom_field(field_name: str, field_value: object):
    _custom.append((field_name, field_value))

def get_fields(*custom_fields: tuple[str, object]) -> list[tuple[str, object]]:
    global _custom
    fields = [
        ("FPS", clock.get_fps(3)),
        ("Profiler", "enabled" if debug.profiler.is_enabled() else "disabled"),
        *custom_fields,
        *_custom
    ]
    _custom.clear()
    return fields
