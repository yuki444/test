import SwiftUI

struct DreamSelectionView: View {
    let onSelect: (DreamType) -> Void

    @State private var titleScale: CGFloat = 0.5
    @State private var titleOpacity: Double = 0
    @State private var cardsVisible: [Bool] = [false, false, false]
    @State private var starPositions: [StarParticle] = StarParticle.generate(count: 20)
    @State private var starPhase: Double = 0

    var body: some View {
        ZStack {
            // 背景グラデーション（星空）
            LinearGradient(
                colors: [Color(red: 0.05, green: 0.05, blue: 0.2), Color(red: 0.1, green: 0.0, blue: 0.3)],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            // 星の背景アニメーション
            ForEach(starPositions) { star in
                Circle()
                    .fill(Color.white.opacity(star.opacity + sin(starPhase + star.phase) * 0.3))
                    .frame(width: star.size, height: star.size)
                    .position(x: star.x, y: star.y)
            }

            VStack(spacing: 32) {
                Spacer()

                // タイトル
                VStack(spacing: 8) {
                    Text("✨ ゆめのぼうけん ✨")
                        .font(.system(size: 32, weight: .bold, design: .rounded))
                        .foregroundColor(.white)
                        .shadow(color: .purple.opacity(0.8), radius: 10)

                    Text("きみの ゆめを えらんでね！")
                        .font(.system(size: 20, weight: .medium, design: .rounded))
                        .foregroundColor(.white.opacity(0.85))
                }
                .scaleEffect(titleScale)
                .opacity(titleOpacity)

                // 夢の選択カード
                VStack(spacing: 20) {
                    ForEach(Array(DreamType.allCases.enumerated()), id: \.element.id) { index, dream in
                        DreamCard(dream: dream) {
                            onSelect(dream)
                        }
                        .opacity(cardsVisible[index] ? 1 : 0)
                        .offset(y: cardsVisible[index] ? 0 : 40)
                    }
                }
                .padding(.horizontal, 24)

                Spacer()
            }
        }
        .onAppear {
            // タイトルアニメーション
            withAnimation(.spring(response: 0.6, dampingFraction: 0.7)) {
                titleScale = 1.0
                titleOpacity = 1.0
            }
            // カードを順番に表示
            for i in 0..<3 {
                withAnimation(.spring(response: 0.5, dampingFraction: 0.7).delay(Double(i) * 0.15 + 0.3)) {
                    cardsVisible[i] = true
                }
            }
            // 星のアニメーション
            withAnimation(.linear(duration: 4).repeatForever(autoreverses: false)) {
                starPhase = .pi * 2
            }
        }
    }
}

struct DreamCard: View {
    let dream: DreamType
    let onTap: () -> Void

    @State private var isPressed: Bool = false
    @State private var emojiFloat: Bool = false

    var body: some View {
        Button(action: onTap) {
            HStack(spacing: 20) {
                // 絵文字
                Text(dream.emoji)
                    .font(.system(size: 52))
                    .offset(y: emojiFloat ? -5 : 5)
                    .animation(.easeInOut(duration: 1.0).repeatForever(autoreverses: true), value: emojiFloat)

                VStack(alignment: .leading, spacing: 6) {
                    Text(dream.title)
                        .font(.system(size: 24, weight: .bold, design: .rounded))
                        .foregroundColor(.white)
                    Text(dream.animal.description)
                        .font(.system(size: 14, weight: .medium, design: .rounded))
                        .foregroundColor(.white.opacity(0.8))
                    HStack(spacing: 4) {
                        Text(dream.animal.emoji)
                        Text(dream.animal.name)
                            .font(.system(size: 13, design: .rounded))
                            .foregroundColor(.white.opacity(0.7))
                    }
                }
                Spacer()

                Image(systemName: "chevron.right")
                    .foregroundColor(.white.opacity(0.7))
                    .font(.system(size: 16, weight: .bold))
            }
            .padding(.horizontal, 24)
            .padding(.vertical, 20)
            .background(
                RoundedRectangle(cornerRadius: 24)
                    .fill(
                        LinearGradient(
                            colors: dream.gradientColors.map { $0.opacity(0.7) },
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 24)
                            .stroke(Color.white.opacity(0.25), lineWidth: 1.5)
                    )
            )
            .scaleEffect(isPressed ? 0.96 : 1.0)
            .shadow(color: dream.color.opacity(0.5), radius: 12, x: 0, y: 6)
        }
        .buttonStyle(.plain)
        .onTapGesture {
            withAnimation(.spring(response: 0.2)) {
                isPressed = true
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
                withAnimation(.spring(response: 0.2)) {
                    isPressed = false
                }
                onTap()
            }
        }
        .onAppear {
            emojiFloat = true
        }
    }
}

struct StarParticle: Identifiable {
    let id = UUID()
    let x: CGFloat
    let y: CGFloat
    let size: CGFloat
    let opacity: Double
    let phase: Double

    static func generate(count: Int) -> [StarParticle] {
        (0..<count).map { _ in
            StarParticle(
                x: CGFloat.random(in: 0...400),
                y: CGFloat.random(in: 0...900),
                size: CGFloat.random(in: 1.5...4),
                opacity: Double.random(in: 0.3...0.7),
                phase: Double.random(in: 0...(.pi * 2))
            )
        }
    }
}
