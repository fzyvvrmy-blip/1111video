#!/usr/bin/env python3
"""Rebuild the shared wallpaper and October 22 lock screen from local sources."""

from pathlib import Path
import base64
import shutil
import subprocess
import sys
import xml.etree.ElementTree as ET


def main():
    part = Path(__file__).resolve().parents[1]
    repository = part.parents[1]
    handoff = repository / "assets" / "handoff"
    generated = part / "assets" / "wallpaper-generated-v1.png"
    source = part / "source" / "lockscreen-oct22.svg"
    wallpaper = handoff / "lockscreen-wallpaper.png"
    lockscreen = handoff / "lockscreen-oct22.png"

    if not shutil.which("convert"):
        raise SystemExit("需要 ImageMagick 的 convert 命令。依赖见本段 README.md。")
    for family in ("Noto Sans CJK SC", "DejaVu Sans"):
        match = subprocess.check_output(
            ["fc-match", "--format=%{family}", family], text=True
        )
        if family not in match:
            raise SystemExit(f"缺少字体 {family}；当前匹配到 {match}。")

    try:
        import cairo
        import gi

        gi.require_version("Rsvg", "2.0")
        from gi.repository import Rsvg
    except (ImportError, ValueError) as error:
        raise SystemExit("需要 PyGObject、PyCairo 和 librsvg；见本段 README.md。") from error

    handoff.mkdir(parents=True, exist_ok=True)
    # 等比覆盖后居中裁切，保持曲面比例；原始生成图始终保留。
    subprocess.run(
        ["convert", str(generated), "-resize", "1080x2376^", "-gravity", "center",
         "-extent", "1080x2376", "-strip", str(wallpaper)],
        check=True,
    )
    # librsvg禁止读取SVG目录之外的相对图片；只在渲染内存中嵌入壁纸。
    # 保留磁盘上的SVG相对路径，方便编辑器和仓库内复用。
    document = ET.parse(source)
    wallpaper_layer = document.find(".//{http://www.w3.org/2000/svg}image")
    wallpaper_layer.set(
        "{http://www.w3.org/1999/xlink}href",
        "data:image/png;base64," + base64.b64encode(wallpaper.read_bytes()).decode("ascii"),
    )
    handle = Rsvg.Handle.new_from_data(ET.tostring(document.getroot()))
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1080, 2376)
    context = cairo.Context(surface)
    viewport = Rsvg.Rectangle()
    viewport.x, viewport.y, viewport.width, viewport.height = 0, 0, 1080, 2376
    handle.render_document(context, viewport)
    surface.write_to_png(str(lockscreen))
    for asset in (wallpaper, lockscreen):
        print(asset.relative_to(repository).as_posix())


if __name__ == "__main__":
    try:
        main()
    except subprocess.CalledProcessError as error:
        sys.exit(error.returncode)
