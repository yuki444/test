import SwiftUI

struct CharacterIntroView: View {
    let animal: AnimalCharacter?
    let scene: AdventureScene?
    let onContinue: () -> Void

    @State private var animalScale: CGFloat = 0.3
    @State private var bubbleOpacity: Double = 0
    @State private var showButton: Bool = false
    @State private var isJumping: Bool = false

    var body: some View {
        ZStack {
            backgroundGradient

            VStack(spacing: 0) {
                Spacer()

                characterView

                speechBubble

                Spacer()

                if showButton {
                    KidsButton(
                        title: "クイズに ちょうせん！",
                        emoji: "🎯",
                        color: AppColor.primary
                    ) {
                        onContinue()
                    }
                    .padding(.horizontal, 24)
                    .padding(.bottom, 48)
                    .transition(.move(edge: .bottom).combined(with: .opacity))
                }
            }
        }
        .onAppear {
            startAnimation()
        }
    }

    private var backgroundGradient: some View {
        LinearGradient(
            colors: [
                Color(hex: "#FFF8E1"),
                Color(hex: "#F3E5F5")
            ],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
        .ignoresSafeArea()
    }

    private var characterView: some View {
        ZStack {
            PulsingCircle(color: AppColor.yellow)
                .frame(width: 180, height: 180)

            Text(animal?.emoji ?? "🐻")
                .font(.system(size: 100))
                .scaleEffect(animalScale)
                .offset(y: isJumping ? -12 : 0)
                .shadow(color: .black.opacity(0.1), radius: 8, y: 6)
        }
        .frame(height: 200)
    }

    private var speechBubble: some View {
        VStack(spacing: 8) {
            Text(animal?.name ?? "")
                .font(.system(size: 24, weight: .black, design: .rounded))
                .foregroundStyle(AppColor.primary)

            ZStack(alignment: .topLeading) {
                RoundedRectangle(cornerRadius: 24)
                    .fill(.white)
                    .shadow(color: AppColor.softShadow, radius: 12, y: 4)

                VStack(alignment: .leading, spacing: 12) {
                    Text(scene?.characterLine ?? animal?.greeting ?? "")
                        .font(.system(size: 20, weight: .semibold, design: .rounded))
                        .foregroundStyle(AppColor.darkText)
                        .multilineTextAlignment(.leading)
                        .lineSpacing(6)
                }
                .padding(20)
            }
        }
        .padding(.horizontal, 24)
        .opacity(bubbleOpacity)
    }

    private func startAnimation() {
        withAnimation(.spring(duration: 0.7, bounce: 0.4)) {
            animalScale = 1.0
        }

        withAnimation(.easeIn(duration: 0.5).delay(0.6)) {
            bubbleOpacity = 1.0
        }

        withAnimation(.easeInOut(duration: 0.6).repeatForever(autoreverses: true).delay(0.8)) {
            isJumping = true
        }

        if let scene = scene, let animal = animal {
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.8) {
                VoiceService.shared.speak("\(animal.name)だよ！\(scene.characterLine)") {
                    withAnimation(.spring(duration: 0.5)) {
                        showButton = true
                    }
                }
            }
        }

        DispatchQueue.main.asyncAfter(deadline: .now() + 6) {
            withAnimation(.spring(duration: 0.5)) {
                showButton = true
            }
        }
    }
}
