import Foundation

class DailyContentService {
    static let shared = DailyContentService()

    private var adventures: [Adventure] = []
    private var animals: [AnimalCharacter] = []

    private init() {
        loadData()
    }

    private func loadData() {
        adventures = loadAdventures()
        animals = loadAnimals()
    }

    func todaysAdventure() -> Adventure? {
        guard !adventures.isEmpty else { return nil }
        let dayIndex = Calendar.current.component(.weekday, from: Date()) - 1
        return adventures[dayIndex % adventures.count]
    }

    func todaysAnimal() -> AnimalCharacter? {
        guard !animals.isEmpty else { return nil }
        let dayOfYear = Calendar.current.ordinality(of: .day, in: .year, for: Date()) ?? 1
        return animals[(dayOfYear - 1) % animals.count]
    }

    private func loadAdventures() -> [Adventure] {
        guard let url = Bundle.main.url(forResource: "adventures", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let collection = try? JSONDecoder().decode(AdventureCollection.self, from: data) else {
            return []
        }
        return collection.adventures
    }

    private func loadAnimals() -> [AnimalCharacter] {
        guard let url = Bundle.main.url(forResource: "animals", withExtension: "json"),
              let data = try? Data(contentsOf: url),
              let collection = try? JSONDecoder().decode(AnimalCollection.self, from: data) else {
            return []
        }
        return collection.animals
    }
}
