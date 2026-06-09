import SwiftUI

struct CharacterView: View {
    let theme: Theme
    let beat: Bool
    @State private var bounce = false
    @State private var rotation = 0.0
    @State private var particleOffset: [CGSize] = Array(repeating: .zero, count: 6)
    @State private var particleOpacity: [Double] = Array(repeating: 0, count: 6)
    @State private var particleAngles: [Double] = (0..<6).map { Double($0) * 60 }

    var body: some View {
        ZStack {
            // Particles
            ForEach(0..<6, id: \.self) { i in
                Text(theme.particleEmoji)
                    .font(.system(size: 22))
                    .offset(particleOffset[i])
                    .opacity(particleOpacity[i])
            }

            // Glow circle
            Circle()
                .fill(theme.accentColor.opacity(beat ? 0.35 : 0.15))
                .frame(width: beat ? 145 : 120, height: beat ? 145 : 120)
                .animation(.easeOut(duration: 0.15), value: beat)

            // Character emoji
            Text(theme.characterEmoji)
                .font(.system(size: 80))
                .scaleEffect(bounce ? 1.25 : 1.0)
                .rotation3DEffect(.degrees(rotation), axis: (x: 0, y: 1, z: 0))
                .shadow(color: theme.accentColor, radius: beat ? 18 : 6)
        }
        .frame(width: 160, height: 160)
        .onChange(of: beat) { newVal in
            if newVal {
                triggerBounce()
                triggerParticles()
            }
        }
    }

    private func triggerBounce() {
        withAnimation(.spring(response: 0.18, dampingFraction: 0.4)) {
            bounce = true
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.18) {
            withAnimation(.spring(response: 0.22, dampingFraction: 0.6)) {
                bounce = false
            }
        }
        withAnimation(.easeInOut(duration: 0.25)) {
            rotation = 12
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.25) {
            withAnimation(.easeInOut(duration: 0.2)) {
                rotation = 0
            }
        }
    }

    private func triggerParticles() {
        for i in 0..<6 {
            let angle = particleAngles[i] * .pi / 180
            let distance: CGFloat = CGFloat.random(in: 55...90)
            particleAngles[i] += CGFloat.random(in: 20...60)
            particleOffset[i] = .zero
            particleOpacity[i] = 0

            withAnimation(.easeOut(duration: 0.55)) {
                particleOffset[i] = CGSize(
                    width: cos(angle) * distance,
                    height: sin(angle) * distance - 20
                )
                particleOpacity[i] = 0.9
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.3) {
                withAnimation(.easeIn(duration: 0.25)) {
                    particleOpacity[i] = 0
                }
            }
        }
    }
}
