import Foundation

enum StoryData {
    static func story(for dreamType: DreamType) -> Story {
        switch dreamType {
        case .astronaut: return astronautStory
        case .baker:     return bakerStory
        case .explorer:  return explorerStory
        }
    }
}
