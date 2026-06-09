import SwiftUI

struct PraiseView: View {
    let theme: Theme
    let onDismiss: () -> Void
    let onSave: () -> Void

    @State private var scale = 0.3
    @State private var opacity = 0.0
    @State private var confettiItems: [ConfettiItem] = []
    @State private var starPulse = false

    var body: some View {
        ZStack {
            // Dimmed background
            Color.black.opacity(0.55)
                .ignoresSafeArea()
                .onTapGesture { dismiss() }

            // Confetti
            ForEach(confettiItems) { item in
                Text(item.emoji)
                    .font(.system(size: item.size))
                    .position(item.position)
                    .opacity(item.opacity)
                    .rotationEffect(.degrees(item.rotation))
            }

            VStack(spacing: 20) {
                // Character bouncing
                Text(theme.characterEmoji)
                    .font(.system(size: 90))
                    .scaleEffect(starPulse ? 1.15 : 1.0)
                    .animation(.easeInOut(duration: 0.5).repeatForever(autoreverses: true), value: starPulse)

                // Praise text (emoji only – no Japanese for kids)
                HStack(spacing: 8) {
                    Text("⭐").font(.system(size: 36))
                    Text("🎉").font(.system(size: 48))
                    Text("⭐").font(.system(size: 36))
                }

                Text("やったね！")
                    .font(.system(size: 40, weight: .black, design: .rounded))
                    .foregroundColor(.white)
                    .shadow(color: theme.accentColor, radius: 8)

                HStack(spacing: 24) {
                    // Save button
                    Button(action: {
                        onSave()
                        dismiss()
                    }) {
                        VStack(spacing: 6) {
                            Text("💾")
                                .font(.system(size: 44))
                            Text("とっておく")
                                .font(.system(size: 16, weight: .bold, design: .rounded))
                                .foregroundColor(.white)
                        }
                        .frame(width: 110, height: 100)
                        .background(
                            RoundedRectangle(cornerRadius: 22)
                                .fill(Color(hex: "#FF6B9D").opacity(0.85))
                                .overlay(RoundedRectangle(cornerRadius: 22).stroke(Color.white.opacity(0.6), lineWidth: 2))
                        )
                    }

                    // Continue button
                    Button(action: { dismiss() }) {
                        VStack(spacing: 6) {
                            Text("▶️")
                                .font(.system(size: 44))
                            Text("つづける")
                                .font(.system(size: 16, weight: .bold, design: .rounded))
                                .foregroundColor(.white)
                        }
                        .frame(width: 110, height: 100)
                        .background(
                            RoundedRectangle(cornerRadius: 22)
                                .fill(Color(hex: "#48CFAD").opacity(0.85))
                                .overlay(RoundedRectangle(cornerRadius: 22).stroke(Color.white.opacity(0.6), lineWidth: 2))
                        )
                    }
                }
            }
            .scaleEffect(scale)
            .opacity(opacity)
        }
        .onAppear {
            withAnimation(.spring(response: 0.45, dampingFraction: 0.6)) {
                scale = 1.0
                opacity = 1.0
            }
            starPulse = true
            spawnConfetti()
        }
    }

    private func dismiss() {
        withAnimation(.easeIn(duration: 0.25)) {
            scale = 0.8
            opacity = 0
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) {
            onDismiss()
        }
    }

    private func spawnConfetti() {
        let emojis = ["🌟", "⭐", "✨", "🎉", "🎊", theme.particleEmoji, theme.emoji]
        let screenW: CGFloat = 390
        let screenH: CGFloat = 844

        confettiItems = (0..<30).map { _ in
            ConfettiItem(
                emoji: emojis.randomElement()!,
                position: CGPoint(x: CGFloat.random(in: 20...screenW-20), y: CGFloat.random(in: 50...screenH-50)),
                size: CGFloat.random(in: 18...36),
                opacity: Double.random(in: 0.6...1.0),
                rotation: Double.random(in: -45...45)
            )
        }
    }
}

struct ConfettiItem: Identifiable {
    let id = UUID()
    let emoji: String
    let position: CGPoint
    let size: CGFloat
    let opacity: Double
    let rotation: Double
}
