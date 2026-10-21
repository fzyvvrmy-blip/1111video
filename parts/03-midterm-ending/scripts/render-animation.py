#!/usr/bin/env python3
"""Editable Cairo/Pango phone-screen animation; no generative video API required."""

import argparse
import array
from datetime import date
import io
import json
import math
import random
from pathlib import Path
import subprocess
import wave

import cairo
import gi

gi.require_version("Pango", "1.0")
gi.require_version("PangoCairo", "1.0")
gi.require_version("Rsvg", "2.0")
from gi.repository import Pango, PangoCairo, Rsvg


PART = Path(__file__).resolve().parents[1]
ROOT = PART.parents[1]
W, H = 1080, 2376
PURPLE, BRIGHT, INK, MUTED = "#660099", "#8600ca", "#121020", "#838194"
ARRIVALS = [1.1, 1.65, 2.15, 2.55, 2.9, 3.2, 3.48, 3.72, 3.94, 4.14]
SIGNS = [9.3, 10.8, 12.1, 13.25]
FAIL = 14.65
SAMPLE_FRAMES = {
    "01-black-start": 0,
    "02-notifications": 5.2,
    "03-enter-orders": 7.4,
    "04a-receipt-1": 9.75,
    "04b-receipt-2": 11.25,
    "04-receipts": 12.65,
    "04c-receipt-4": 13.7,
    "05-insufficient": 15.3,
    "05b-return-same-order": 16.6,
    "06-refund-failed": 18.1,
    "07-pf-reminder": 23.1,
    "08-ending": 27.7,
    "09-black-end": 29.99,
}


def receipt_state(config, signed):
    completed = config["orders"][:signed]
    return {
        "sleep": config["sleepBalance"] - sum(o["sleepCost"] for o in completed),
        "hair": config["hairBalance"] - sum(o["hairCost"] for o in completed),
        "pending": len(config["orders"]) - signed,
    }


