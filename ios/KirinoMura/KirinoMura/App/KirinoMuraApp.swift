import SwiftUI

@main
struct KirinoMuraApp: App {
    @StateObject private var gameState = GameStateService()

    var body: some Scene {
        WindowGroup {
            ContentView()
                .environmentObject(gameState)
        }
    }
}
