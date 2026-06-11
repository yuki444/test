import Foundation

struct AnimalCharacter: Codable, Identifiable, Equatable {
    let id: String
    let name: String
    let emoji: String
    let color: String
    let personality: String
    let greeting: String
    let cheerPhrase: String
    let hintPhrase: String
    let successPhrase: String
    let wrongPhrase: String
    let completionPhrase: String

    static func == (lhs: AnimalCharacter, rhs: AnimalCharacter) -> Bool {
        lhs.id == rhs.id
    }
}

struct AnimalCollection: Codable {
    let animals: [AnimalCharacter]
}
