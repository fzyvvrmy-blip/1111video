import argparse,importlib.util,json,os
from pathlib import Path
p=argparse.ArgumentParser();p.add_argument('--ffmpeg',default=os.environ.get('FFMPEG_PATH','ffmpeg'));args=p.parse_args()
root=Path(__file__).resolve().parent/'source/part02'
spec=importlib.util.spec_from_file_location('part02_audio',root/'build_preview.py');module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
state=json.loads((root/'preview-state.json').read_text(encoding='utf-8'))
module.create_audio(state,args.ffmpeg)
print('Part02 operations audio rebuilt.')
