import SwiftUI

struct CelebrationView: View {
    let category: TreasureCategory
    let isNewLevel: Bool
    let onDismiss: () -> Void

    @State private var scale: CGFloat = 0.3
    @State private var opacity: Double = 0
    @State private var bounce: CGFloat = 0
    @State private var particles: [ConfettiParticle] = []

    private let emojiBag = ["⭐", "🌟", "✨", "🎊", "🎉", "💫", "🌈"]

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color(hex: "#FFF9C4"), category.color.opacity(0.25)],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            // Confetti layer
            ForEach(particles) { p in
                Text(p.emoji)
                    .font(.system(size: p.size))
                    .position(x: p.x, y: p.y)
                    .opacity(p.opacity)
                    .rotationEffect(.degrees(p.rotation))
            }

            VStack(spacing: 24) {
                Spacer()

                // Main character
                Text("🎉")
                    .font(.system(size: 96))
                    .scaleEffect(scale)
                    .offset(y: bounce)

                VStack(spacing: 10) {
                    Text("すごい！")
                        .font(.system(size: 48, weight: .black, design: .rounded))
                        .foregroundColor(category.color)

                    Text("がんばったね！")
                        .font(.system(size: 32, weight: .bold, design: .rounded))
                        .foregroundColor(Color(hex: "#5D4037"))

                    if isNewLevel {
                        let info = LevelSystem.info(for: 0) // just for emoji lookup — actual level shown below
                        VStack(spacing: 6) {
                            Text("🎊 レベルアップ！ 🎊")
                                .font(.system(size: 28, weight: .black, design: .rounded))
                                .foregroundColor(.orange)
                            Text("⭐️⭐️⭐️")
                                .font(.system(size: 38))
                        }
                        .padding(.horizontal, 20)
                        .padding(.vertical, 12)
                        .background(Color.yellow.opacity(0.25))
                        .cornerRadius(18)
                        .overlay(
                            RoundedRectangle(cornerRadius: 18)
                                .stroke(Color.orange, lineWidth: 3)
                        )
                    }

                    HStack(spacing: 6) {
                        Text(category.emoji)
                            .font(.system(size: 28))
                        Text("\(category.name)の　たからもの　に　なったよ！")
                            .font(.system(size: 16, weight: .semibold, design: .rounded))
                            .foregroundColor(Color(hex: "#5D4037"))
                            .multilineTextAlignment(.center)
                    }
                    .padding(.horizontal, 16)
                    .padding(.vertical, 10)
                    .background(Color.white.opacity(0.8))
                    .cornerRadius(14)
                    .padding(.horizontal)
                }
                .opacity(opacity)

                Spacer()

                Button(action: onDismiss) {
                    Text("やったー！")
                        .font(.system(size: 26, weight: .black, design: .rounded))
                        .foregroundColor(.white)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 18)
                        .background(
                            LinearGradient(
                                colors: [Color(hex: "#FF6B6B"), Color(hex: "#FF8E53")],
                                startPoint: .leading,
                                endPoint: .trailing
                            )
                        )
                        .cornerRadius(24)
                        .shadow(color: .orange.opacity(0.5), radius: 10, x: 0, y: 5)
                }
                .padding(.horizontal, 28)
                .padding(.bottom, 52)
                .opacity(opacity)
            }
        }
        .onAppear { animate() }
    }

    private func animate() {
        withAnimation(.spring(response: 0.55, dampingFraction: 0.5)) { scale = 1.0 }
        withAnimation(.easeIn(duration: 0.4).delay(0.3)) { opacity = 1.0 }
        withAnimation(
            Animation.easeInOut(duration: 0.45)
                .repeatForever(autoreverses: true)
                .delay(0.5)
        ) { bounce = -18 }

        let screenW = UIScreen.main.bounds.width
        let screenH = UIScreen.main.bounds.height
        particles = (0..<35).map { _ in
            ConfettiParticle(
                id: UUID(),
                emoji: (emojiBag + [category.emoji]).randomElement()!,
                x: CGFloat.random(in: 0...screenW),
                y: CGFloat.random(in: 0...screenH),
                size: CGFloat.random(in: 18...44),
                opacity: Double.random(in: 0.55...1.0),
                rotation: Double.random(in: 0...360)
            )
        }
    }
}

struct ConfettiParticle: Identifiable {
    let id: UUID
    let emoji: String
    let x: CGFloat
    let y: CGFloat
    let size: CGFloat
    let opacity: Double
    let rotation: Double
}
