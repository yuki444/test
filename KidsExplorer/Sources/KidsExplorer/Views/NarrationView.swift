import SwiftUI

struct NarrationView: View {
    let scene: AdventureScene?
    let onFinished: () -> Void

    @State private var displayedText: String = ""
    @State private var showContinue: Bool = false
    @State private var bgScale: CGFloat = 1.0
    @State private var emojiOffset: CGFloat = 50

    var body: some View {
        ZStack {
            backgroundView

            VStack(spacing: 32) {
                Spacer()

                emojiRow

                narrationBubble

                if showContinue {
                    KidsButton(
                        title: "つぎへ！",
                        emoji: "➡️",
                        color: AppColor.primary
                    ) {
                        onFinished()
                    }
                    .padding(.horizontal, 24)
                    .transition(.move(edge: .bottom).combined(with: .opacity))
                }

                Spacer()
            }
        }
        .onAppear {
            startNarration()
        }
    }

    private var backgroundView: some View {
        ZStack {
            LinearGradient(
                colors: [Color(hex: "#E8F5E9"), Color(hex: "#E3F2FD")],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            ForEach(0..<12, id: \.self) { i in
                Circle()
                    .fill(AppColor.secondary.opacity(0.08))
                    .frame(width: CGFloat.random(in: 60...160))
                    .position(
                        x: CGFloat.random(in: 0...400),
                        y: CGFloat.random(in: 0...900)
                    )
            }
        }
    }

    private var emojiRow: some View {
        HStack(spacing: -8) {
            ForEach(Array((scene?.overlayEmojis.prefix(4) ?? ["✨", "🌟"]).enumerated()), id: \.0) { i, emoji in
                Text(emoji)
                    .font(.system(size: 44))
                    .rotationEffect(.degrees(Double(i) * 15 - 22))
                    .offset(y: emojiOffset)
                    .shadow(color: .black.opacity(0.1), radius: 4)
            }
        }
        .onAppear {
            withAnimation(.spring(duration: 0.8)) {
                emojiOffset = 0
            }
        }
    }

    private var narrationBubble: some View {
        VStack(spacing: 16) {
            Text("📖")
                .font(.system(size: 36))

            Text(displayedText)
                .font(.system(size: 22, weight: .semibold, design: .rounded))
                .foregroundStyle(AppColor.darkText)
                .multilineTextAlignment(.center)
                .lineSpacing(8)
                .padding(.horizontal, 28)
                .frame(minHeight: 160)
        }
        .padding(24)
        .background(
            RoundedRectangle(cornerRadius: 28)
                .fill(.white)
                .shadow(color: AppColor.softShadow, radius: 16, y: 6)
        )
        .padding(.horizontal, 20)
    }

    private func startNarration() {
        guard let scene = scene else {
            showContinue = true
            return
        }

        displayedText = scene.narration

        VoiceService.shared.speak(scene.narration) {
            withAnimation(.spring(duration: 0.6)) {
                showContinue = true
            }
        }

        DispatchQueue.main.asyncAfter(deadline: .now() + 8) {
            withAnimation(.spring(duration: 0.6)) {
                showContinue = true
            }
        }
    }
}
