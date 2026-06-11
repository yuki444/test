import SwiftUI

struct AdventureIntroView: View {
    @Environment(AppState.self) private var appState
    @State private var titleScale: CGFloat = 0.5
    @State private var animalOffset: CGFloat = 200
    @State private var showButton: Bool = false
    @State private var particleOffset: [CGFloat] = Array(repeating: 0, count: 8)
    @State private var isSpeaking: Bool = false

    var body: some View {
        ZStack {
            backgroundView
            particlesView
            contentView
        }
        .onAppear {
            startIntroAnimation()
        }
    }

    private var backgroundView: some View {
        ZStack {
            LinearGradient(
                colors: [
                    Color(hex: "#1a1a4e"),
                    Color(hex: "#2d1b69"),
                    Color(hex: "#11002e")
                ],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            ForEach(0..<20, id: \.self) { i in
                Text("⭐️")
                    .font(.system(size: CGFloat.random(in: 12...28)))
                    .position(
                        x: CGFloat.random(in: 20...380),
                        y: CGFloat.random(in: 40...800)
                    )
                    .opacity(Double.random(in: 0.3...0.9))
            }
        }
    }

    private var particlesView: some View {
        let emojis = ["✨", "🌟", "💫", "⭐️", "🎉", "🎊", "🌈", "🦋"]
        return ForEach(0..<emojis.count, id: \.self) { i in
            Text(emojis[i])
                .font(.system(size: 30))
                .offset(
                    x: CGFloat([-120, 120, -80, 100, -140, 130, -60, 90][i]),
                    y: particleOffset[i]
                )
                .opacity(0.7)
        }
    }

    private var contentView: some View {
        VStack(spacing: 32) {
            Spacer()

            if let adventure = appState.todaysAdventure {
                VStack(spacing: 16) {
                    Text("✨")
                        .font(.system(size: 60))

                    Text(adventure.title)
                        .font(.system(size: 32, weight: .black, design: .rounded))
                        .foregroundStyle(.white)
                        .multilineTextAlignment(.center)
                        .shadow(color: .black.opacity(0.3), radius: 4)
                        .scaleEffect(titleScale)

                    Text(adventure.subtitle)
                        .font(AppFont.body)
                        .foregroundStyle(.white.opacity(0.9))
                        .multilineTextAlignment(.center)
                }
                .padding(.horizontal, 24)
            }

            if let animal = appState.todaysAnimal {
                VStack(spacing: 12) {
                    Text(animal.emoji)
                        .font(.system(size: 90))
                        .shadow(color: .black.opacity(0.2), radius: 8, y: 6)
                        .offset(y: animalOffset)

                    if animalOffset == 0 {
                        Text(animal.name)
                            .font(AppFont.headline)
                            .foregroundStyle(.white)
                            .transition(.opacity.combined(with: .scale))
                    }
                }
                .frame(height: 160)
            }

            Spacer()

            if showButton {
                VStack(spacing: 16) {
                    if isSpeaking {
                        HStack(spacing: 8) {
                            ForEach(0..<3) { i in
                                RoundedRectangle(cornerRadius: 3)
                                    .fill(.white)
                                    .frame(width: 6, height: 20 + CGFloat(i * 6))
                                    .animation(
                                        .easeInOut(duration: 0.5).repeatForever().delay(Double(i) * 0.15),
                                        value: isSpeaking
                                    )
                            }
                        }
                        Text("おはなし ちゅう...")
                            .font(AppFont.caption)
                            .foregroundStyle(.white.opacity(0.7))
                    }

                    KidsButton(
                        title: "ぼうけん はじめよう！",
                        emoji: "🚀",
                        color: AppColor.primary
                    ) {
                        withAnimation {
                            appState.currentScreen = .adventure
                        }
                    }
                    .padding(.horizontal, 24)

                    Button("もどる") {
                        withAnimation {
                            appState.currentScreen = .home
                        }
                    }
                    .font(AppFont.caption)
                    .foregroundStyle(.white.opacity(0.6))
                }
                .transition(.move(edge: .bottom).combined(with: .opacity))
                .padding(.bottom, 40)
            }
        }
    }

    private func startIntroAnimation() {
        withAnimation(.spring(duration: 0.8).delay(0.3)) {
            titleScale = 1.0
        }
        withAnimation(.spring(duration: 0.9, bounce: 0.3).delay(0.8)) {
            animalOffset = 0
        }
        for i in 0..<particleOffset.count {
            withAnimation(.easeInOut(duration: 2.0 + Double(i) * 0.2).repeatForever(autoreverses: true).delay(Double(i) * 0.3)) {
                particleOffset[i] = CGFloat([-30, 30, -20, 25, -40, 35, -15, 20][i])
            }
        }

        if let adventure = appState.todaysAdventure {
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                isSpeaking = true
                VoiceService.shared.speak(adventure.openingNarration) {
                    isSpeaking = false
                    withAnimation(.spring(duration: 0.6)) {
                        showButton = true
                    }
                }
            }
        } else {
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) {
                withAnimation(.spring(duration: 0.6)) {
                    showButton = true
                }
            }
        }
    }
}
