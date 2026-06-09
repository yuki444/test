import Foundation

struct RhythmTap: Codable {
    let buttonId: Int
    let slot: Int  // 0-15 (16th note grid)
}

struct SavedRhythm: Identifiable, Codable {
    let id: UUID
    let themeId: Int
    let taps: [RhythmTap]
    let createdAt: Date
    let title: String

    init(themeId: Int, taps: [RhythmTap]) {
        self.id = UUID()
        self.themeId = themeId
        self.taps = taps
        self.createdAt = Date()
        let formatter = DateFormatter()
        formatter.dateFormat = "M/d HH:mm"
        self.title = formatter.string(from: Date())
    }
}

class GalleryStore: ObservableObject {
    @Published var rhythms: [SavedRhythm] = []

    private let key = "saved_rhythms"

    init() {
        load()
    }

    func save(_ rhythm: SavedRhythm) {
        rhythms.insert(rhythm, at: 0)
        if rhythms.count > 20 { rhythms = Array(rhythms.prefix(20)) }
        persist()
    }

    func delete(at offsets: IndexSet) {
        rhythms.remove(atOffsets: offsets)
        persist()
    }

    private func persist() {
        if let data = try? JSONEncoder().encode(rhythms) {
            UserDefaults.standard.set(data, forKey: key)
        }
    }

    private func load() {
        if let data = UserDefaults.standard.data(forKey: key),
           let saved = try? JSONDecoder().decode([SavedRhythm].self, from: data) {
            rhythms = saved
        }
    }
}
