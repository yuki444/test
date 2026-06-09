import SwiftUI

@main
struct TreasureApp: App {
    @StateObject private var store = TreasureStore()

    var body: some Scene {
        WindowGroup {
            HomeView()
                .environmentObject(store)
        }
    }
}
