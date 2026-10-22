# LINE WebView 音訊播放實作基準

> 用途：記錄本次「日語動詞跟讀練習」在 LINE
> 內建瀏覽器（WebView）成功播放日語音訊的實作方式，供後續課程或網頁快速沿用。\
> 驗證日期：2026-10-22\
> 專案：`shadowing_courses / lessons/jp_verbs_practice`\
> 正式升格 Commit：`3598ce9`\
> 結果：**v5.6 CLOSED PASS**

## 1. 核心結論

LINE 內建瀏覽器的正式語音方案，不應依賴瀏覽器 `speechSynthesis` /
`SpeechSynthesisUtterance` 即時 TTS。

本次實機驗證成功的架構：

``` text
日文文字 / 課程資料
        ↓
edge-tts 預先產生 MP3
        ↓
MP3 靜態檔案
        ↓
HTML5 Audio
        ↓
GitHub Pages
        ↓
LINE WebView
        ↓
PASS
```

**核心原則：TTS 在建置階段完成；LINE 執行階段只負責播放標準 MP3。**

## 2. 為什麼不用 speechSynthesis

原版使用 Web Speech API。在一般瀏覽器可能正常，但本次 LINE
實機測試發現目前 LINE WebView 沒有可用的 `speechSynthesis` API。

曾嘗試： - LINE User-Agent 判斷 - `getVoices()` - silent warm-up -
delay - watchdog - fallback 提示

仍無法解決 API 本身不存在的問題。

因此不要把以下方式當成 LINE 正式方案：

``` js
const u = new SpeechSynthesisUtterance(text);
speechSynthesis.speak(u);
```

顯示「請改用 Chrome」只能算降級提示，不是 LINE 內可用的修復。

## 3. 正式採用：edge-tts 預產 MP3

本次規格：

``` text
edge-tts 7.3.1
Voice: ja-JP-NanamiNeural
Rate: -10%
```

28 個動詞，每個動詞 4 個音訊：

``` text
audio/v01_masu.mp3
audio/v01_dict.mp3
audio/v01_koto.mp3
audio/v01_sentence.mp3
...
audio/v28_masu.mp3
audio/v28_dict.mp3
audio/v28_koto.mp3
audio/v28_sentence.mp3
```

總數：

``` text
28 × 4 = 112 MP3
```

命名意義： - `masu`：ます形 - `dict`：辭書形 - `koto`：辭書形＋こと -
`sentence`：完整例句

Python 核心概念：

``` python
import edge_tts

communicate = edge_tts.Communicate(
    text,
    voice="ja-JP-NanamiNeural",
    rate="-10%"
)
await communicate.save(output_file)
```

## 4. 產檔後必做檢查

不能只確認「檔名存在」。本次曾因先前失敗留下 0-byte
MP3，而產生器採「存在即 skip」，導致壞檔被誤認為完成。

檢查總數：

``` powershell
(Get-ChildItem .\audio\*.mp3).Count
```

本案例預期：

``` text
112
```

檢查零位元組：

``` powershell
Get-ChildItem .\audio\*.mp3 |
Where-Object Length -eq 0 |
Select-Object Name,Length
```

預期：**無輸出**。

本次舊版 `edge-tts` 曾遇 WebSocket 403；升級到 `edge-tts 7.3.1` 後正常。

## 5. HTML5 Audio 播放

頁面使用標準 HTML5 Audio：

``` html
<audio id="audioPlayer" preload="none"></audio>
```

核心概念：

``` js
const audio = document.getElementById("audioPlayer");

async function playFile(src, rate = 1.0) {
  audio.pause();
  audio.currentTime = 0;
  audio.src = src;
  audio.playbackRate = rate;
  await audio.play();
}
```

也可使用：

``` js
const audio = new Audio(src);
audio.play();
```

重點是：**LINE 只播放既有 MP3，不在 LINE 裡即時合成語音。**

## 6. 音訊 mapping 要綁定穩定 ID

不要依畫面排序或 group filter 後的 index 臨時計算 MP3。

建議：

``` js
{
  id: "v01",
  masu: "行きます",
  dict: "行く",
  audio: {
    masu: "audio/v01_masu.mp3",
    dict: "audio/v01_dict.mp3",
    koto: "audio/v01_koto.mp3",
    sentence: "audio/v01_sentence.mp3"
  }
}
```

這樣切換 Group I / II /
III、隨機、上一個／下一個後，仍能確保畫面文字與音訊一致。

## 7. 播放速度

單字／形態 MP3 已用 edge-tts `-10%` 生成，網頁播放維持：

``` js
audio.playbackRate = 1.0;
```

完整句提供： - `1.0x 正常` - `0.7x 慢速`

慢速直接使用：

``` js
audio.playbackRate = 0.7;
```

不需要再產一份慢速 MP3。本次正式需求不使用 `0.85x`。

## 8. 跟讀 3 次

一組為：

``` text
ます形 → 辭書形 → 辭書形＋こと
```

整組重複 3 次：

``` text
3 個音訊 × 3 次 = 9 段播放
```

概念：

``` js
const sequence = [
  item.audio.masu,
  item.audio.dict,
  item.audio.koto
];

for (let round = 0; round < 3; round++) {
  for (const src of sequence) {
    await playAudioAndWait(src);
    await sleep(450);
  }
}
```

本次沿用約 `450 ms` 段落間隔。

## 9. UI 一定要能解鎖

播放期間可鎖定其他控制並標示 active，但所有結束路徑都必須 unlock：

