import Foundation

struct Quiz: Codable {
    let type: QuizType
    let question: String
    let visualItems: [String]
    let answer: String
    let options: [String]
    let successMessage: String
    let hintMessage: String

    enum QuizType: String, Codable {
        case addition
        case katakana
        case counting
    }

    func isCorrect(_ option: String) -> Bool {
        option == answer
    }
}
