"""Build the standalone animation, using only local references and vector covers."""
import argparse
import base64
import html
import io
import json
import math
from pathlib import Path
import shutil
import subprocess
import wave

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent


def data_url(data, mime):
    return 'data:' + mime + ';base64,' + base64.b64encode(data).decode('ascii')


def crop_reference(name, box, size):
    image = Image.open(ROOT / 'assets' / 'references' / name).convert('RGB')
    image = image.crop(box).resize(size, Image.Resampling.LANCZOS)
    out = io.BytesIO()
    image.save(out, 'JPEG', quality=93)
    return data_url(out.getvalue(), 'image/jpeg')


def vector_cover(title, subtitle, kind):
    colors = {
        'electronics': ('#c8bddb', '#efebf5'),
        'programming': ('#291743', '#7a4baf'),
        'english': ('#b0b4d9', '#e3dcec'),
        'mechanics': ('#c4b5d7', '#eddfec'),
        'experiment': ('#b4a1d3', '#e7dcf7'),
        'probability': ('#c4b3e4', '#eee5fa'),
        'algebra': ('#bcb2db', '#ece4f6'),
        'philosophy': ('#9c78b9', '#dfc9e9'),
    }
    a, b = colors[kind]
    if kind == 'electronics':
        art = '<g fill="none" stroke="#73538f" stroke-width="5" stroke-linecap="round" stroke-linejoin="round"><path d="M80 85h80m80 0h180v145H80V85m80 0v-25h80v50h-80V85m110 0v62m0 32v51m-30-83h60m-60 32h60"/><circle cx="80" cy="160" r="29" fill="#efebf5"/><path d="M62 160q9-22 18 0t18 0M374 115v85m-14-68h28m-28 30h28m-28 30h28"/></g>'
    elif kind == 'programming':
        art = '<rect x="45" y="38" width="410" height="218" rx="13" fill="#20152f" stroke="#b093cf"/><circle cx="67" cy="56" r="4" fill="#b99cd7"/><circle cx="82" cy="56" r="4" fill="#7a568f"/><circle cx="97" cy="56" r="4" fill="#7a568f"/><text x="80" y="170" font-size="87" fill="#e8d6fa" font-family="Consolas,monospace">&lt;/&gt;</text><path d="M295 102h100M295 128h74M295 154h94M295 180h61" stroke="#b796d3" stroke-width="8" stroke-linecap="round"/><text x="77" y="218" fill="#ac86c9" font-size="19" font-family="Consolas,monospace">hello, world.</text>'
    elif kind == 'english':
        art = '<path d="M64 74Q153 36 250 83Q347 36 436 74V240Q344 204 250 249Q154 204 64 240Z" fill="#fffbff" stroke="#8e79ab" stroke-width="3"/><path d="M250 83V249" stroke="#b8a3ca" stroke-width="3"/><text x="102" y="152" font-size="51" fill="#76618f" font-family="Georgia,serif">Aa</text><path d="M290 109h100M290 135h100M290 161h78M104 182h103M104 202h83M290 187h100M290 208h70" stroke="#cbbdd8" stroke-width="6"/>'
    elif kind == 'mechanics':
        art = '<g stroke="#73538f" fill="none" stroke-width="5"><circle cx="169" cy="151" r="64"/><circle cx="169" cy="151" r="29"/><circle cx="325" cy="151" r="43"/><circle cx="325" cy="151" r="15"/><path d="M233 151h49M105 151H64M325 108V58M325 194v40M169 87V45M169 215v40"/><path d="m162 48 7-15 7 15M325 59l-8 13m8-13 8 13"/></g><path d="M57 263H445" stroke="#8a6b9e" stroke-width="3"/><text x="373" y="90" fill="#75528f" font-size="28" font-family="Georgia,serif">F</text>'
    elif kind == 'experiment':
        art = '<g stroke="#745293" stroke-width="5" fill="none"><path d="M148 53h79M164 53v77l-54 93q-8 19 14 19h129q22 0 14-19l-55-93V53"/><path d="M137 184h102"/><rect x="307" y="85" width="63" height="157" rx="12"/><path d="M310 102h58M309 166h59"/></g><path d="m138 189-22 40q-3 6 8 6h129q11 0 8-6l-23-40Z" fill="#a274c5" opacity=".65"/><circle cx="180" cy="202" r="6" fill="#dfc7f3"/><circle cx="208" cy="220" r="8" fill="#dfc7f3"/>'
    elif kind == 'probability':
        art = '<path d="M48 248H455M80 266V43" stroke="#765393" stroke-width="3"/><path d="M80 240C152 240 166 77 250 76C334 77 348 240 430 240" stroke="#8652b0" stroke-width="5" fill="none"/><path d="M145 240C166 157 193 79 250 76C307 79 333 157 355 240Z" fill="#b590d4" opacity=".25"/><text x="285" y="71" fill="#765393" font-size="25" font-family="Georgia,serif">P(X)</text>'
    elif kind == 'algebra':
        art = '<g fill="#74538f" font-size="39" font-family="Georgia,serif"><text x="94" y="114">1　0　2</text><text x="94" y="170">0　1　3</text><text x="94" y="226">2　3　1</text></g><path d="M80 67H59V250H80M281 67h21V250h-21" fill="none" stroke="#74538f" stroke-width="5"/><path d="m343 199 66-78M343 199v-91M343 199h96" stroke="#a17ebd" stroke-width="4"/><circle cx="409" cy="121" r="6" fill="#765393"/>'
    else:
        art = '<path d="m116 81 143-38 123 44v174l-123-44-143 38Z" fill="#ede1f4" stroke="#88649f" stroke-width="3"/><path d="M259 43v174M137 104l99-26M137 132l99-26M137 160l99-26M282 89l77 27M282 119l77 27M282 149l77 27" stroke="#a68bb8" stroke-width="5"/>'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="500" height="300" viewBox="0 0 500 300"><defs><linearGradient id="g" x2="1" y2="1"><stop stop-color="{a}"/><stop offset="1" stop-color="{b}"/></linearGradient></defs><rect width="500" height="300" fill="url(#g)"/><circle cx="440" cy="18" r="150" fill="#fff" opacity=".12"/>{art}</svg>'''
    return data_url(svg.encode('utf-8'), 'image/svg+xml')


def create_audio(state, ffmpeg):
    rate = 44100
    length = state['duration']
    audio = np.zeros((int(rate * length), 2), dtype=np.float64)

    def tone(at, frequency, duration=.09, amp=.13, pan=0, glide=0):
        count = int(rate * duration)
        x = np.arange(count) / rate
        envelope = np.minimum(x / .004, 1) * np.exp(-x / (duration / 3))
        signal = np.sin(2 * np.pi * (frequency * x + .5 * glide * x * x)) * envelope
        signal += .17 * np.sin(2 * np.pi * 2 * frequency * x) * envelope
        begin = int(at * rate)
        end = min(len(audio), begin + count)
        if end <= begin:
            return
        audio[begin:end, 0] += signal[:end-begin] * amp * (1 - .3 * pan)
        audio[begin:end, 1] += signal[:end-begin] * amp * (1 + .3 * pan)

    def swoosh(at, duration=.34, amp=.06):
        rng = np.random.default_rng(int(at * 1000))
        count = int(rate * duration)
        n = rng.normal(0, 1, count)
        n = np.convolve(n, np.ones(12) / 12, mode='same')
        env = np.sin(np.linspace(0, np.pi, count)) ** 2
        begin = int(at * rate)
        audio[begin:begin+count, :] += (n * env * amp)[:, None]

    def crisp_click(at, amp=.50, pan=0, variant=0):
        # A dry transient with short inharmonic resonances, rather than a beep.
        duration = .034
        count = int(rate * duration)
        x = np.arange(count) / rate
        rng = np.random.default_rng(410 + variant)
        noise = rng.normal(0, .65, count)
        high = noise - np.convolve(noise, np.ones(7) / 7, mode='same')
        signal = .48 * np.sin(2 * np.pi * (1880 + variant * 17) * x) * np.exp(-x / .0048)
        signal += .26 * np.sin(2 * np.pi * 3670 * x) * np.exp(-x / .0027)
        signal += .13 * np.sin(2 * np.pi * 6250 * x) * np.exp(-x / .0016)
        signal += .19 * high * np.exp(-x / .0019)
        signal *= np.minimum(x / .00024, 1)
        signal *= np.minimum((duration - x) / .003, 1)
        begin = int(at * rate)
        audio[begin:begin+count, 0] += signal * amp * (1 - .25 * pan)
        audio[begin:begin+count, 1] += signal * amp * (1 + .25 * pan)

    def glass_ping(at, frequency, amp=.18, duration=.24, pan=0):
        count = int(rate * duration)
        x = np.arange(count) / rate
        attack = np.minimum(x / .0008, 1)
        signal = .73 * np.sin(2 * np.pi * frequency * x) * np.exp(-x / .051)
        signal += .19 * np.sin(2 * np.pi * frequency * 2.756 * x) * np.exp(-x / .024)
        signal += .08 * np.sin(2 * np.pi * frequency * 3.86 * x) * np.exp(-x / .012)
        signal *= attack * np.minimum((duration - x) / .008, 1)
        begin = int(at * rate)
        audio[begin:begin+count, 0] += signal * amp * (1 - .2 * pan)
        audio[begin:begin+count, 1] += signal * amp * (1 + .2 * pan)

    elective_index = 0
    crisp_click(.662, .51, variant=20)
    for i, action in enumerate(state['additions']):
        t = action['time']
        pan = (-1 if i % 2 == 0 else 1) * .35
        if action.get('batch'):
            swoosh(t + .07, .17, .014)
            glass_ping(t + action['flight'], 1510 + 105 * i, .085, .15, pan)
        else:
            j = elective_index
            crisp_click(t + .012, .49 + .018 * j, pan, j)
            swoosh(t + .08, min(.30, action['flight'] * .47), .028 + .006 * j)
            glass_ping(t + action['flight'], 1540 + 145 * j, .16 + .012 * j, .24, pan)
            elective_index += 1
    # Small sales chips arrive faster, with lighter, higher sounds than taps.
    for i, t in enumerate([2.20, 2.95, 3.62, 4.04, 4.29, 4.56, 5.06]):
        glass_ping(t + .025, 2480 + i * 85, .032 + i * .002, .085)
    # A soft UI swell builds behind the last purchases, ending at the cart cut.
    rush_start, rush_duration = 3.70, 2.36
    n = int(rate * rush_duration)
    x = np.arange(n) / rate
    rng = np.random.default_rng(1111)
    noise = rng.normal(0, 1, n)
    filtered = noise - np.convolve(noise, np.ones(17) / 17, mode='same')
    envelope = np.minimum(x / .18, 1) * (x / rush_duration) ** 1.8
    envelope *= np.minimum((rush_duration - x) / .045, 1)
    sweep = np.sin(2 * np.pi * (720 * x + 320 * x * x)) * .28
    begin = int(rush_start * rate)
    audio[begin:begin+n, :] += ((filtered * .014 + sweep * .009) * envelope)[:, None]
    for i, t in enumerate([5.90, 11.60, 16.79, 22.24]):
        crisp_click(t, .51, variant=10+i)
    swoosh(6.09, .18, .025)
    glass_ping(6.41, 1046.5, .13, .28)
    glass_ping(6.56, 783.99, .11, .27)
    swoosh(11.86, .42, .10)
    crisp_click(14.52, .51, variant=18)
    swoosh(14.55, .39, .045)
    glass_ping(14.94, 2170, .10, .15)
    for i, t in enumerate([15.02, 15.12, 15.22, 15.32, 15.42]):
        crisp_click(t, .10, variant=30+i)
    glass_ping(15.53, 2637, .085, .18)
    for i, note in enumerate([830.61, 1108.73, 1318.51]):
        tone(18.26 + i * .13, note, .60, .12)
    tone(25.74, 260, .105, .11, glide=-700)
    audio = np.tanh(audio * 1.3)
    pcm = (audio * 32767).astype('<i2')
    renders = HERE / 'renders'
    renders.mkdir(exist_ok=True)
    wav_path = renders / 'operations.wav'
    with wave.open(str(wav_path), 'wb') as wav:
        wav.setnchannels(2)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(pcm.tobytes())
    aac_path = renders / 'operations.m4a'
    subprocess.run([ffmpeg, '-hide_banner', '-loglevel', 'error', '-y', '-i', str(wav_path), '-c:a', 'aac', '-b:a', '128k', str(aac_path)], check=True)
    return data_url(aac_path.read_bytes(), 'audio/mp4')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--ffmpeg', default=shutil.which('ffmpeg'))
    args = parser.parse_args()
    if not args.ffmpeg:
        raise SystemExit('Pass --ffmpeg with an installed FFmpeg executable.')
    state = json.loads((HERE / 'preview-state.json').read_text('utf-8'))
    art = {
        'banner': crop_reference('home-v1.png', (21, 351, 825, 591), (1024, 306)),
        'calculus': crop_reference('home-v1.png', (25, 872, 409, 1084), (600, 340)),
        'physics': crop_reference('home-v1.png', (439, 872, 823, 1084), (600, 340)),
        'flowers': crop_reference('cart-v2.png', (117, 720, 389, 903), (600, 403)),
    }
    for course in state['courses']:
        if course['art'] not in art:
            art[course['art']] = vector_cover(course['title'], course['tag'], course['art'])
    audio = create_audio(state, args.ffmpeg)
    template = (HERE / 'animation.template.html').read_text('utf-8')
    output = template.replace('@@CONFIG@@', json.dumps(state, ensure_ascii=False)).replace('@@ART@@', json.dumps(art, ensure_ascii=False)).replace('@@AUDIO@@', audio)
    path = HERE / 'part02-preview.html'
    path.write_text(output, encoding='utf-8')
    print(json.dumps({'html': str(path), 'bytes': path.stat().st_size, 'credits': sum(c['credits'] for c in state['courses']), 'sleep': sum(c['sleep'] for c in state['courses'])}), flush=True)


if __name__ == '__main__':
    main()
