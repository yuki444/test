import Foundation

struct AdventureScene: Codable, Identifiable {
    let id: String
    let order: Int
    let locationPrompt: String
    let locationHint: String
    let narration: String
    let overlayEmojis: [String]
    let characterLine: String
    let quiz: Quiz
}
