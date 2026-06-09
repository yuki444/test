import SwiftUI
import Combine

enum AppScreen {
    case home
    case theme(Theme)
    case gallery
}

class AppViewModel: ObservableObject {
    @Published var screen: AppScreen = .home
    @Published var showGallery = false

    let audioEngine = AudioEngine()
    lazy var rhythmVM = RhythmViewModel(audioEngine: audioEngine)
    let galleryStore = GalleryStore()

    func openTheme(_ theme: Theme) {
        rhythmVM.stopPlayback()
        screen = .theme(theme)
    }

    func goHome() {
        rhythmVM.stopPlayback()
        screen = .home
    }

    func openGallery() {
        rhythmVM.stopPlayback()
        showGallery = true
    }
}
