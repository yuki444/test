import Foundation

struct Season: Codable {
    var number: Int
    var dayNumber: Int
    var totalDays: Int = 30
    var mysteryTitle: String
    var mysteryHint: String
    var internalTruth: String
    var isResolved: Bool = false
    var startDate: Date

    var progress: Double {
        Double(dayNumber) / Double(totalDays)
    }

    var remainingDays: Int {
        max(0, totalDays - dayNumber)
    }
}

extension Season {
    static let firstSeason = Season(
        number: 1,
        dayNumber: 1,
        mysteryTitle: "長老の沈黙",
        mysteryHint: "霧の向こうに、何かが見えた気がした。",
        internalTruth: "長老フィアは30日後にこの村を離れる決断をしようとしている。理由は20年前に起きた出来事への罪悪感。村人は誰も気づいていない。",
        startDate: Date()
    )
}
