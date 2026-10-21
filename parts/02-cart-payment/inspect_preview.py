"""Inspect actual encoded frames and build a compact review image."""
import json
from pathlib import Path

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

HERE = Path(__file__).resolve().parent
KEYS = [('01-list', 0), ('02-rush', 4.73), ('03-ten-courses', 5.65), ('04-cart', 7.75), ('05-cost', 14.05), ('06-deferred', 15.80), ('07-success', 20.10), ('08-lockscreen', 24.25), ('09-black', 27.2)]


def main():
    config = json.loads((HERE / 'preview-state.json').read_text('utf-8'))
    video = HERE / 'renders' / ('part02-' + config['version'] + '.mp4')
    key_dir = HERE / 'keyframes' / config['version']
    key_dir.mkdir(exist_ok=True, parents=True)
    capture = cv2.VideoCapture(str(video))
    if not capture.isOpened():
        raise RuntimeError('Encoded video could not be opened')
    width = int(capture.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(capture.get(cv2.CAP_PROP_FRAME_HEIGHT))
    fps = capture.get(cv2.CAP_PROP_FPS)
    count = int(capture.get(cv2.CAP_PROP_FRAME_COUNT))
    assert (width, height) == (1080, 2376), (width, height)
    assert abs(fps - 30) < .01, fps
    assert count == config['fps'] * config['duration'], count
    thumb_w, thumb_h = 216, 475
    sheet = Image.new('RGB', (thumb_w * 3 + 64, (thumb_h + 40) * 3 + 16), '#eae6ef')
    draw = ImageDraw.Draw(sheet)
    try:
        font = ImageFont.truetype('C:/Windows/Fonts/seguisb.ttf', 15)
    except OSError:
        font = ImageFont.load_default()
    checked = []
    for i, (name, t) in enumerate(KEYS):
        capture.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = capture.read()
        assert ok, (name, t)
        if name == '09-black':
            assert frame.max() <= 3, int(frame.max())
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        image.save(key_dir / (name + '-encoded.jpg'), quality=95)
        image = image.resize((thumb_w, thumb_h), Image.Resampling.LANCZOS)
        x, y = 16 + (i % 3) * (thumb_w + 16), 12 + (i // 3) * (thumb_h + 40)
        sheet.paste(image, (x, y))
        draw.text((x, y + thumb_h + 6), f'{name}  /  {t:.2f}s', font=font, fill='#4e3f5d')
        checked.append({'frame': name, 'time': t, 'mean': round(float(np.mean(frame)), 2)})
    transitions = [('05-cost', 14.05, '18 hours'), ('10-transfer', 14.75, 'Move below'), ('11-countdown', 15.20, '18 to 0'), ('06-deferred', 15.80, '0 now / 18 on receipt')]
    strip = Image.new('RGB', (1360, 520), '#eae6ef')
    strip_draw = ImageDraw.Draw(strip)
    for i, (name, t, label) in enumerate(transitions):
        capture.set(cv2.CAP_PROP_POS_MSEC, t * 1000)
        ok, frame = capture.read()
        assert ok, (name, t)
        image = Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        image.save(key_dir / (name + '-encoded.jpg'), quality=95)
        # Payment panel crop makes the number handoff readable in one strip.
        panel = image.crop((0, 802, 1080, 2302)).resize((320, 444), Image.Resampling.LANCZOS)
        x = 10 + i * 340
        strip.paste(panel, (x, 55))
        strip_draw.text((x, 18), f'{t:.2f}s / {label}', font=font, fill='#4e3f5d')
    strip.save(key_dir / 'payment-transition.jpg', quality=95)
    capture.release()
    overview = key_dir / 'overview.jpg'
    sheet.save(overview, quality=95)
    mobile = Image.new('RGB', (588, 1268), '#eae6ef')
    mobile_draw = ImageDraw.Draw(mobile)
    mobile_keys = [('01-list', 'Larger primary button'), ('05-cost', 'Payment / 18 hours'), ('06-deferred', '0 now / 18 on receipt'), ('07-success', 'Midterm delivery')]
    for i, (name, label) in enumerate(mobile_keys):
        frame = Image.open(key_dir / (name + '-encoded.jpg')).convert('RGB')
        frame = frame.resize((270, 594), Image.Resampling.LANCZOS)
        x, y = 12 + (i % 2) * 294, 12 + (i // 2) * 634
        mobile.paste(frame, (x, y))
        mobile_draw.text((x, y + 601), label, fill='#4e3f5d', font=font)
    mobile.save(key_dir / 'mobile-review.jpg', quality=95)
    result = {'video': video.name, 'width': width, 'height': height, 'fps': fps, 'frames': count, 'duration': count / fps, 'checked': checked, 'endingBlack': True}
    (HERE / 'renders' / 'qa.json').write_text(json.dumps(result, indent=2), 'utf-8')
    print(json.dumps(result), flush=True)


if __name__ == '__main__':
    main()
