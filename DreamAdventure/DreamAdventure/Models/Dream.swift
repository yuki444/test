import SwiftUI

enum DreamType: String, CaseIterable, Identifiable {
    case astronaut = "astronaut"
    case baker = "baker"
    case explorer = "explorer"

    var id: String { rawValue }

    var title: String {
        switch self {
        case .astronaut: return "うちゅうひこうし"
        case .baker:     return "ケーキしょくにん"
        case .explorer:  return "うみのたんけんか"
        }
    }

    var emoji: String {
        switch self {
        case .astronaut: return "🚀"
        case .baker:     return "🎂"
        case .explorer:  return "🌊"
        }
    }

    var color: Color {
        switch self {
        case .astronaut: return Color(red: 0.2, green: 0.1, blue: 0.5)
        case .baker:     return Color(red: 0.9, green: 0.4, blue: 0.5)
        case .explorer:  return Color(red: 0.0, green: 0.5, blue: 0.8)
        }
    }

    var gradientColors: [Color] {
        switch self {
        case .astronaut: return [Color(red: 0.05, green: 0.05, blue: 0.25), Color(red: 0.3, green: 0.1, blue: 0.6)]
        case .baker:     return [Color(red: 1.0, green: 0.85, blue: 0.7), Color(red: 0.95, green: 0.5, blue: 0.6)]
        case .explorer:  return [Color(red: 0.0, green: 0.6, blue: 0.9), Color(red: 0.0, green: 0.3, blue: 0.6)]
        }
    }

    var animal: AnimalCharacter {
        switch self {
        case .astronaut: return AnimalCharacter(name: "コスモくま", emoji: "🐻", description: "うちゅうが だいすきな くまさん")
        case .baker:     return AnimalCharacter(name: "シェフうさぎ", emoji: "🐰", description: "りょうりが とくいな うさぎさん")
        case .explorer:  return AnimalCharacter(name: "マリンイルカ", emoji: "🐬", description: "うみを しっている いるかさん")
        }
    }
}

struct AnimalCharacter {
    let name: String
    let emoji: String
    let description: String
}
