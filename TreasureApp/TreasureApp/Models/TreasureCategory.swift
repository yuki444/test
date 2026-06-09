import SwiftUI

struct TreasureCategory: Identifiable, Codable, Equatable, Hashable {
    let id: UUID
    var name: String
    var emoji: String
    var colorHex: String
    var subcategories: [String]
    var isCustom: Bool

    var color: Color { Color(hex: colorHex) }

    static let defaults: [TreasureCategory] = [
        TreasureCategory(
            id: UUID(uuidString: "00000001-0000-0000-0000-000000000001")!,
            name: "いきもの",
            emoji: "🐛",
            colorHex: "#4CAF50",
            subcategories: ["むし", "とり", "さかな", "どうぶつ"],
            isCustom: false
        ),
        TreasureCategory(
            id: UUID(uuidString: "00000002-0000-0000-0000-000000000002")!,
            name: "のりもの",
            emoji: "🚗",
            colorHex: "#2196F3",
            subcategories: ["くるま", "でんしゃ", "ひこうき", "ふね"],
            isCustom: false
        ),
        TreasureCategory(
            id: UUID(uuidString: "00000003-0000-0000-0000-000000000003")!,
            name: "しょくぶつ",
            emoji: "🌿",
            colorHex: "#8BC34A",
            subcategories: ["はな", "き", "くさ", "みのり"],
            isCustom: false
        ),
        TreasureCategory(
            id: UUID(uuidString: "00000004-0000-0000-0000-000000000004")!,
            name: "しぜん",
            emoji: "⛅",
            colorHex: "#03A9F4",
            subcategories: ["そら", "いし", "かわ", "うみ"],
            isCustom: false
        ),
        TreasureCategory(
            id: UUID(uuidString: "00000005-0000-0000-0000-000000000005")!,
            name: "ばしょ",
            emoji: "🏠",
            colorHex: "#FF9800",
            subcategories: ["いえ", "こうえん", "みせ", "がっこう"],
            isCustom: false
        ),
        TreasureCategory(
            id: UUID(uuidString: "00000006-0000-0000-0000-000000000006")!,
            name: "そのほか",
            emoji: "⭐",
            colorHex: "#9C27B0",
            subcategories: [],
            isCustom: true
        ),
    ]
}
