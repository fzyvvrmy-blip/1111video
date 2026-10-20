#!/usr/bin/env python3
"""Editable Cairo/Pango phone-screen animation; no generative video API required."""

import argparse
import array
import base64
import io
import json
import math
from pathlib import Path
import subprocess
import wave
import xml.etree.ElementTree as ET

import cairo
import gi

gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
gi.require_version("Rsvg", "2.0")
from gi.repository import Pango, PangoCairo, Rsvg


PART = Path(__file__).resolve().parents[1]
ROOT = PART.parents[1]
W, H = 1080, 2376
PURPLE, INK, MUTED = "#660099", "#22162F", "#82758E"
ARRIVALS = [1.1, 1.9, 2.5, 3.05, 3.55, 4.0]
SIGNS = [9.3, 10.8, 12.1, 13.25]
FAIL = 14.65
SAMPLE_FRAMES = {
    "01-black-start": 0,
    "02-notifications": 5.2,
    "03-enter-orders": 7.4,
    "04-receipts": 12.65,
    "05-insufficient": 15.3,
    "06-refund-failed": 18.1,
    "07-pf-reminder": 23.1,
    "08-ending": 27.7,
    "09-black-end": 29.99,
}


def clamp(v):
    return max(0.0, min(1.0, v))


def ease(v):
    v = clamp(v)
    return 1 - (1 - v) ** 3


def fade(t, start, end):
    return clamp((t - start) / (end - start))


def color(ctx, value, alpha=1):
    value = value.lstrip("#")
    ctx.set_source_rgba(*(int(value[i:i + 2], 16) / 255 for i in (0, 2, 4)), alpha)


def rounded(ctx, x, y, w, h, radius):
    radius = min(radius, w / 2, h / 2)
    ctx.new_sub_path()
    for cx, cy, a in ((x + w - radius, y + radius, -90),
                      (x + w - radius, y + h - radius, 0),
                      (x + radius, y + h - radius, 90),
                      (x + radius, y + radius, 180)):
        ctx.arc(cx, cy, radius, math.radians(a), math.radians(a + 90))
    ctx.close_path()


def box(ctx, x, y, w, h, fill="#FFFFFF", radius=28, alpha=1):
    rounded(ctx, x, y, w, h, radius)
    color(ctx, fill, alpha)
    ctx.fill()


def paint(ctx, surface, alpha=1, x=0, y=0):
    ctx.set_source_surface(surface, x, y)
    ctx.paint_with_alpha(clamp(alpha))


