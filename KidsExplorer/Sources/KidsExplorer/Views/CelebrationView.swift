import SwiftUI

struct CelebrationView: View {
    @Environment(AppState.self) private var appState
    @State private var bgHue: Double = 0
    @State private var centerScale: CGFloat = 0.3
    @State private var confettiPositions: [(CGFloat, CGFloat, CGFloat)] = []
    @State private var stampScale: CGFloat = 0
    @State private var showHomeButton: Bool = false

    private let emojis = ["🎉", "🎊", "⭐️", "🌟", "✨", "💫", "🎈", "🎁", "🏆", "🌈"]
    private let confettiCount = 30

    var body: some View {
        ZStack {
            animatedBackground
            confettiLayer
            centerContent
        }
        .onAppear {
            setupConfetti()
            startAnimation()
        }
    }

    private var animatedBackground: some View {
        ZStack {
            Color(hue: bgHue, saturation: 0.5, brightness: 0.98)
                .ignoresSafeArea()
                .animation(.linear(duration: 3).repeatForever(autoreverses: false), value: bgHue)

            RadialGradient(
                colors: [.white.opacity(0.4), .clear],
                center: .center,
                startRadius: 0,
                endRadius: 300
            )
            .ignoresSafeArea()
        }
        .onAppear {
            withAnimation(.linear(duration: 3).repeatForever(autoreverses: false)) {
                bgHue = 1.0
            }
        }
    }

    private var confettiLayer: some View {
        GeometryReader { geo in
            ForEach(0..<confettiPositions.count, id: \.self) { i in
                Text(emojis[i % emojis.count])
                    .font(.system(size: CGFloat.random(in: 24...44)))
                    .position(
                        x: confettiPositions[i].0 * geo.size.width,
                        y: confettiPositions[i].1 * geo.size.height
                    )
                    .rotationEffect(.degrees(confettiPositions[i].2))
                    .opacity(0.8)
            }
        }
    }

    private var centerContent: some View {
        VStack(spacing: 32) {
            Spacer()

            ZStack {
                ForEach(0..<8, id: \.self) { i in
                    Text(["🌟", "⭐️", "✨"][i % 3])
                        .font(.system(size: 36))
                        .offset(
                            x: cos(Double(i) * .pi / 4) * 100,
                            y: sin(Double(i) * .pi / 4) * 100
                        )
                }

                VStack(spacing: 8) {
                    Text("🏆")
                        .font(.system(size: 100))
                    Text("スタンプ ゲット！")
                        .font(.system(size: 24, weight: .black, design: .rounded))
                        .foregroundStyle(AppColor.primary)
                }
                .scaleEffect(stampScale)
            }
            .frame(height: 280)

            VStack(spacing: 12) {
                Text("きょうの ぼうけん おわり！")
                    .font(.system(size: 28, weight: .black, design: .rounded))
                    .foregroundStyle(AppColor.darkText)

                Text("またあした あそんでね！")
                    .font(AppFont.body)
                    .foregroundStyle(.secondary)
            }
            .padding(.horizontal, 32)
            .multilineTextAlignment(.center)
            .scaleEffect(centerScale)

            Spacer()

            if showHomeButton {
                VStack(spacing: 12) {
                    KidsButton(
                        title: "おうちに かえる",
                        emoji: "🏠",
                        color: AppColor.primary
                    ) {
                        withAnimation {
                            appState.currentScreen = .home
                        }
                    }
                    .padding(.horizontal, 24)

                    Button("もういちど あそぶ") {
                        withAnimation {
                            appState.currentScreen = .intro
                        }
                    }
                    .font(AppFont.body)
                    .foregroundStyle(.secondary)
                    .padding(.bottom, 8)
                }
                .padding(.bottom, 48)
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
    }

    private func setupConfetti() {
        confettiPositions = (0..<confettiCount).map { _ in
            (CGFloat.random(in: 0...1), CGFloat.random(in: 0...1), Double.random(in: 0...360))
        }
    }

    private func startAnimation() {
        withAnimation(.spring(duration: 0.8, bounce: 0.4).delay(0.3)) {
            centerScale = 1.0
            stampScale = 1.0
        }

        VoiceService.shared.speak("やったー！ぼうけんスタンプを ゲットしたよ！またあした あそんでね！") {
            withAnimation(.spring(duration: 0.5)) {
                showHomeButton = true
            }
        }

        DispatchQueue.main.asyncAfter(deadline: .now() + 5) {
            withAnimation(.spring(duration: 0.5)) {
                showHomeButton = true
            }
        }
    }
}
