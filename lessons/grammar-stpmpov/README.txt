# STPMPPOV 交通＋日期時間造句練習｜MP3版

## 上傳結構

```
stpmpov-travel/
├─ stpmpov_travel_datetime_trainer.html
├─ data/
│  ├─ date_parts.json
│  ├─ time_parts.json
│  ├─ sentence_parts_stpmpov.json
│  └─ audio_manifest.json
├─ audio/                 # 執行 generate_audio.py 後產生
└─ tools/
   └─ generate_audio.py
```

## 生成 MP3

```bash
pip install edge-tts
python tools/generate_audio.py
```

完成後，把整個資料夾上傳 GitHub Pages。
