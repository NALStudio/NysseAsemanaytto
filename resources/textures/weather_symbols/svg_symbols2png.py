import subprocess
import os

INKSCAPE_PATH: str = "C:/Program Files/Inkscape/bin/inkscape.exe"
SIZE: int = 512

origin: str = "./svg"
destination: str = "./png"

os.makedirs(destination, exist_ok=True)

svgs = os.listdir(origin)
for i, path_end in enumerate(svgs):
    path = os.path.join(origin, path_end)
    path_name, path_ext = os.path.splitext(path)
    assert path_ext == ".svg", "Only SVG files are supported!"

    output: str = os.path.join(destination, os.path.basename(path_name) + ".png")

    print(f"Rendering '{path}' to '{output}'... ({i} / {len(svgs)})")
    subprocess.run([INKSCAPE_PATH, '--export-type=png', f'--export-filename={os.path.abspath(output)}', f'--export-width={SIZE}', f'--export-height={SIZE}', os.path.abspath(path)]).check_returncode()
