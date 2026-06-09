import SwiftUI

struct ThemePageView: View {
    let theme: Theme
    @ObservedObject var rhythmVM: RhythmViewModel
    let galleryStore: GalleryStore
    let onBack: () -> Void
    let onGallery: () -> Void

    @State private var recordingPulse = false
    @State private var saveFlash = false

    var body: some View {
        ZStack {
            // Background gradient
            LinearGradient(
                colors: [theme.gradientTop, theme.gradientBottom],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                topBar
                Spacer(minLength: 0)
                characterArea
                Spacer(minLength: 12)
                soundButtons
                Spacer(minLength: 16)
                controlArea
                Spacer(minLength: 20)
            }
            .padding(.horizontal, 20)

            // Praise overlay
            if rhythmVM.showPraise {
                PraiseView(
                    theme: theme,
                    onDismiss: { rhythmVM.showPraise = false },
                    onSave: {
                        let saved = rhythmVM.buildSavedRhythm(themeId: theme.id)
                        galleryStore.save(saved)
                        withAnimation(.spring()) { saveFlash = true }
                        DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) { saveFlash = false }
                    }
                )
                .transition(.opacity)
                .zIndex(10)
            }
        }
        .navigationBarHidden(true)
        .onDisappear { rhythmVM.stopPlayback() }
    }

    // MARK: - Top Bar

    private var topBar: some View {
        HStack {
            // Back button
            Button(action: onBack) {
                ZStack {
                    Circle()
                        .fill(Color.white.opacity(0.2))
                        .frame(width: 52, height: 52)
                    Text("🏠")
                        .font(.system(size: 28))
                }
            }

            Spacer()

            // Theme name
            Text(theme.emoji + " " + theme.nameJP)
                .font(.system(size: 28, weight: .black, design: .rounded))
                .foregroundColor(.white)
                .shadow(radius: 4)

            Spacer()

            // Gallery button
            Button(action: onGallery) {
                ZStack {
                    Circle()
                        .fill(Color.white.opacity(0.2))
                        .frame(width: 52, height: 52)
                    Text(saveFlash ? "💛" : "🖼️")
                        .font(.system(size: 28))
                        .scaleEffect(saveFlash ? 1.4 : 1.0)
                        .animation(.spring(response: 0.2, dampingFraction: 0.4), value: saveFlash)
                }
            }
        }
        .padding(.top, 8)
    }

    // MARK: - Character

    private var characterArea: some View {
        VStack(spacing: 6) {
            CharacterView(theme: theme, beat: rhythmVM.characterBeat)

            // State indicator
            stateIndicator
        }
    }

    @ViewBuilder
    private var stateIndicator: some View {
        switch rhythmVM.state {
        case .idle:
            EmptyView()
        case .recording(let remaining):
            ZStack {
                RoundedRectangle(cornerRadius: 16)
                    .fill(Color.red.opacity(0.75))
                    .frame(width: 160, height: 38)
                    .overlay(
                        RoundedRectangle(cornerRadius: 16)
                            .stroke(Color.white.opacity(0.6), lineWidth: 2)
                            .scaleEffect(recordingPulse ? 1.06 : 1.0)
                            .animation(.easeInOut(duration: 0.4).repeatForever(autoreverses: true), value: recordingPulse)
                    )
                HStack(spacing: 8) {
                    Circle()
                        .fill(Color.white)
                        .frame(width: 10, height: 10)
                        .opacity(recordingPulse ? 1 : 0.3)
                        .animation(.easeInOut(duration: 0.4).repeatForever(autoreverses: true), value: recordingPulse)
                    Text(String(format: "%.1f", remaining))
                        .font(.system(size: 20, weight: .bold, design: .monospaced))
                        .foregroundColor(.white)
                }
            }
            .onAppear { recordingPulse = true }
            .onDisappear { recordingPulse = false }

        case .playing:
            HStack(spacing: 6) {
                ForEach(0..<4) { i in
                    RoundedRectangle(cornerRadius: 3)
                        .fill(theme.accentColor)
                        .frame(width: 6, height: rhythmVM.characterBeat ? 28 : 14)
                        .animation(.spring(response: 0.15).delay(Double(i) * 0.04), value: rhythmVM.characterBeat)
                }
            }
            .frame(height: 38)
        }
    }

    // MARK: - Sound Buttons (2×2 grid)

    private var soundButtons: some View {
        LazyVGrid(
            columns: [GridItem(.flexible(), spacing: 14), GridItem(.flexible(), spacing: 14)],
            spacing: 14
        ) {
            ForEach(theme.buttons) { button in
                SoundButtonView(
                    button: button,
                    isActive: rhythmVM.activeButtonId == button.id
                ) {
                    rhythmVM.tapButton(button, theme: theme)
                }
                .aspectRatio(1.0, contentMode: .fit)
            }
        }
    }

    // MARK: - Control Area

    private var controlArea: some View {
        Group {
            switch rhythmVM.state {
            case .idle:
                recordButton
            case .recording:
                // During recording just show the buttons (no extra control)
                EmptyView()
            case .playing:
                HStack(spacing: 20) {
                    stopButton
                    recordAgainButton
                }
            }
        }
    }

    private var recordButton: some View {
        Button(action: { rhythmVM.startRecording(theme: theme) }) {
            ZStack {
                Capsule()
                    .fill(LinearGradient(colors: [Color(hex: "#FF6B9D"), Color(hex: "#FF4466")], startPoint: .leading, endPoint: .trailing))
                    .shadow(color: Color(hex: "#FF6B9D").opacity(0.6), radius: 12, y: 4)
                HStack(spacing: 12) {
                    Text("🎵")
                        .font(.system(size: 32))
                    Text("はじめる")
                        .font(.system(size: 26, weight: .black, design: .rounded))
                        .foregroundColor(.white)
                }
                .padding(.horizontal, 28)
                .padding(.vertical, 14)
            }
        }
        .buttonStyle(PressableButtonStyle())
    }

    private var stopButton: some View {
        Button(action: { rhythmVM.stopPlayback() }) {
            ZStack {
                Capsule()
                    .fill(Color.white.opacity(0.25))
                    .overlay(Capsule().stroke(Color.white.opacity(0.5), lineWidth: 2))
                HStack(spacing: 10) {
                    Text("⏹")
                        .font(.system(size: 26))
                    Text("とめる")
                        .font(.system(size: 22, weight: .bold, design: .rounded))
                        .foregroundColor(.white)
                }
                .padding(.horizontal, 22)
                .padding(.vertical, 12)
            }
        }
        .buttonStyle(PressableButtonStyle())
    }

    private var recordAgainButton: some View {
        Button(action: { rhythmVM.startRecording(theme: theme) }) {
            ZStack {
                Capsule()
                    .fill(Color(hex: "#FF6B9D").opacity(0.85))
                HStack(spacing: 10) {
                    Text("🔄")
                        .font(.system(size: 26))
                    Text("もういちど")
                        .font(.system(size: 20, weight: .bold, design: .rounded))
                        .foregroundColor(.white)
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 12)
            }
        }
        .buttonStyle(PressableButtonStyle())
    }
}

struct PressableButtonStyle: ButtonStyle {
    func makeBody(configuration: Configuration) -> some View {
        configuration.label
            .scaleEffect(configuration.isPressed ? 0.93 : 1.0)
            .animation(.spring(response: 0.15, dampingFraction: 0.6), value: configuration.isPressed)
    }
}