class Renderer:
    def __init__(self, config):
        self.config = config
        self.text_cache = {}
        self.october = cairo.ImageSurface.create_from_png(str(ROOT / "assets/handoff/lockscreen-oct22.png"))
        self.november = self.make_november()
        raw = subprocess.check_output([
            "convert", str(ROOT / "assets/references/xiaowu-avatar.jpg"),
            "-resize", "96x96^", "-gravity", "center", "-extent", "96x96", "PNG:-",
        ])
        self.avatar = cairo.ImageSurface.create_from_png(io.BytesIO(raw))

    def make_november(self):
        doc = ET.parse(PART / "source/lockscreen-oct22.svg")
        ns = "{http://www.w3.org/2000/svg}"
        doc.find(f".//{ns}g[@id='date']/{ns}text").text = self.config["dateForward"]
        doc.find(f".//{ns}g[@id='clock']/{ns}text").text = self.config["clock"]
        image = doc.find(f".//{ns}image")
        image.set("{http://www.w3.org/1999/xlink}href", "data:image/png;base64," +
                  base64.b64encode((ROOT / "assets/handoff/lockscreen-wallpaper.png").read_bytes()).decode())
        handle = Rsvg.Handle.new_from_data(ET.tostring(doc.getroot()))
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, W, H)
        ctx = cairo.Context(surface)
        viewport = Rsvg.Rectangle()
        viewport.x, viewport.y, viewport.width, viewport.height = 0, 0, W, H
        handle.render_document(ctx, viewport)
        self.text(ctx, self.config["weekLabel"], 540, 561, 29, MUTED, align="center")
        return surface

    def text(self, ctx, text, x, y, size=32, fill=INK, bold=False, align="left", width=None, alpha=1):
        key = (text, size, fill, bold, width)
        if key not in self.text_cache:
            layout = PangoCairo.create_layout(ctx)
            font = Pango.FontDescription("Noto Sans CJK SC")
            font.set_absolute_size(size * Pango.SCALE)
            font.set_weight(Pango.Weight.BOLD if bold else Pango.Weight.NORMAL)
            layout.set_font_description(font)
            layout.set_text(str(text), -1)
            if width:
                layout.set_width(int(width * Pango.SCALE))
                layout.set_ellipsize(Pango.EllipsizeMode.END)
            _, logical = layout.get_pixel_extents()
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, max(1, logical.width + 8), max(1, logical.height + 8))
            temp = cairo.Context(surface)
            color(temp, fill)
            PangoCairo.show_layout(temp, layout)
            self.text_cache[key] = (surface, logical.width)
        surface, tw = self.text_cache[key]
        if align == "center":
            x -= tw / 2
        elif align == "right":
            x -= tw
        paint(ctx, surface, alpha, x, y)

    def icon(self, ctx, name, x, y, size=48, fill=PURPLE):
        ctx.save()
        ctx.translate(x, y)
        ctx.scale(size / 48, size / 48)
        ctx.set_line_width(3)
        ctx.set_line_join(cairo.LINE_JOIN_ROUND)
        ctx.set_line_cap(cairo.LINE_CAP_ROUND)
        color(ctx, fill)
        if name == "home":
            ctx.move_to(4, 22); ctx.line_to(24, 5); ctx.line_to(44, 22)
            ctx.move_to(10, 20); ctx.line_to(10, 43); ctx.line_to(20, 43)
            ctx.line_to(20, 30); ctx.line_to(29, 30); ctx.line_to(29, 43)
            ctx.line_to(39, 43); ctx.line_to(39, 20); ctx.stroke()
        elif name == "play":
            rounded(ctx, 4, 5, 40, 38, 8); ctx.stroke()
            ctx.move_to(20, 16); ctx.line_to(32, 24); ctx.line_to(20, 32); ctx.close_path(); ctx.fill()
        elif name == "message":
            rounded(ctx, 4, 5, 40, 31, 10); ctx.stroke()
            ctx.move_to(15, 36); ctx.line_to(12, 44); ctx.line_to(26, 36); ctx.stroke()
            for px in (15, 24, 33):
                ctx.arc(px, 21, 1.5, 0, math.tau); ctx.fill()
        elif name == "cart":
            ctx.move_to(1, 6); ctx.line_to(8, 6); ctx.line_to(15, 32); ctx.line_to(39, 32)
            ctx.move_to(11, 13); ctx.line_to(43, 13); ctx.line_to(39, 26); ctx.line_to(15, 26); ctx.stroke()
            for px in (18, 35):
                ctx.arc(px, 41, 3, 0, math.tau); ctx.fill()
        elif name == "profile":
            ctx.arc(24, 24, 23, 0, math.tau); ctx.fill()
            color(ctx, "#FFFFFF"); ctx.set_line_width(3)
            ctx.arc(24, 25, 11, 0.15, math.pi - 0.15); ctx.stroke()
        else:
            rounded(ctx, 9, 3, 30, 42, 6); ctx.stroke()
            for yy in (14, 22, 30):
                ctx.move_to(17, yy); ctx.line_to(31, yy); ctx.stroke()
        ctx.restore()

    def notification(self, ctx, order, y, opacity=1, pf=False, press=0):
        ctx.save()
        ctx.push_group()
        ctx.translate(540, y + 108)
        ctx.scale(1 - 0.015 * press, 1 - 0.015 * press)
        ctx.translate(-540, -(y + 108))
        box(ctx, 64, y + 5, 952, 216 if pf else 198, "#3E2359", 30, 0.07)
        box(ctx, 64, y, 952, 216 if pf else 198, "#FFFFFF", 30, 0.95)
        box(ctx, 90, y + 25, 38, 38, PURPLE, 10)
        self.icon(ctx, "order", 97, y + 31, 24, "#FFFFFF")
        self.text(ctx, "教务处" if pf else "学分专场", 145, y + 25, 26, MUTED)
        self.text(ctx, "现在", 981, y + 27, 24, MUTED, align="right")
        if pf:
            self.text(ctx, "距离本学期P/F申请截止", 96, y + 83, 37, bold=True)
            self.text(ctx, f"还有{self.config['pfDays']}天。", 96, y + 139, 35, PURPLE)
        else:
            self.text(ctx, "您有新的课程订单待签收。", 96, y + 76, 33, bold=True)
            self.text(ctx, order["title"] + " · " + order["detail"], 96, y + 132, 28, MUTED, width=882)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(clamp(opacity))
        ctx.restore()

    def lock_scene(self, ctx, t):
        paint(ctx, self.november)
        current = [i for i, start in enumerate(ARRIVALS) if t >= start]
        if current:
            self.text(ctx, f"待签收 {len(current)}", 1006, 598, 27, PURPLE, align="right")
        for arrival in current:
            movement = sum(ease((t - ARRIVALS[j]) / 0.38) for j in current if j > arrival)
            progress = ease((t - ARRIVALS[arrival]) / 0.4)
            y = 660 + 212 * movement - 150 * (1 - progress)
            index = len(self.config["orders"]) - 1 - arrival
            press = math.sin(math.pi * clamp((t - 5.8) / 0.28)) if arrival == 5 else 0
            self.notification(ctx, self.config["orders"][index], y, progress, press=press)

    def app_header(self, ctx, signed, low=False):
        box(ctx, 0, 0, W, H, "#F3F0FA", 0)
        self.text(ctx, self.config["clock"], 58, 27, 35, bold=True)
        # 与锁屏同样的53%电量，避免切入页面后数字变化。
        self.text(ctx, "53%", 1016, 30, 29, align="right")
        ctx.save(); ctx.arc(95, 151, 42, 0, math.tau); ctx.clip()
        ctx.translate(53, 109); ctx.scale(84 / 96, 84 / 96); paint(ctx, self.avatar); ctx.restore()
        self.text(ctx, "小五同学", 158, 116, 37, bold=True)
        self.text(ctx, "清华大学", 158, 166, 24, PURPLE)
        self.text(ctx, "我的课程", 56, 230, 58, bold=True)
        self.text(ctx, "先用后付", 1022, 253, 29, PURPLE, align="right")

        gradient = cairo.LinearGradient(50, 330, 1030, 518)
        gradient.add_color_stop_rgb(0, 0.40, 0, 0.60)
        gradient.add_color_stop_rgb(1, 0.57, 0.20, 0.77)
        rounded(ctx, 48, 330, 984, 188, 28); ctx.set_source(gradient); ctx.fill()
        self.text(ctx, "睡眠余额", 78, 354, 27, "#EBDDFA")
        self.text(ctx, "余额不足" if low else self.config["sleepBalance"], 78, 397, 42, "#FFFFFF", True)
        self.text(ctx, "头发余额", 593, 354, 27, "#EBDDFA")
        self.text(ctx, self.config["hairBalance"], 593, 397, 42, "#FFFFFF", True)
        for px in (78, 593):
            box(ctx, px, 480, 400, 7, "#FFFFFF", 3, 0.24)
            if not low:
                box(ctx, px, 480, max(8, 400 * (1 - signed / 5)), 7, "#FFFFFF", 3, 0.9)

        self.text(ctx, "全部", 64, 548, 32, MUTED)
        self.text(ctx, "待签收", 238, 548, 34, PURPLE, True)
        box(ctx, 374, 554, 43, 38, PURPLE, 19)
        self.text(ctx, str(6 - signed), 395, 553, 24, "#FFFFFF", align="center")
        self.text(ctx, "已签收", 502, 548, 32, MUTED)
        self.text(ctx, "退课/售后", 749, 548, 32, MUTED)
        box(ctx, 254, 604, 86, 6, PURPLE, 3)

    def navigation(self, ctx):
        box(ctx, 0, 2168, 1080, 208, "#FFFFFF", 0)
        color(ctx, "#E5DFED"); ctx.set_line_width(1)
        ctx.move_to(0, 2168); ctx.line_to(1080, 2168); ctx.stroke()
        for i, (icon, label) in enumerate(zip(
                ["home", "play", "message", "cart", "profile"],
                ["首页", "直播", "消息", "选课车", "我的课表"])):
            x = 108 + i * 216
            self.icon(ctx, icon, x - 30, 2195, 60, PURPLE if i == 4 else INK)
            self.text(ctx, label, x, 2267, 29, PURPLE if i == 4 else INK, i == 4, "center")
        box(ctx, 420, 2340, 240, 7, "#C8C0D0", 3)

    def scroll_position(self, t):
        return sum(344 * ease((t - (start + 0.4)) / 0.65) for start in SIGNS)

    def order_card(self, ctx, index, y, signed, t):
        order = self.config["orders"][index]
        done = index < signed
        box(ctx, 48, y, 984, 322, "#EBE7F0" if done else "#FFFFFF", 26)
        tagfill = MUTED if done else PURPLE
        box(ctx, 74, y + 27, 132, 43, "#E8DDF4", 12)
        self.text(ctx, order["tag"], 140, y + 29, 25, tagfill, align="center")
        self.text(ctx, "已签收" if done else "待签收", 1002, y + 30, 27, tagfill, align="right")
        self.text(ctx, order["title"], 78, y + 91, 44, MUTED if done else INK, True)
        self.text(ctx, order["detail"], 78, y + 157, 29, MUTED, width=886)
        self.text(ctx, "睡眠与头发账户扣款", 78, y + 247, 26, MUTED)
        if done:
            self.text(ctx, "签收完成", 971, y + 244, 29, MUTED, align="right")
        else:
            refund_press = index == 4 and 16.65 < t < 16.9
            box(ctx, 620, y + 225, 164, 66, "#EADDFA" if refund_press else "#F3EDF9", 33)
            self.text(ctx, "申请退课", 702, y + 238, 27, PURPLE, align="center")
            active_time = SIGNS[index] if index < 4 else FAIL
            press = abs(t - active_time) < 0.12
            box(ctx, 805, y + 225 + (3 if press else 0), 197, 66, "#4E0079" if press else PURPLE, 33)
            self.text(ctx, "确认签收", 903, y + 238 + (3 if press else 0), 28, "#FFFFFF", align="center")

    def popup(self, ctx, title, message, button, amount=1, policy=""):
        amount = clamp(amount)
        ctx.save(); ctx.push_group()
        box(ctx, 0, 0, W, H, "#190B28", 0, 0.43)
        scale = 0.94 + 0.06 * ease(amount)
        ctx.translate(540, 1140); ctx.scale(scale, scale); ctx.translate(-540, -1140)
        box(ctx, 116, 863, 848, 575 if policy else 507, "#FFFFFF", 40)
        box(ctx, 488, 917, 104, 104, "#F2E7FB", 52)
        self.text(ctx, "!", 540, 914, 65, PURPLE, True, "center")
        self.text(ctx, title, 540, 1046, 47, INK, True, "center")
        self.text(ctx, message, 540, 1125, 32, MUTED, align="center")
        if policy:
            self.text(ctx, policy, 540, 1190, 29, MUTED, align="center")
        button_y = 1300 if policy else 1232
        box(ctx, 180, button_y, 720, 85, PURPLE, 42)
        self.text(ctx, button, 540, button_y + 16, 33, "#FFFFFF", align="center")
        ctx.pop_group_to_source(); ctx.paint_with_alpha(amount); ctx.restore()

    def app_scene(self, ctx, t):
        signed = sum(t >= start + 0.13 for start in SIGNS)
        self.app_header(ctx, signed, t >= FAIL + 0.13)
        scroll = self.scroll_position(t)
        ctx.save(); ctx.rectangle(0, 628, W, 1538); ctx.clip()
        for index in range(len(self.config["orders"])):
            self.order_card(ctx, index, 642 + index * 344 - scroll, signed, t)
        ctx.restore()
        self.navigation(ctx)
        for start in SIGNS:
            if start + 0.12 <= t < start + 0.92:
                a = min(fade(t, start + 0.12, start + 0.25), 1 - fade(t, start + 0.74, start + 0.92))
                box(ctx, 98, 1987, 884, 105, "#2D1A3D", 27, 0.95 * a)
                self.text(ctx, f"扣款：睡眠{self.config['sleepCost']} · 头发{self.config['hairCost']}",
                          540, 2017, 28, "#FFFFFF", align="center", alpha=a)
        if 14.78 <= t < 16.45:
            a = min(fade(t, 14.78, 14.98), 1 - fade(t, 16.22, 16.45))
            self.popup(ctx, "余额不足", "无法完成扣款", "返回订单", a)
        if t >= 16.96:
            self.popup(ctx, "申请失败", "已超过退课时间。", "知道了", fade(t, 16.96, 17.18),
                       policy="该商品一经选修，概不退换。")

    def draw(self, t, scale=1):
        surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, round(W * scale), round(H * scale))
        ctx = cairo.Context(surface); ctx.scale(scale, scale)
        color(ctx, "#000000"); ctx.paint()
        if 0.6 <= t < 6.1:
            ctx.push_group(); self.lock_scene(ctx, t); ctx.pop_group_to_source()
            ctx.paint_with_alpha(ease((t - 0.6) / 0.45))
        elif 6.1 <= t < 6.85:
            self.lock_scene(ctx, 6.1)
            progress = ease((t - 6.1) / 0.75)
            ctx.save()
            rounded(ctx, 64 * (1 - progress), 660 * (1 - progress),
                    952 + 128 * progress, 198 + (H - 198) * progress, 30 * (1 - progress))
            ctx.clip(); self.app_scene(ctx, 7); ctx.restore()
        elif 6.85 <= t < 20.2:
            ctx.push_group(); self.app_scene(ctx, t); ctx.pop_group_to_source()
            ctx.paint_with_alpha(1 - ease((t - 19.55) / 0.65))
        elif 21 <= t < 25.7:
            ctx.push_group(); paint(ctx, self.october)
            if t >= 21.55:
                p = ease((t - 21.55) / 0.48)
                self.notification(ctx, None, 660 - 90 * (1 - p), p, pf=True)
            ctx.pop_group_to_source()
            ctx.paint_with_alpha(min(ease((t - 21) / 0.5), 1 - ease((t - 24.8) / 0.9)))
        elif t >= 25.7:
            a = min(ease((t - 25.9) / 0.7), 1 - fade(t, 29.2, 29.9))
            self.text(ctx, "愿你的每一学分，", 540, 1012, 65, "#FFFFFF", True, "center", alpha=a)
            self.text(ctx, "都不是冲动消费！", 540, 1120, 65, "#FFFFFF", True, "center", alpha=a)
        surface.flush()
        return surface


