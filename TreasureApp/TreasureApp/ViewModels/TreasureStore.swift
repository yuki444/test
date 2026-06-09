import Foundation
import UIKit

class TreasureStore: ObservableObject {
    @Published var categories: [TreasureCategory] = []
    @Published var items: [TreasureItem] = []

    private let categoriesKey = "treasure_categories_v1"
    private let itemsKey = "treasure_items_v1"

    var imagesDirectory: URL {
        FileManager.default.urls(for: .documentDirectory, in: .userDomainMask)[0]
            .appendingPathComponent("TreasureImages", isDirectory: true)
    }

    init() {
        createImagesDirectoryIfNeeded()
        loadCategories()
        loadItems()
    }

    // MARK: - Setup

    private func createImagesDirectoryIfNeeded() {
        try? FileManager.default.createDirectory(at: imagesDirectory, withIntermediateDirectories: true)
    }

    // MARK: - Categories

    private func loadCategories() {
        if let data = UserDefaults.standard.data(forKey: categoriesKey),
           let decoded = try? JSONDecoder().decode([TreasureCategory].self, from: data) {
            categories = decoded
        } else {
            categories = TreasureCategory.defaults
            saveCategories()
        }
    }

    func saveCategories() {
        if let data = try? JSONEncoder().encode(categories) {
            UserDefaults.standard.set(data, forKey: categoriesKey)
        }
    }

    func addCustomCategory(name: String, emoji: String, colorHex: String = "#9C27B0") {
        let category = TreasureCategory(
            id: UUID(),
            name: name,
            emoji: emoji,
            colorHex: colorHex,
            subcategories: [],
            isCustom: true
        )
        categories.append(category)
        saveCategories()
    }

    func updateSubcategories(for categoryId: UUID, subcategories: [String]) {
        if let idx = categories.firstIndex(where: { $0.id == categoryId }) {
            categories[idx].subcategories = subcategories
            saveCategories()
        }
    }

    // MARK: - Items

    private func loadItems() {
        if let data = UserDefaults.standard.data(forKey: itemsKey),
           let decoded = try? JSONDecoder().decode([TreasureItem].self, from: data) {
            items = decoded
        }
    }

    func saveItems() {
        if let data = try? JSONEncoder().encode(items) {
            UserDefaults.standard.set(data, forKey: itemsKey)
        }
    }

    func addTreasure(image: UIImage, categoryId: UUID, subcategory: String) {
        let filename = "\(UUID().uuidString).jpg"
        let url = imagesDirectory.appendingPathComponent(filename)
        if let data = image.jpegData(compressionQuality: 0.8) {
            try? data.write(to: url)
        }
        let item = TreasureItem(categoryId: categoryId, subcategory: subcategory, imageFilename: filename)
        items.append(item)
        saveItems()
    }

    func loadImage(filename: String) -> UIImage? {
        UIImage(contentsOfFile: imagesDirectory.appendingPathComponent(filename).path)
    }

    func items(for categoryId: UUID) -> [TreasureItem] {
        items.filter { $0.categoryId == categoryId }
            .sorted { $0.date > $1.date }
    }

    func count(for categoryId: UUID) -> Int {
        items.filter { $0.categoryId == categoryId }.count
    }

    func deleteItem(_ item: TreasureItem) {
        try? FileManager.default.removeItem(
            at: imagesDirectory.appendingPathComponent(item.imageFilename)
        )
        items.removeAll { $0.id == item.id }
        saveItems()
    }
}
