import SwiftUI
import Observation

@Observable
class AppState {
    var currentScreen: AppScreen = .home
    var todaysAdventure: Adventure?
    var todaysAnimal: AnimalCharacter?
    var completedDates: Set<String> = []
    var isVoiceEnabled: Bool = true

    enum AppScreen {
        case home
        case intro
        case adventure
        case celebration
    }

    init() {
        loadProgress()
    }

    var isTodayCompleted: Bool {
        completedDates.contains(todayKey)
    }

    private var todayKey: String {
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        return formatter.string(from: Date())
    }

    func markTodayCompleted() {
        completedDates.insert(todayKey)
        UserDefaults.standard.set(Array(completedDates), forKey: "completedDates")
    }

    private func loadProgress() {
        let saved = UserDefaults.standard.array(forKey: "completedDates") as? [String] ?? []
        completedDates = Set(saved)
    }
}
