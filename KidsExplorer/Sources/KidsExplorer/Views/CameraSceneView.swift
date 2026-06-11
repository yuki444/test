import SwiftUI
import AVFoundation

struct CameraSceneView: View {
    let scene: AdventureScene?
    let animal: AnimalCharacter?
    let onContinue: () -> Void

    @StateObject private var cameraService = CameraService()
    @State private var emojiPositions: [(CGFloat, CGFloat)] = []
    @State private var emojiScales: [CGFloat] = []
    @State private var showButton: Bool = false
    @State private var particleTimer: Timer?

    var body: some View {
        ZStack {
            cameraOrPlaceholder
            overlayEffects
            uiOverlay
        }
        .onAppear {
            cameraService.startSession()
            setupEmojiPositions()
            DispatchQueue.main.asyncAfter(deadline: .now() + 3.0) {
                withAnimation(.spring(duration: 0.6)) {
                    showButton = true
                }
            }
            VoiceService.shared.speak("カメラを むけてみよう！まほうのせかいが あらわれるよ！")
        }
        .onDisappear {
            cameraService.stopSession()
            particleTimer?.invalidate()
        }
    }

    private var cameraOrPlaceholder: some View {
        Group {
            if cameraService.isAuthorized {
                CameraPreviewView(session: cameraService.session)
                    .ignoresSafeArea()
            } else {
                LinearGradient(
                    colors: [Color(hex: "#1a1a4e"), Color(hex: "#2d1b69")],
                    startPoint: .top,
                    endPoint: .bottom
                )
                .ignoresSafeArea()
                .overlay(
                    VStack(spacing: 16) {
                        Text("📷")
                            .font(.system(size: 80))
                        Text("カメラを つかうよ！\nゆるしてね！")
                            .font(AppFont.body)
                            .foregroundStyle(.white)
                            .multilineTextAlignment(.center)
                        Button("カメラを ゆるす") {
                            cameraService.checkAuthorization()
                        }
                        .font(AppFont.body)
                        .padding(.horizontal, 24)
                        .padding(.vertical, 12)
                        .background(AppColor.primary)
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                    }
                )
            }
        }
    }

    private var overlayEffects: some View {
        GeometryReader { geo in
            let emojis = scene?.overlayEmojis ?? ["✨", "🌟", "⭐️"]
            ForEach(0..<min(emojiPositions.count, emojis.count), id: \.self) { i in
                Text(emojis[i % emojis.count])
                    .font(.system(size: 44))
                    .scaleEffect(emojiScales.indices.contains(i) ? emojiScales[i] : 1.0)
                    .position(
                        x: emojiPositions.indices.contains(i) ? emojiPositions[i].0 * geo.size.width : geo.size.width / 2,
                        y: emojiPositions.indices.contains(i) ? emojiPositions[i].1 * geo.size.height : geo.size.height / 2
                    )
                    .shadow(color: .white.opacity(0.8), radius: 8)
            }
        }
    }

    private var uiOverlay: some View {
        VStack {
            Spacer()

            if showButton {
                VStack(spacing: 16) {
                    if let animal = animal {
                        HStack(spacing: 12) {
                            Text(animal.emoji)
                                .font(.system(size: 44))
                            Text("まほうのせかいが みえるかな？")
                                .font(AppFont.body)
                                .foregroundStyle(.white)
                                .shadow(color: .black.opacity(0.5), radius: 4)
                        }
                        .padding(16)
                        .background(.black.opacity(0.4))
                        .clipShape(RoundedRectangle(cornerRadius: 20))
                        .padding(.horizontal, 20)
                    }

                    KidsButton(
                        title: "つぎへ すすむ！",
                        emoji: "➡️",
                        color: AppColor.primary
                    ) {
                        onContinue()
                    }
                    .padding(.horizontal, 24)
                    .padding(.bottom, 40)
                }
                .transition(.move(edge: .bottom).combined(with: .opacity))
            } else {
                HStack(spacing: 8) {
                    ForEach(0..<3) { i in
                        Circle()
                            .fill(.white.opacity(0.8))
                            .frame(width: 10, height: 10)
                            .scaleEffect(showButton ? 1 : 0.5)
                            .animation(.easeInOut(duration: 0.5).repeatForever().delay(Double(i) * 0.15), value: showButton)
                    }
                }
                .padding(.bottom, 60)
            }
        }
    }

    private func setupEmojiPositions() {
        let count = scene?.overlayEmojis.count ?? 5
        emojiPositions = (0..<count).map { _ in
            (CGFloat.random(in: 0.1...0.9), CGFloat.random(in: 0.1...0.85))
        }
        emojiScales = Array(repeating: 1.0, count: count)

        for i in 0..<count {
            withAnimation(.easeInOut(duration: Double.random(in: 1.5...2.5)).repeatForever(autoreverses: true).delay(Double(i) * 0.3)) {
                emojiScales[i] = CGFloat.random(in: 0.8...1.3)
            }
        }
    }
}

struct CameraPreviewView: UIViewRepresentable {
    let session: AVCaptureSession

    func makeUIView(context: Context) -> UIView {
        let view = UIView()
        let previewLayer = AVCaptureVideoPreviewLayer(session: session)
        previewLayer.videoGravity = .resizeAspectFill
        previewLayer.frame = UIScreen.main.bounds
        view.layer.addSublayer(previewLayer)
        return view
    }

    func updateUIView(_ uiView: UIView, context: Context) {
        if let previewLayer = uiView.layer.sublayers?.first as? AVCaptureVideoPreviewLayer {
            previewLayer.frame = uiView.bounds
        }
    }
}
