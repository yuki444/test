import Foundation

enum VillageAtmosphere: String, Codable {
    case warm = "温かい"
    case tense = "緊張している"
    case mysterious = "不思議な"
    case peaceful = "穏やかな"
    case sad = "悲しげな"
}

struct DayEvent: Codable, Identifiable {
    let id: UUID
    let description: String
    let day: Int
}

struct VillageState: Codable {
    var atmosphere: VillageAtmosphere = .peaceful
    var currentSeason: Season
    var npcs: [NPC]
    var recentEvents: [DayEvent] = []
    var lastLoginDate: Date?

    var npcsWantingToTalk: [NPC] {
        npcs.filter { $0.wantsToTalk }
    }

    mutating func advanceDay() {
        currentSeason.dayNumber += 1
        lastLoginDate = Date()
    }
}
