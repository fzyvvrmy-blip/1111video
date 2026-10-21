#!/usr/bin/env python3
"""Render the part-two campus lock-screen design inside part three only."""

import argparse
import json
from pathlib import Path
import xml.etree.ElementTree as ET

import cairo
import gi

gi.require_version("Rsvg", "2.0")
from gi.repository import Rsvg

PART = Path(__file__).resolve().parents[1]
NS = "{http://www.w3.org/2000/svg}"


def render(source, destination):
    handle = Rsvg.Handle.new_from_data(ET.tostring(source))
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 1080, 2376)
    viewport = Rsvg.Rectangle()
    viewport.x, viewport.y, viewport.width, viewport.height = 0, 0, 1080, 2376
    handle.render_document(cairo.Context(surface), viewport)
    surface.write_to_png(str(destination))


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", default="source/animation-v3.json", help="相对于本段目录的配置文件")
    args = parser.parse_args()
    config = json.loads((PART / args.config).read_text())
    for suffix, date, weekday, week in (
        ("oct22", "10月22日", "星期四", config["returnWeekLabel"]),
        ("nov02", "11月2日", "星期一", config["weekLabel"]),
    ):
        doc = ET.parse(PART / "source/lockscreen-v2.svg")
        for name, value in (("clock", config["clock"]), ("date", date),
                            ("weekday", weekday), ("week", week)):
            doc.find(f".//{NS}text[@id='{name}']").text = value
        output = PART / "assets" / f"lockscreen-v2-{suffix}.png"
        render(doc.getroot(), output)
        print(output.relative_to(PART))


if __name__ == "__main__":
    main()
