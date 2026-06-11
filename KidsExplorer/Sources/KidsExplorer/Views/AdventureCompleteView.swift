import SwiftUI

struct AdventureCompleteView: View {
    let adventure: Adventure
    let animal: AnimalCharacter?
    let onFinish: () -> Void

    @State private var stars: [Bool] = [false, false, false]
    @State private var animalBounce: CGFloat = 0
    @State private var titleScale: CGFloat = 0.5
    @State private var showButton: Bool = false

    var body: some View {
        ZStack {
            backgroundView
            contentView
        }
        .onAppear {
            startSequence()
        }
    }

    private var backgroundView: some View {
        ZStack {
            LinearGradient(
                colors: [Color(hex: "#FFD700").opacity(0.4), Color(hex: "#FF8C42").opacity(0.3)],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            ForEach(0..<16, id: \.self) { i in
                Text(["🌟", "⭐️", "✨", "💫"][i % 4])
                    .font(.system(size: CGFloat.random(in: 20...40)))
                    .position(
                        x: CGFloat.random(in: 10...390),
                        y: CGFloat.random(in: 50...800)
                    )
                    .opacity(Double.random(in: 0.4...0.9))
            }
        }
    }

    private var contentView: some View {
        VStack(spacing: 28) {
            Spacer()

            Text(animal?.emoji ?? "🐻")
                .font(.system(size: 100))
                .offset(y: animalBounce)
                .shadow(color: .black.opacity(0.1), radius: 8, y: 6)

            VStack(spacing: 12) {
                Text("🎊 ぼうけん かんりょう！ 🎊")
                    .font(.system(size: 26, weight: .black, design: .rounded))
                    .foregroundStyle(AppColor.primary)
                    .scaleEffect(titleScale)

                Text(adventure.title)
                    .font(AppFont.headline)
                    .foregroundStyle(AppColor.darkText)

                Text(animal?.completionPhrase ?? "よくがんばったね！")
                    .font(AppFont.body)
                    .foregroundStyle(.secondary)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 32)
            }

            starsRow

            Spacer()

            if showButton {
                KidsButton(
                    title: "ごほうびを もらう！",
                    emoji: "🎁",
                    color: AppColor.primary
                ) {
                    onFinish()
                }
                .padding(.horizontal, 24)
                .padding(.bottom, 48)
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }
        }
    }

    private var starsRow: some View {
        HStack(spacing: 16) {
            ForEach(0..<3) { i in
                Text("⭐️")
                    .font(.system(size: stars[i] ? 52 : 32))
                    .opacity(stars[i] ? 1 : 0.3)
                    .scaleEffect(stars[i] ? 1.2 : 1.0)
                    .animation(.spring(duration: 0.5, bounce: 0.5).delay(Double(i) * 0.3), value: stars[i])
            }
        }
    }

    private func startSequence() {
        withAnimation(.spring(duration: 0.7, bounce: 0.3).delay(0.2)) {
            titleScale = 1.0
        }
        withAnimation(.easeInOut(duration: 1.0).repeatForever(autoreverses: true).delay(0.5)) {
            animalBounce = -10
        }

        for i in 0..<3 {
            DispatchQueue.main.asyncAfter(deadline: .now() + Double(i) * 0.5 + 0.8) {
                withAnimation { stars[i] = true }
            }
        }

        if let animal = animal {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                VoiceService.shared.speak("ぼうけんかんりょう！\(animal.completionPhrase)") {
                    withAnimation(.spring(duration: 0.5)) {
                        showButton = true
                    }
                }
            }
        }

        DispatchQueue.main.asyncAfter(deadline: .now() + 5) {
            withAnimation(.spring(duration: 0.5)) {
                showButton = true
            }
        }
    }
}
