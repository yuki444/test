import Foundation

struct LevelInfo {
    let level: Int
    let title: String
    let emoji: String
    let progress: Double
    let nextCount: Int?
}

struct LevelSystem {
    // (requiredCount, title, emoji)
    static let thresholds: [(Int, String, String)] = [
        (0,  "たまご",       "🥚"),
        (5,  "ひよこ",       "🐣"),
        (15, "こども",       "🌱"),
        (30, "なかよし",     "🌸"),
        (50, "たんていか",   "🔍"),
        (75, "たからはかせ", "🏆"),
    ]

    static func levelIndex(for count: Int) -> Int {
        var idx = 0
        for (i, (threshold, _, _)) in thresholds.enumerated() {
            if count >= threshold { idx = i }
        }
        return idx
    }

    static func info(for count: Int) -> LevelInfo {
        let idx = levelIndex(for: count)
        let (currentThreshold, title, emoji) = thresholds[idx]

        let progress: Double
        let nextCount: Int?

        if idx < thresholds.count - 1 {
            let nextThreshold = thresholds[idx + 1].0
            nextCount = nextThreshold
            progress = Double(count - currentThreshold) / Double(nextThreshold - currentThreshold)
        } else {
            nextCount = nil
            progress = 1.0
        }

        return LevelInfo(level: idx, title: title, emoji: emoji, progress: progress, nextCount: nextCount)
    }
}