def make_audio(out, duration):
    """Original synthetic interface effects, kept as two editable stems."""
    sr = 48000
    notifications = array.array("f", [0]) * int(duration * sr)
    operations = array.array("f", [0]) * int(duration * sr)

    def tone(track, start, length, frequency, gain, decay=6, attack=0.008):
        begin = int(start * sr)
        for i in range(int(length * sr)):
            if begin + i >= len(track):
                break
            t = i / sr
            envelope = min(1, t / attack) * math.exp(-decay * t / length)
            track[begin + i] += gain * envelope * math.sin(math.tau * frequency * t)

    for start in [0.4] + ARRIVALS[1:] + [21.35]:
        tone(notifications, start, 0.75, 880, 0.20, 5)
        tone(notifications, start + 0.055, 0.65, 1320, 0.08, 6)
    for start in [5.8] + SIGNS + [FAIL, 16.25, 16.7]:
        tone(operations, start, 0.065, 600, 0.09, 8, 0.002)
    for start in SIGNS:
        tone(operations, start + 0.13, 0.32, 554, 0.12, 5)
        tone(operations, start + 0.20, 0.25, 415, 0.09, 5)
    for start in [14.8, 17.0]:
        tone(operations, start, 0.22, 240, 0.13, 4)
        tone(operations, start + 0.11, 0.30, 196, 0.11, 5)

    def save(name, tracks):
        samples = array.array("h", (int(max(-0.92, min(0.92, sum(v))) * 32767) for v in zip(*tracks)))
        with wave.open(str(out / name), "wb") as audio:
            audio.setnchannels(1); audio.setsampwidth(2); audio.setframerate(sr)
            audio.writeframes(samples.tobytes())

    save("notifications.wav", [notifications])
    save("operations.wav", [operations])
    save("preview-mix.wav", [notifications, operations])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true", help="只渲染540×1188的节奏预览")
    parser.add_argument("--stills-only", action="store_true", help="只导出关键静帧")
    args = parser.parse_args()
    config = json.loads((PART / "source/animation-v1.json").read_text())
    out = PART / "renders" / config["version"]
    out.mkdir(parents=True, exist_ok=True)
    keyframes = PART / "keyframes" / "animation-v1"
    keyframes.mkdir(parents=True, exist_ok=True)
    renderer = Renderer(config)
    renderer.november.write_to_png(str(keyframes / "lockscreen-nov02-draft.png"))
    for name, timestamp in SAMPLE_FRAMES.items():
        renderer.draw(timestamp).write_to_png(str(keyframes / (name + ".png")))
    print("已生成关键帧", flush=True)
    if args.stills_only:
        return
    make_audio(out, config["duration"])
    scale = 0.5 if args.preview else 1
    width, height, fps = round(W * scale), round(H * scale), config["fps"]
    video = out / ("part03-preview-540p.mp4" if args.preview else "part03-draft-1080x2376.mp4")
    command = ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-f", "rawvideo",
               "-pixel_format", "bgra", "-video_size", f"{width}x{height}", "-framerate", str(fps),
               "-i", "pipe:0", "-i", str(out / "preview-mix.wav"), "-c:v", "libx264",
               "-preset", "veryfast", "-crf", "18", "-threads", "4", "-pix_fmt", "yuv420p",
               "-c:a", "aac", "-b:a", "160k", "-movflags", "+faststart", "-shortest", str(video)]
    process = subprocess.Popen(command, stdin=subprocess.PIPE)
    try:
        for frame in range(round(config["duration"] * fps)):
            surface = renderer.draw(frame / fps, scale)
            process.stdin.write(surface.get_data())
            if frame % (fps * 5) == 0:
                print(f"渲染 {frame / fps:.0f}/{config['duration']} 秒", flush=True)
    finally:
        process.stdin.close()
    if process.wait():
        raise SystemExit("ffmpeg编码失败，请查看上方输出。")
    print(video.relative_to(ROOT).as_posix(), flush=True)
    if not args.preview:
        preview = out / "part03-preview-540p.mp4"
        subprocess.run(["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(video),
                        "-vf", "scale=540:1188", "-c:v", "libx264", "-preset", "veryfast", "-crf", "21",
                        "-threads", "4", "-c:a", "copy", "-movflags", "+faststart", str(preview)], check=True)
        print(preview.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    main()
