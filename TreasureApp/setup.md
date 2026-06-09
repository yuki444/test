# たからものアプリ セットアップガイド

## Xcodeでプロジェクトを作る手順

### 1. 新規プロジェクト作成
1. Xcode を起動
2. **File → New → Project**
3. **iOS → App** を選択
4. 以下を入力:
   - Product Name: `TreasureApp`
   - Team: 自分のApple ID
   - Organization Identifier: `com.yourname`
   - Interface: `SwiftUI`
   - Language: `Swift`
5. 保存先を選択して **Create**

### 2. ソースファイルを追加
このリポジトリの `TreasureApp/TreasureApp/` フォルダ内のファイルを、
作成したXcodeプロジェクトの対応する場所にコピーする。

**ファイル構成:**
```
TreasureApp/
├── TreasureApp.swift          ← App エントリポイント（既存を置き換え）
├── Info.plist                 ← カメラ権限の設定
├── Models/
│   ├── TreasureItem.swift
│   ├── TreasureCategory.swift
│   └── LevelSystem.swift
├── Views/
│   ├── HomeView.swift
│   ├── CameraView.swift
│   ├── TagSelectionView.swift
│   ├── GalleryView.swift
│   ├── CategoryGalleryView.swift
│   ├── TreasureDetailView.swift
│   ├── LevelDashboardView.swift
│   ├── CelebrationView.swift
│   └── AddCategoryView.swift
├── ViewModels/
│   ├── TreasureStore.swift
│   └── CameraManager.swift
└── Extensions/
    └── Color+Hex.swift
```

### 3. Xcodeでファイルを追加
1. プロジェクトナビゲータで右クリック → **Add Files to "TreasureApp"**
2. 上記フォルダ群を選択
3. **Create groups** にチェックを入れて追加

### 4. Info.plist を設定
Xcodeのプロジェクト設定 → **Info タブ** で以下のキーを追加:
- `Privacy - Camera Usage Description`
- `Privacy - Photo Library Usage Description`

または `Info.plist` ファイルを丸ごと置き換える。

### 5. 実機でビルド
1. iPhoneをMacに接続
2. Xcodeのターゲットを自分のiPhoneに設定
3. **Run (⌘R)** でビルド＆インストール

## アプリの機能

| 画面 | 説明 |
|------|------|
| ホーム | カテゴリボタン一覧・レベル表示 |
| カメラ | 撮影・確認 |
| タグ選択 | 何を見つけたか選ぶ |
| お祝い演出 | 「すごい！がんばったね！」＋コンフェッティ |
| ギャラリー | カテゴリ別に一覧表示 |
| レベル | 各カテゴリの成長を確認 |

## レベルシステム

| レベル | 名前 | 必要枚数 |
|--------|------|---------|
| Lv0 | 🥚 たまご | 0枚から |
| Lv1 | 🐣 ひよこ | 5枚から |
| Lv2 | 🌱 こども | 15枚から |
| Lv3 | 🌸 なかよし | 30枚から |
| Lv4 | 🔍 たんていか | 50枚から |
| Lv5 | 🏆 たからはかせ | 75枚から |
