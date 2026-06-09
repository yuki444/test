import Foundation

struct TreasureItem: Identifiable, Codable {
    let id: UUID
    let date: Date
    var categoryId: UUID
    var subcategory: String
    var imageFilename: String

    init(
        id: UUID = UUID(),
        date: Date = Date(),
        categoryId: UUID,
        subcategory: String,
        imageFilename: String
    ) {
        self.id = id
        self.date = date
        self.categoryId = categoryId
        self.subcategory = subcategory
        self.imageFilename = imageFilename
    }
}
