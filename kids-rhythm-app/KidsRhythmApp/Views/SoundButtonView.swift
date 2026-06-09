import SwiftUI

struct SoundButtonView: View {
    let button: SoundButton
    let isActive: Bool
    let onTap: () -> Void

    @State private var pressed = false

    var body: some View {
        Button(action: {
            withAnimation(.spring(response: 0.15, dampingFraction: 0.5)) {
                pressed = true
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.15) {
                withAnimation(.spring(response: 0.2, dampingFraction: 0.7)) {
                    pressed = false
                }
            }
            onTap()
        }) {
            ZStack {
                // Shadow layer
                RoundedRectangle(cornerRadius: 28)
                    .fill(button.color.opacity(0.4))
                    .offset(y: pressed ? 2 : 6)

                // Main button
                RoundedRectangle(cornerRadius: 28)
                    .fill(
                        LinearGradient(
                            colors: [button.color.opacity(0.9), button.color],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 28)
                            .stroke(Color.white.opacity(0.5), lineWidth: 3)
                    )
                    .overlay(
                        // Active glow ring
                        RoundedRectangle(cornerRadius: 28)
                            .stroke(Color.white, lineWidth: isActive ? 5 : 0)
                            .scaleEffect(isActive ? 1.08 : 1.0)
                            .opacity(isActive ? 0.9 : 0)
                            .animation(.easeOut(duration: 0.2), value: isActive)
                    )
                    .offset(y: pressed ? 4 : 0)

                // Emoji
                Text(button.emoji)
                    .font(.system(size: 60))
                    .scaleEffect(pressed || isActive ? 1.2 : 1.0)
                    .offset(y: pressed ? 4 : 0)
                    .animation(.spring(response: 0.15, dampingFraction: 0.5), value: pressed)
                    .animation(.spring(response: 0.15, dampingFraction: 0.5), value: isActive)
            }
        }
        .buttonStyle(PlainButtonStyle())
        .scaleEffect(pressed ? 0.93 : 1.0)
        .animation(.spring(response: 0.15, dampingFraction: 0.5), value: pressed)
    }
}
