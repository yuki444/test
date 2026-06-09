import SwiftUI
import AVFoundation

struct CameraView: View {
    @EnvironmentObject var store: TreasureStore
    @Environment(\.dismiss) var dismiss
    let category: TreasureCategory

    @StateObject private var camera = CameraManager()
    @State private var capturedImage: UIImage?
    @State private var showTagSelection = false
    @State private var shutterScale: CGFloat = 1.0

    var body: some View {
        ZStack {
            Color.black.ignoresSafeArea()

            if let image = capturedImage {
                previewConfirmView(image: image)
            } else {
                liveCameraView
            }
        }
        .onAppear { camera.checkPermission() }
        .onDisappear { camera.stopSession() }
        .fullScreenCover(isPresented: $showTagSelection) {
            if let image = capturedImage {
                TagSelectionView(image: image, category: category)
                    .environmentObject(store)
                    .onDisappear { dismiss() }
            }
        }
    }

    private var liveCameraView: some View {
        ZStack {
            CameraPreviewView(session: camera.session)
                .ignoresSafeArea()

            VStack {
                // Top bar
                HStack {
                    Button { dismiss() } label: {
                        Image(systemName: "xmark")
                            .font(.system(size: 20, weight: .bold))
                            .foregroundColor(.white)
                            .padding(14)
                            .background(Color.black.opacity(0.5))
                            .clipShape(Circle())
                    }
                    Spacer()
                    HStack(spacing: 8) {
                        Text(category.emoji)
                            .font(.system(size: 26))
                        Text(category.name)
                            .font(.system(size: 17, weight: .bold, design: .rounded))
                            .foregroundColor(.white)
                    }
                    .padding(.horizontal, 14)
                    .padding(.vertical, 8)
                    .background(category.color.opacity(0.85))
                    .cornerRadius(20)
                    Spacer()
                    Button { camera.flipCamera() } label: {
                        Image(systemName: "arrow.triangle.2.circlepath.camera")
                            .font(.system(size: 20))
                            .foregroundColor(.white)
                            .padding(14)
                            .background(Color.black.opacity(0.5))
                            .clipShape(Circle())
                    }
                }
                .padding()

                Spacer()

                // Shutter
                Button {
                    withAnimation(.spring(response: 0.2, dampingFraction: 0.5)) {
                        shutterScale = 0.85
                    }
                    camera.capturePhoto { image in
                        withAnimation { shutterScale = 1.0 }
                        capturedImage = image
                        camera.stopSession()
                    }
                } label: {
                    ZStack {
                        Circle()
                            .stroke(Color.white, lineWidth: 4)
                            .frame(width: 96, height: 96)
                        Circle()
                            .fill(Color.white)
                            .frame(width: 80, height: 80)
                    }
                    .scaleEffect(shutterScale)
                }
                .padding(.bottom, 52)
            }
        }
    }

    private func previewConfirmView(image: UIImage) -> some View {
        ZStack {
            Image(uiImage: image)
                .resizable()
                .scaledToFill()
                .ignoresSafeArea()
                .overlay(Color.black.opacity(0.25))

            VStack {
                Spacer()
                HStack(spacing: 40) {
                    // Retake
                    VStack(spacing: 6) {
                        Button {
                            capturedImage = nil
                            camera.startSession()
                        } label: {
                            Image(systemName: "arrow.counterclockwise")
                                .font(.system(size: 30))
                                .foregroundColor(.white)
                                .frame(width: 68, height: 68)
                                .background(Color.black.opacity(0.5))
                                .clipShape(Circle())
                        }
                        Text("もういちど")
                            .font(.system(size: 14, weight: .bold, design: .rounded))
                            .foregroundColor(.white)
                    }

                    // Use photo
                    VStack(spacing: 6) {
                        Button { showTagSelection = true } label: {
                            Image(systemName: "checkmark")
                                .font(.system(size: 30, weight: .bold))
                                .foregroundColor(.white)
                                .frame(width: 80, height: 80)
                                .background(Color.green)
                                .clipShape(Circle())
                                .shadow(color: .green.opacity(0.6), radius: 10)
                        }
                        Text("つかう！")
                            .font(.system(size: 14, weight: .bold, design: .rounded))
                            .foregroundColor(.white)
                    }
                }
                .padding(.bottom, 56)
            }
        }
    }
}

struct CameraPreviewView: UIViewRepresentable {
    let session: AVCaptureSession

    func makeUIView(context: Context) -> UIView {
        let view = UIView(frame: UIScreen.main.bounds)
        let preview = AVCaptureVideoPreviewLayer(session: session)
        preview.videoGravity = .resizeAspectFill
        preview.frame = view.bounds
        view.layer.addSublayer(preview)
        return view
    }

    func updateUIView(_ uiView: UIView, context: Context) {}
}
