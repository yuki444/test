import SwiftUI

struct LocationPromptView: View {
    let scene: AdventureScene?
    let onReady: () -> Void

    @State private var arrowBounce: CGFloat = 0
    @State private var showContent: Bool = false
    @State private var mapScale: CGFloat = 0.7

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color(hex: "#FFF3E0"), Color(hex: "#E3F2FD")],
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()

            VStack(spacing: 32) {
                Spacer()

                VStack(spacing: 20) {
                    ZStack {
                        Circle()
                            .fill(AppColor.yellow.opacity(0.3))
                            .frame(width: 160, height: 160)

                        Text("🗺️")
                            .font(.system(size: 90))
                            .scaleEffect(mapScale)
                    }

                    Text("つぎの ばしょへ！")
                        .font(.system(size: 28, weight: .black, design: .rounded))
                        .foregroundStyle(AppColor.darkText)

                    if let scene = scene {
                        Text(scene.locationPrompt)
                            .font(AppFont.headline)
                            .foregroundStyle(AppColor.primary)
                            .multilineTextAlignment(.center)

                        HStack(spacing: 8) {
                            Text("💡")
                            Text(scene.locationHint)
                                .font(AppFont.caption)
                                .foregroundStyle(.secondary)
                        }
                        .padding(.horizontal, 24)
                        .multilineTextAlignment(.center)
                    }
                }

                Text("↓")
                    .font(.system(size: 48, weight: .black))
                    .foregroundStyle(AppColor.primary)
                    .offset(y: arrowBounce)

                KidsButton(
                    title: "ついたよ！カメラを ひらく",
                    emoji: "📷",
                    color: AppColor.secondary
                ) {
                    onReady()
                }
                .padding(.horizontal, 24)

                Spacer()
            }
            .opacity(showContent ? 1 : 0)
            .scaleEffect(showContent ? 1 : 0.9)
        }
        .onAppear {
            withAnimation(.spring(duration: 0.6)) {
                showContent = true
                mapScale = 1.0
            }
            withAnimation(.easeInOut(duration: 0.8).repeatForever(autoreverses: true)) {
                arrowBounce = 10
            }
            if let scene = scene {
                DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                    VoiceService.shared.speak(scene.locationPrompt)
                }
            }
        }
    }
}
