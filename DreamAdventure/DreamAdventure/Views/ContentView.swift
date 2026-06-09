import SwiftUI

struct ContentView: View {
    @State private var selectedDream: DreamType? = nil
    @State private var showStory: Bool = false

    var body: some View {
        ZStack {
            if showStory, let dream = selectedDream {
                StoryView(dreamType: dream) {
                    withAnimation(.easeInOut(duration: 0.5)) {
                        showStory = false
                        selectedDream = nil
                    }
                }
                .transition(.opacity)
            } else {
                DreamSelectionView { dream in
                    selectedDream = dream
                    withAnimation(.easeInOut(duration: 0.5)) {
                        showStory = true
                    }
                }
                .transition(.opacity)
            }
        }
        .animation(.easeInOut(duration: 0.5), value: showStory)
    }
}
