import SwiftUI

struct GalleryView: View {
    @ObservedObject var galleryStore: GalleryStore
    @ObservedObject var rhythmVM: RhythmViewModel
    @Environment(\.dismiss) private var dismiss

    @State private var playingId: UUID? = nil

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color(hex: "#1a0533"), Color(hex: "#3d1a6e")],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                // Top bar
                HStack {
                    Button(action: {
                        rhythmVM.stopPlayback()
                        dismiss()
                    }) {
                        ZStack {
                            Circle()
                                .fill(Color.white.opacity(0.2))
                                .frame(width: 52, height: 52)
                            Text("🏠")
                                .font(.system(size: 28))
                        }
                    }

                    Spacer()

                    Text("🖼️ ギャラリー")
                        .font(.system(size: 26, weight: .black, design: .rounded))
                        .foregroundColor(.white)

                    Spacer()

                    // Placeholder to balance the back button
                    Color.clear.frame(width: 52, height: 52)
                }
                .padding(.horizontal, 20)
                .padding(.top, 8)
                .padding(.bottom, 16)

                if galleryStore.rhythms.isEmpty {
                    Spacer()
                    emptyState
                    Spacer()
                } else {
                    ScrollView(showsIndicators: false) {
                        LazyVGrid(
                            columns: [GridItem(.flexible(), spacing: 14), GridItem(.flexible(), spacing: 14)],
                            spacing: 14
                        ) {
                            ForEach(galleryStore.rhythms) { rhythm in
                                RhythmCard(
                                    rhythm: rhythm,
                                    isPlaying: playingId == rhythm.id,
                                    onPlay: { playRhythm(rhythm) },
                                    onStop: { stopRhythm() }
                                )
                            }
                        }
                        .padding(.horizontal, 20)
                        .padding(.bottom, 30)
                    }
                }
            }
        }
        .navigationBarHidden(true)
        .onDisappear { rhythmVM.stopPlayback() }
    }

    private var emptyState: some View {
        VStack(spacing: 18) {
            Text("🎵")
                .font(.system(size: 80))
            Text("まだないよ")
                .font(.system(size: 28, weight: .black, design: .rounded))
                .foregroundColor(.white.opacity(0.7))
            Text("リズムをつくってとっておこう！")
                .font(.system(size: 16, weight: .semibold, design: .rounded))
                .foregroundColor(.white.opacity(0.5))
        }
    }

    private func playRhythm(_ rhythm: SavedRhythm) {
        guard let theme = Theme.all.first(where: { $0.id == rhythm.themeId }) else { return }
        playingId = rhythm.id
        rhythmVM.playSavedRhythm(rhythm, theme: theme)
    }

    private func stopRhythm() {
        rhythmVM.stopPlayback()
        playingId = nil
    }
}

struct RhythmCard: View {
    let rhythm: SavedRhythm
    let isPlaying: Bool
    let onPlay: () -> Void
    let onStop: () -> Void

    private var theme: Theme? {
        Theme.all.first(where: { $0.id == rhythm.themeId })
    }

    var body: some View {
        Button(action: isPlaying ? onStop : onPlay) {
            ZStack {
                RoundedRectangle(cornerRadius: 22)
                    .fill(
                        LinearGradient(
                            colors: theme.map { [$0.gradientTop, $0.gradientBottom] } ?? [Color.gray, Color.gray.opacity(0.5)],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 22)
                            .stroke(isPlaying ? Color.white : Color.white.opacity(0.3), lineWidth: isPlaying ? 3 : 2)
                    )
                    .shadow(color: (theme?.gradientBottom ?? .gray).opacity(0.4), radius: 8, y: 4)

                VStack(spacing: 8) {
                    Text(theme?.characterEmoji ?? "🎵")
                        .font(.system(size: 48))
                        .scaleEffect(isPlaying ? 1.2 : 1.0)
                        .animation(.spring(response: 0.3).repeatForever(autoreverses: true), value: isPlaying)

                    Text(theme?.nameJP ?? "")
                        .font(.system(size: 18, weight: .black, design: .rounded))
                        .foregroundColor(.white)

                    Text(rhythm.title)
                        .font(.system(size: 12, weight: .semibold, design: .rounded))
                        .foregroundColor(.white.opacity(0.7))

                    // Play/stop icon
                    ZStack {
                        Circle()
                            .fill(Color.white.opacity(0.25))
                            .frame(width: 40, height: 40)
                        Text(isPlaying ? "⏹" : "▶️")
                            .font(.system(size: 22))
                    }
                }
                .padding(.vertical, 16)
            }
            .aspectRatio(1.0, contentMode: .fit)
        }
        .buttonStyle(PressableButtonStyle())
    }
}
