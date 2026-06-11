import SwiftUI

struct ContentView: View {
    @Environment(AppState.self) private var appState

    var body: some View {
        Group {
            switch appState.currentScreen {
            case .home:
                HomeView()
            case .intro:
                AdventureIntroView()
            case .adventure:
                if let adventure = appState.todaysAdventure {
                    AdventureContainerView(adventure: adventure)
                } else {
                    HomeView()
                }
            case .celebration:
                CelebrationView()
            }
        }
        .animation(.easeInOut(duration: 0.4), value: appState.currentScreen)
        .onAppear {
            loadTodaysContent()
        }
    }

    private func loadTodaysContent() {
        appState.todaysAdventure = DailyContentService.shared.todaysAdventure()
        appState.todaysAnimal = DailyContentService.shared.todaysAnimal()
    }
}