def validate_config(config):
    """Check the actual upstream contract and the successful/failed ledger."""
    upstream = json.loads((PART / "source/part02-state-v4.json").read_text())
    courses = {c["id"]: c for c in upstream["courses"]}
    assert len(config["orders"]) == len(courses) == 10
    assert {o["courseId"] for o in config["orders"]} == set(courses)
    for order in config["orders"]:
        original = courses[order["courseId"]]
        assert (order["courseTitle"], order["credits"], order["sleepCost"], order["art"]) == (
            original["title"], original["credits"], original["sleep"], original["art"])
        assert order["hairCost"] >= 0
    assert sum(o["credits"] for o in config["orders"]) == config["totalCredits"] == 31
    assert sum(o["sleepCost"] for o in config["orders"]) == config["estimatedSleepCost"] == 18
    assert config["sleepBalance"] == upstream["sleepBalance"] == 6
    assert [o["courseId"] for o in config["orders"][:4]] == config["signedCourseIds"]
    assert config["orders"][4]["courseId"] == config["failedCourseId"]
    ledger = [{"signed": n, **receipt_state(config, n)} for n in range(5)]
    assert all(s["sleep"] >= 0 and s["hair"] >= 0 for s in ledger)
    failed_order = config["orders"][4]
    assert failed_order["sleepCost"] > ledger[-1]["sleep"]
    calendar = config["calendar"]
    anchor, forward = date.fromisoformat(calendar["anchorDate"]), date.fromisoformat(calendar["forwardDate"])
    assert anchor.weekday() == 3 and forward.weekday() == 0
    weeks = ((forward.toordinal() - forward.weekday()) - (anchor.toordinal() - anchor.weekday())) // 7
    assert calendar["anchorWeek"] + weeks == calendar["forwardWeek"] == 8
    assert config["pfDays"] == 1
    assert "【X】" not in json.dumps(config, ensure_ascii=False)
    return {"balances": ledger, "failedCourseId": failed_order["courseId"],
            "failedSleepCost": failed_order["sleepCost"], "failedAttemptDeducts": False,
            "totalCredits": 31, "totalSleepCost": 18, "pfDays": 1, "weeks": [6, 8]}


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
        self.icon_cache = {}
        self.ui = json.loads((PART / "source/ui-v2.json").read_text())
        self.october = cairo.ImageSurface.create_from_png(str(PART / "assets/lockscreen-v2-oct22.png"))
        self.november = cairo.ImageSurface.create_from_png(str(PART / "assets/lockscreen-v2-nov02.png"))
        self.covers = {}
        for order in config["orders"]:
            key = order["art"]
            path = PART / "assets/part02-v4" / (key + ".png")
            if path.exists():
                self.covers[key] = cairo.ImageSurface.create_from_png(str(path))
            else:
                handle = Rsvg.Handle.new_from_file(str(path.with_suffix(".svg")))
                surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, 500, 300)
                viewport = Rsvg.Rectangle()
                viewport.x, viewport.y, viewport.width, viewport.height = 0, 0, 500, 300
                handle.render_document(cairo.Context(surface), viewport)
                self.covers[key] = surface
        raw = subprocess.check_output([
            "convert", str(ROOT / "assets/references/xiaowu-avatar.jpg"),
            "-resize", "96x96^", "-gravity", "center", "-extent", "96x96", "PNG:-",
        ])
        self.avatar = cairo.ImageSurface.create_from_png(io.BytesIO(raw))

    def text(self, ctx, text, x, y, size=32, fill=INK, bold=False, align="left", width=None, alpha=1):
        key = (text, size, fill, bold, width)
        if key not in self.text_cache:
            layout = PangoCairo.create_layout(ctx)
            font = Pango.FontDescription(self.ui["fontFamily"])
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
        aliases = {"play": "live", "message": "chat", "order": "parcel"}
        name = aliases.get(name, name)
        key = (name, size, fill)
        if key not in self.icon_cache:
            path = self.ui["icons"].get(name, self.ui["icons"]["plan"])
            svg = (f'<svg xmlns="http://www.w3.org/2000/svg" width="{size}" height="{size}" '
                   f'viewBox="0 0 24 24" fill="none" stroke="{fill}" stroke-width="1.8" '
                   f'stroke-linecap="round" stroke-linejoin="round">{path}</svg>')
            surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, size, size)
            viewport = Rsvg.Rectangle()
            viewport.x, viewport.y, viewport.width, viewport.height = 0, 0, size, size
            Rsvg.Handle.new_from_data(svg.encode()).render_document(cairo.Context(surface), viewport)
            self.icon_cache[key] = surface
        paint(ctx, self.icon_cache[key], x=x, y=y)

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
            self.text(ctx, f"还有{self.config['pfDays']}天。", 96, y + 139, 42, PURPLE, bold=True)
        else:
            self.text(ctx, "您有新的课程订单待签收。", 96, y + 76, 33, bold=True)
            self.text(ctx, order["title"] + " · " + order["detail"], 96, y + 132, 28, MUTED, width=882)
        ctx.pop_group_to_source()
        ctx.paint_with_alpha(clamp(opacity))
        ctx.restore()

    def touch(self, ctx, t, start, x, y):
        progress = (t - start) / .3
        if 0 <= progress <= 1:
            opacity = math.sin(progress * math.pi)
            radius = 36 + 14 * progress
            color(ctx, "#BC77E5", .15 * opacity)
            ctx.arc(x, y, radius + 10, 0, math.tau); ctx.fill()
            color(ctx, "#FFFFFF", .88 * opacity)
            ctx.arc(x, y, radius, 0, math.tau); ctx.fill_preserve()
            color(ctx, "#A155CF", opacity); ctx.set_line_width(3); ctx.stroke()

    def lock_scene(self, ctx, t):
        paint(ctx, self.november)
        current = [i for i, start in enumerate(ARRIVALS) if t >= start]
        if current:
            self.text(ctx, f"待签收 {len(current)}", 1006, 860, 27, "#FFFFFF", align="right")
        ctx.save(); ctx.rectangle(0, 888, W, 1300); ctx.clip()
        for arrival in current:
            movement = sum(ease((t - ARRIVALS[j]) / 0.38) for j in current if j > arrival)
            progress = ease((t - ARRIVALS[arrival]) / 0.4)
            y = 912 + 212 * movement - 150 * (1 - progress)
            index = len(self.config["orders"]) - 1 - arrival
            press = math.sin(math.pi * clamp((t - 5.8) / 0.28)) if arrival == 9 else 0
            self.notification(ctx, self.config["orders"][index], y, progress, press=press)
        ctx.restore()
        self.touch(ctx, t, 5.8, 820, 1015)

    def app_header(self, ctx, signed):
        state = receipt_state(self.config, signed)
        box(ctx, 0, 0, W, H, "#F6F4FF", 0)
        self.text(ctx, self.config["clock"], 50, 17, 44, bold=True)
        self.icon(ctx, "wifi", 804, 29, 44, INK)
        for i in range(4):
            box(ctx, 870 + i * 10, 66 - i * 8, 6, 10 + i * 8, INK, 1)
        box(ctx, 952, 31, 68, 33, "#85818D", 6)
        box(ctx, 1023, 40, 4, 14, "#85818D", 1)
        self.text(ctx, str(self.config["battery"]), 986, 31, 25, "#FFFFFF", True, "center")
        ctx.save(); ctx.arc(95, 151, 42, 0, math.tau); ctx.clip()
        ctx.translate(53, 109); ctx.scale(84 / 96, 84 / 96); paint(ctx, self.avatar); ctx.restore()
        self.text(ctx, "小五同学", 158, 116, 37, bold=True)
        self.text(ctx, "清华大学", 158, 166, 24, PURPLE)
        self.text(ctx, "我的课表", 56, 230, 58, bold=True)
        self.text(ctx, "先用后付", 1022, 253, 29, PURPLE, align="right")

        box(ctx, 48, 330, 984, 188, "#FFF2EE", 28)
        self.text(ctx, "睡眠余额", 78, 345, 27, "#9A493F")
        self.text(ctx, f"{state['sleep']} 小时", 78, 382, 63, "#CE4937", True)
        self.text(ctx, "头发余额", 650, 345, 27, MUTED)
        self.text(ctx, f"{state['hair']} 根", 650, 392, 45, PURPLE, True)

        self.text(ctx, "全部", 64, 548, 32, MUTED)
        self.text(ctx, "待签收", 238, 548, 34, PURPLE, True)
        box(ctx, 374, 554, 50, 38, BRIGHT, 19)
        self.text(ctx, str(state["pending"]), 399, 553, 24, "#FFFFFF", align="center")
        self.text(ctx, "已签收", 502, 548, 32, MUTED)
        self.text(ctx, "退课/售后", 749, 548, 32, MUTED)
        box(ctx, 254, 604, 86, 6, PURPLE, 3)

    def navigation(self, ctx):
        box(ctx, 0, 2160, 1080, 216, "#FFFFFF", 0)
        color(ctx, "#E5DFED"); ctx.set_line_width(1)
        ctx.move_to(0, 2160); ctx.line_to(1080, 2160); ctx.stroke()
        for i, (icon, label) in enumerate(zip(
                ["home", "play", "message", "cart", "profile"],
                ["首页", "直播", "消息", "选课车", "我的课表"])):
            x = 108 + i * 216
            self.icon(ctx, icon, x - 32, 2178, 64, BRIGHT if i == 4 else INK)
            self.text(ctx, label, x, 2248, 32, BRIGHT if i == 4 else INK, i == 4, "center")
            if i == 2:
                box(ctx, x + 18, 2164, 60, 46, BRIGHT, 23)
                self.text(ctx, str(self.config["messageBadge"]), x + 48, 2164, 28, "#FFFFFF", True, "center")
        color(ctx, "#9996A1"); ctx.set_line_width(4)
        for y in (2324, 2334, 2344):
            ctx.move_to(162, y); ctx.line_to(198, y); ctx.stroke()
        rounded(ctx, 522, 2316, 36, 36, 9); ctx.stroke()
        ctx.move_to(914, 2316); ctx.line_to(880, 2334); ctx.line_to(914, 2352); ctx.close_path(); ctx.stroke()

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
        cover = self.covers[order["art"]]
        ctx.save(); rounded(ctx, 78, y + 91, 104, 104, 14); ctx.clip()
        factor = max(104 / cover.get_width(), 104 / cover.get_height())
        ctx.translate(130 - cover.get_width() * factor / 2, y + 143 - cover.get_height() * factor / 2)
        ctx.scale(factor, factor); paint(ctx, cover, 0.48 if done else 1); ctx.restore()
        self.text(ctx, order["title"], 202, y + 91, 36, MUTED if done else INK, True, width=528)
        self.text(ctx, order["detail"], 202, y + 148, 28, MUTED, width=528)
        self.text(ctx, f"{order['credits']}学分 · {order['category']}", 78, y + 248, 25, MUTED)
        self.text(ctx, f"睡眠{order['sleepCost']}小时", 1002, y + 89,
                  38, MUTED if done else PURPLE, True, align="right")
        self.text(ctx, f"头发{order['hairCost']}根", 1002, y + 145,
                  38, MUTED if done else PURPLE, True, align="right")
        if done:
            self.text(ctx, "签收完成", 971, y + 244, 29, MUTED, align="right")
        else:
            refund_press = index == 4 and 16.65 < t < 16.9
            box(ctx, 620, y + 225, 164, 66, "#EADDFA" if refund_press else "#F3EDF9", 33)
            self.text(ctx, "申请退课", 702, y + 238, 27, PURPLE, align="center")
            active_time = SIGNS[index] if index < 4 else (FAIL if index == 4 else -10)
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
        self.app_header(ctx, signed)
        scroll = self.scroll_position(t)
        ctx.save(); ctx.rectangle(0, 628, W, 1532); ctx.clip()
        for index in range(len(self.config["orders"])):
            self.order_card(ctx, index, 642 + index * 344 - scroll, signed, t)
        ctx.restore()
        self.navigation(ctx)
        for index, start in enumerate(SIGNS):
            if start + 0.12 <= t < start + 0.92:
                a = min(fade(t, start + 0.12, start + 0.25), 1 - fade(t, start + 0.74, start + 0.92))
                box(ctx, 98, 1987, 884, 105, "#2D1A3D", 27, 0.95 * a)
                order = self.config["orders"][index]
                self.text(ctx, f"已扣款：睡眠{order['sleepCost']}小时 · 头发{order['hairCost']}根",
                          540, 2017, 28, "#FFFFFF", align="center", alpha=a)
        if 14.78 <= t < 16.45:
            a = min(fade(t, 14.78, 14.98), 1 - fade(t, 16.22, 16.45))
            remaining = receipt_state(self.config, len(SIGNS))["sleep"]
            required = self.config["orders"][4]["sleepCost"]
            self.popup(ctx, "余额不足", f"需睡眠{required}小时，当前仅剩{remaining}小时。", "返回订单", a)
        if t >= 16.96:
            self.popup(ctx, "申请失败", "已超过退课时间。", "知道了", fade(t, 16.96, 17.18),
                       policy="该商品一经选修，概不退换。")
        for index, start in enumerate(SIGNS):
            y = 642 + index * 344 - self.scroll_position(start) + 258
            self.touch(ctx, t, start, 903, y)
        self.touch(ctx, t, FAIL, 903, 900)
        self.touch(ctx, t, 16.25, 540, 1274)
        self.touch(ctx, t, 16.7, 702, 900)

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
            rounded(ctx, 64 * (1 - progress), 912 * (1 - progress),
                    952 + 128 * progress, 198 + (H - 198) * progress, 30 * (1 - progress))
            ctx.clip(); self.app_scene(ctx, 7); ctx.restore()
        elif 6.85 <= t < 20.2:
            ctx.push_group(); self.app_scene(ctx, t); ctx.pop_group_to_source()
            ctx.paint_with_alpha(1 - ease((t - 19.55) / 0.65))
        elif 21 <= t < 25.7:
            ctx.push_group(); paint(ctx, self.october)
            if t >= 21.55:
                p = ease((t - 21.55) / 0.48)
                self.notification(ctx, None, 912 - 90 * (1 - p), p, pf=True)
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
        rng = random.Random(round(start * 1000))
        for i in range(round(sr * 0.034)):
            t = i / sr
            transient = (0.48 * math.sin(math.tau * 1880 * t) * math.exp(-t / .0048)
                         + .26 * math.sin(math.tau * 3670 * t) * math.exp(-t / .0027)
                         + .12 * rng.uniform(-1, 1) * math.exp(-t / .0019))
            operations[round(start * sr) + i] += .5 * min(1, t / .00024) * transient
    for start in SIGNS:
        tone(operations, start + 0.13, 0.32, 554, 0.12, 5)
        tone(operations, start + 0.20, 0.25, 415, 0.09, 5)
    for start in [14.8, 17.0]:
        tone(operations, start, 0.22, 240, 0.13, 4)
        tone(operations, start + 0.11, 0.30, 196, 0.11, 5)

    def save(name, tracks):
        samples = array.array("h")
        for values in zip(*tracks):
            value = int(max(-0.92, min(0.92, sum(values))) * 32767)
            samples.extend((value, value))
        with wave.open(str(out / name), "wb") as audio:
            audio.setnchannels(2); audio.setsampwidth(2); audio.setframerate(sr)
            audio.writeframes(samples.tobytes())

    save("notifications.wav", [notifications])
    save("operations.wav", [operations])
    save("preview-mix.wav", [notifications, operations])


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--preview", action="store_true", help="只渲染540×1188的节奏预览")
    parser.add_argument("--stills-only", action="store_true", help="只导出关键静帧")
    args = parser.parse_args()
    config = json.loads((PART / "source/animation-v2.json").read_text())
    ledger = validate_config(config)
    subprocess.run(["python3", str(PART / "scripts/render-lockscreen-v2.py")], check=True)
    out = PART / "renders" / config["version"]
    out.mkdir(parents=True, exist_ok=True)
    (out / "receipt-ledger.json").write_text(json.dumps(ledger, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps(ledger, ensure_ascii=False), flush=True)
    keyframes = PART / "keyframes" / "animation-v2"
    keyframes.mkdir(parents=True, exist_ok=True)
    renderer = Renderer(config)
    renderer.november.write_to_png(str(keyframes / "lockscreen-nov02.png"))
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
               "-force_key_frames", "0,20.2,29.9",
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
                        "-force_key_frames", "0,20.2,29.9",
                        "-threads", "4", "-c:a", "copy", "-movflags", "+faststart", str(preview)], check=True)
        print(preview.relative_to(ROOT).as_posix(), flush=True)


if __name__ == "__main__":
    main()
