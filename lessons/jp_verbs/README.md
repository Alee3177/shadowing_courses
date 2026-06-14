# 動詞 Shadowing 跟讀版

檔案：
- `index.html`：跟讀版主頁
- `lesson.json`：整合資料，含 どうし#1-#5、出門前穿戴、回家後脫下
- `tools/generate_audio.py`：生成 MP3
- `audio/`：MP3 目錄

生成 MP3：
```bash
pip install edge-tts
python tools/generate_audio.py --voice ja-JP-NanamiNeural
```

本版 HTML 會優先播放 `audio/v001.mp3` 這類 MP3；若尚未生成 MP3，會自動改用瀏覽器內建日文語音。
