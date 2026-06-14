import Foundation

enum VillageLocation: String, Codable, CaseIterable, Hashable {
    case plaza = "広場"
    case bakery = "パン屋"
    case smithy = "鍛冶屋"
    case riverside = "川沿い"
    case elderHouse = "長老の家"
}

enum EmotionalState: String, Codable {
    case happy = "明るい"
    case worried = "心配そう"
    case sad = "悲しそう"
    case mysterious = "何かを隠している"
    case neutral = "普通"
    case excited = "興奮している"
}

struct Message: Codable, Identifiable {
    let id: UUID
    let role: MessageRole
    let content: String
    let timestamp: Date

    enum MessageRole: String, Codable {
        case player, npc
    }
}

struct NPC: Identifiable, Codable {
    let id: UUID
    var name: String
    var occupation: String
    var personality: String
    var backstory: String
    var emotionalState: EmotionalState
    var relationshipWithPlayer: Int
    var conversationHistory: [Message]
    var wantsToTalk: Bool
    var location: VillageLocation
    var avatarEmoji: String
}

extension NPC {
    static let defaultNPCs: [NPC] = [
        NPC(
            id: UUID(),
            name: "リナ",
            occupation: "パン屋",
            personality: "温かく世話好きだが、心配性。自分の感情を押し込める癖がある。",
            backstory: "夫を10年前に亡くし、一人で息子カイを育ててきた。",
            emotionalState: .worried,
            relationshipWithPlayer: 40,
            conversationHistory: [],
            wantsToTalk: true,
            location: .bakery,
            avatarEmoji: "👩‍🍳"
        ),
        NPC(
            id: UUID(),
            name: "ゴルド",
            occupation: "鍛冶屋",
            personality: "口数が少なく不器用だが、誰より村のことを思っている。",
            backstory: "若い頃は旅をしていた。ある出来事をきっかけにこの村に定住した。",
            emotionalState: .mysterious,
            relationshipWithPlayer: 20,
            conversationHistory: [],
            wantsToTalk: false,
            location: .smithy,
            avatarEmoji: "⚒️"
        ),
        NPC(
            id: UUID(),
            name: "カイ",
            occupation: "リナの息子",
            personality: "若くて感情的。夢を持っているが、母への罪悪感に縛られている。",
            backstory: "旅に出たい気持ちを押し殺している。最近ふさぎ込んでいる。",
            emotionalState: .sad,
            relationshipWithPlayer: 30,
            conversationHistory: [],
            wantsToTalk: false,
            location: .riverside,
            avatarEmoji: "🧒"
        ),
        NPC(
            id: UUID(),
            name: "フィア",
            occupation: "長老",
            personality: "村の歴史を知る賢者。だが最近、何かを抱えている様子。",
            backstory: "この村に50年以上住み続けている。村の「秘密」を知っている。",
            emotionalState: .mysterious,
            relationshipWithPlayer: 10,
            conversationHistory: [],
            wantsToTalk: false,
            location: .elderHouse,
            avatarEmoji: "🧓"
        ),
        NPC(
            id: UUID(),
            name: "ミコ",
            occupation: "旅人",
            personality: "この村に最近来た謎の旅人。何かを探している。",
            backstory: "出自不明。村の古い歴史を調べているようだ。",
            emotionalState: .neutral,
            relationshipWithPlayer: 0,
            conversationHistory: [],
            wantsToTalk: true,
            location: .plaza,
            avatarEmoji: "🧳"
        )
    ]
}
