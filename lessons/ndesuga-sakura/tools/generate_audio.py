#!/usr/bin/env python3
# Regenerate MP3 files from data/ndesuga_stpmpov_shadowing.json.
# Offline fallback uses espeak reading the romaji `speak` field.
import json, os, subprocess
ROOT=os.path.dirname(os.path.dirname(__file__))
DATA=os.path.join(ROOT,'data','ndesuga_stpmpov_shadowing.json')
AUDIO=os.path.join(ROOT,'audio')
os.makedirs(AUDIO,exist_ok=True)
with open(DATA,encoding='utf-8') as f: data=json.load(f)
for it in data['items']:
    wav=os.path.join(AUDIO,it['id']+'.wav')
    mp3=os.path.join(AUDIO,it['id']+'.mp3')
    text=it.get('speak') or it.get('romaji') or it['jp']
    subprocess.run(['espeak','-v','en-us','-s','135','-p','45','-w',wav,text],check=True)
    subprocess.run(['ffmpeg','-y','-loglevel','error','-i',wav,'-codec:a','libmp3lame','-q:a','4',mp3],check=True)
    os.remove(wav)
    print('generated',mp3)
