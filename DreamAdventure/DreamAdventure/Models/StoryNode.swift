import SwiftUI

struct StoryNode: Identifiable {
    let id: String
    let scene: SceneType
    let background: BackgroundType
    let narration: [String]        // 複数行のナレーション
    let characterDialogue: String?  // 動物キャラのセリフ
    let interaction: InteractionType
    let nextNodeId: String?
    let choices: [StoryChoice]
}

struct StoryChoice: Identifiable {
    let id: String
    let text: String
    let emoji: String
    let nextNodeId: String
    let feedback: String           // 選択後のリアクション
}

enum SceneType {
    case opening        // 共感シーン
    case challenge      // 挑戦シーン
    case cooperation    // 協力シーン
    case achievement    // 夢実現シーン
    case ending         // エンディング
}

enum BackgroundType {
    // 宇宙系
    case nightSky, spaceship, moon, stars, cosmos
    // ケーキ系
    case kitchen, forest, bakery, celebration
    // 海系
    case beach, ocean, underwater, treasure, storm
    // 共通
    case home, meadow
}

enum InteractionType {
    case tapToContinue               // タップで次へ
    case tapCharacter                // キャラクタータップ
    case choice                      // 選択肢
    case shake                       // シェイク操作（ケーキを混ぜる等）
    case celebration                 // お祝いエフェクト
}

struct Story {
    let dreamType: DreamType
    let nodes: [String: StoryNode]
    let startNodeId: String
}
