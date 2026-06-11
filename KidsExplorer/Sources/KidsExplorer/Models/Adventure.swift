import Foundation

struct Adventure: Codable, Identifiable, Equatable {
    let id: String
    let title: String
    let subtitle: String
    let theme: String
    let colorHex: String
    let locationName: String
    let openingNarration: String
    let scenes: [AdventureScene]

    static func == (lhs: Adventure, rhs: Adventure) -> Bool {
        lhs.id == rhs.id
    }
}

struct AdventureCollection: Codable {
    let adventures: [Adventure]
}
