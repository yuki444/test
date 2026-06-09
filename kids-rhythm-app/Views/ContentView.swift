import SwiftUI

struct ContentView: View {
    @StateObject private var appVM = AppViewModel()

    var body: some View {
        ZStack {
            switch appVM.screen {
            case .home:
                HomeView(
                    onSelectTheme: { appVM.openTheme($0) },
                    onGallery: { appVM.openGallery() }
                )
                .transition(.asymmetric(insertion: .opacity, removal: .move(edge: .leading)))

            case .theme(let theme):
                ThemePageView(
                    theme: theme,
                    rhythmVM: appVM.rhythmVM,
                    galleryStore: appVM.galleryStore,
                    onBack: { appVM.goHome() },
                    onGallery: { appVM.openGallery() }
                )
                .transition(.asymmetric(insertion: .move(edge: .trailing), removal: .move(edge: .trailing)))

            case .gallery:
                EmptyView()
            }
        }
        .animation(.easeInOut(duration: 0.3), value: appVM.screen.id)
        .sheet(isPresented: $appVM.showGallery) {
            GalleryView(galleryStore: appVM.galleryStore, rhythmVM: appVM.rhythmVM)
        }
    }
}

extension AppScreen: Equatable {
    static func == (lhs: AppScreen, rhs: AppScreen) -> Bool {
        switch (lhs, rhs) {
        case (.home, .home): return true
        case (.gallery, .gallery): return true
        case (.theme(let a), .theme(let b)): return a.id == b.id
        default: return false
        }
    }

    var id: Int {
        switch self {
        case .home: return -1
        case .gallery: return -2
        case .theme(let t): return t.id
        }
    }
}
