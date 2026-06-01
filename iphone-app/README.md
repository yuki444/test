# ぽかぽかガーデン 🌸

5歳の子供が楽しめるiPhone向け花育てゲーム。

## 遊び方

1. じょうろ🪣をタップ
2. 5回水をあげると花が咲く！
3. 6色の花を全部咲かせて「にじのはな」をゲット！

## 技術スタック

- HTML5 / CSS3 / Vanilla JavaScript
- Web Audio API（音声フィードバック）
- Canvas 2D API（パーティクルエフェクト）
- localStorage（進捗保存）
- Capacitor（iOS/Androidアプリ化）

## iOSアプリ化手順（macOS + Xcode必須）

```bash
npm install @capacitor/core @capacitor/ios @capacitor/cli
npx cap add ios
npx cap sync
npx cap open ios
```

Xcodeで Archive → TestFlight / App Store に提出。

## デザイン方針（開発チーム・検討チーム合意事項）

| 観点 | 実装内容 |
|------|---------|
| タッチターゲット | 最小120×120px（じょうろボタン） |
| フィードバック | 音・アニメーション・パーティクルの3重 |
| 文字不要設計 | 絵文字とアイコンで完結 |
| 達成感 | 開花時の全画面セレブレーション |
| 安全性 | 外部リンクなし・課金なし・広告なし |
| セッション長 | 1植物2〜3分、自然に終わる設計 |
