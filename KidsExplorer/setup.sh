#!/bin/bash
# おうちたんけん - セットアップスクリプト

set -e

echo "🏠 おうちたんけん - セットアップ開始"
echo "=================================="

# 必要なツールの確認
check_tool() {
    if ! command -v "$1" &> /dev/null; then
        echo "❌ $1 が見つかりません"
        return 1
    else
        echo "✅ $1 を確認"
        return 0
    fi
}

check_tool xcode-select || {
    echo "Xcode Command Line Tools をインストールしてください:"
    echo "  xcode-select --install"
    exit 1
}

# xcodegen のインストール確認
if ! command -v xcodegen &> /dev/null; then
    echo "📦 xcodegen をインストール中..."
    if command -v brew &> /dev/null; then
        brew install xcodegen
    else
        echo "❌ Homebrew が必要です: https://brew.sh"
        echo "   または: mint install yonaskolb/XcodeGen"
        exit 1
    fi
fi

echo ""
echo "🔨 Xcode プロジェクトを生成中..."
xcodegen generate

echo ""
echo "✅ 完了！KidsExplorer.xcodeproj が生成されました"
echo ""
echo "次のステップ:"
echo "  1. open KidsExplorer.xcodeproj"
echo "  2. Signing & Capabilities で開発チームを設定"
echo "  3. iPhone 実機または シミュレーターで実行"
echo ""
echo "📋 必要な設定:"
echo "  - iOS 17.0+"
echo "  - Swift 5.9+"
echo "  - カメラ権限 (実機で使用時)"