-   正常 `ended`
-   `error`
-   `audio.play()` Promise rejection
-   例外
-   watchdog timeout

不能只依賴 `audio.onended`。

本次測試版另有約 30 秒 watchdog，避免 UI 永久卡住。

**原則：成功、失敗、例外、超時，最後都必須 unlock UI。**

## 10. LINE 驗收流程

### A. 本機瀏覽器

``` powershell
py -m http.server 8000
```

用 Chrome / Edge 開啟 `http://localhost:8000/`，先確認 HTML5 Audio
本身正常。

### B. GitHub Pages 獨立 test path

先部署測試路徑，例如：

``` text
lessons/jp_verbs_practice_v56_test/
```

不要一開始就覆蓋正式版。

### C. LINE 內建瀏覽器實機

至少驗證： - `🔊 ます形` - `🔊 辭書形` - `🔊 ＋こと` - `🔁 跟讀 3 次`

確認： - 有聲音 - 聲音與文字一致 - 跟讀為 9 段 - 播放結束 UI 恢復

### D. 正式升格後再驗一次

Test path 在 LINE PASS 後，才升格 formal path；正式網址仍需再次 LINE
實機驗收。

本次正式結果：**PASS**。

## 11. 建議固定升格 SOP

``` text
1. 產生 MP3
2. 檢查 MP3 數量
3. 檢查 zero-byte
4. 本機 HTML5 Audio 測試
5. 建 GitHub Pages test path
6. push test path
7. LINE WebView 實機驗收
8. PASS 後複製到 formal path
9. test / formal SHA-256 比對
10. Git staged boundary audit
11. commit
12. push
13. 正式網址 LINE 實機驗收
14. CLOSED PASS
```

不要採：

``` text
產生完成 → 直接覆蓋正式版 → 才測 LINE
```

## 12. Test → Formal 完整性比對

HTML：

``` powershell
(Get-FileHash .\TEST\index.html -Algorithm SHA256).Hash
(Get-FileHash .\FORMAL\index.html -Algorithm SHA256).Hash
```

必須相同。

MP3：

``` powershell
$bad = foreach ($f in Get-ChildItem $testAudio\*.mp3) {
    $formal = Join-Path $formalAudio $f.Name

    if (!(Test-Path $formal) -or
        (Get-FileHash $f.FullName -Algorithm SHA256).Hash -ne
        (Get-FileHash $formal -Algorithm SHA256).Hash) {
        $f.Name
    }
}

"MismatchCount=$(@($bad).Count)"
```

預期：

``` text
MismatchCount=0
```

## 13. Git boundary audit

正式升格時確認只 stage 正式路徑：

``` powershell
git diff --cached --name-only |
Where-Object { $_ -notlike "lessons/jp_verbs_practice/*" }
```

預期：**無輸出**。

本次正式升格：

``` text
113 files
= 1 index.html
+ 112 MP3
```

正式 Commit：

``` text
3598ce9
fix(japanese): promote LINE-compatible HTML5 audio for verb practice
```

## 14. 未來快速沿用

未來另一個日語網頁若要支援 LINE：

1.  資料中為每個項目指定固定 MP3 路徑。
2.  用 `edge-tts` + `ja-JP-NanamiNeural` 預產 MP3。
3.  產檔後檢查數量與 zero-byte。
4.  網頁使用 HTML5 Audio，不以 `speechSynthesis` 作 LINE 正式播放引擎。
5.  慢速需求優先使用 `audio.playbackRate`。
6.  先部署獨立 test path。
7.  必須實際從 LINE 內建瀏覽器開啟測試。
8.  LINE PASS 才升格 formal。
9.  正式網址再做一次 LINE 實機驗收。

## 15. 快速判斷表

  項目                         LINE 正式方案
  ---------------------------- ------------------
  `speechSynthesis`            ❌ 不依賴
  `SpeechSynthesisUtterance`   ❌ 不依賴
  edge-tts                     ✅ 建置階段
  MP3                          ✅
  HTML5 Audio                  ✅
  `audio.playbackRate`         ✅
  GitHub Pages                 ✅ 本次已驗證
  LINE WebView                 ✅ 本次實機 PASS
  Test path 先驗證             ✅
  Formal 再驗收                ✅
  zero-byte 檢查               ✅ 必做
  SHA-256 test/formal 比對     ✅ 建議必做

## 16. 一句話記憶

> **LINE 裡不要即時「合成聲音」，而是先把聲音做成 MP3；LINE 只負責用
> HTML5 Audio 播放。**

## 17. 本次驗證基準

``` text
Project:
shadowing_courses

Formal:
lessons/jp_verbs_practice/

Test:
lessons/jp_verbs_practice_v56_test/

Audio:
28 verbs × 4 = 112 MP3

TTS:
edge-tts 7.3.1
ja-JP-NanamiNeural
rate -10%

Browser audio:
HTML5 Audio

Sentence speed:
1.0x / 0.7x

Repeat:
3 forms × 3 rounds = 9 plays

Formal commit:
3598ce9

Final:
GitHub Pages + LINE WebView = PASS
v5.6 = CLOSED PASS
```

------------------------------------------------------------------------

**文件定位：**\
這份文件是「LINE WebView 網頁語音播放」的實作與驗證基準。未來遇到 LINE
裡網頁 TTS 無聲、`speechSynthesis`
不可用，或要新增日語跟讀課程時，優先沿用：

``` text
edge-tts → MP3 → HTML5 Audio → GitHub Pages → LINE 實機驗收
```
