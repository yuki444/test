import SwiftUI

enum AppColor {
    static let primary = Color(hex: "#FF8C42")
    static let secondary = Color(hex: "#4FB3FF")
    static let yellow = Color(hex: "#FFE234")
    static let green = Color(hex: "#4ECB71")
    static let purple = Color(hex: "#7B68EE")
    static let cream = Color(hex: "#FFF9F0")
    static let darkText = Color(hex: "#2D2D2D")
    static let softShadow = Color.black.opacity(0.12)
}

enum AppFont {
    static func rounded(_ size: CGFloat, weight: Font.Weight = .bold) -> Font {
        .system(size: size, weight: weight, design: .rounded)
    }
    static let title: Font = .system(size: 32, weight: .bold, design: .rounded)
    static let headline: Font = .system(size: 26, weight: .bold, design: .rounded)
    static let body: Font = .system(size: 22, weight: .semibold, design: .rounded)
    static let caption: Font = .system(size: 18, weight: .medium, design: .rounded)
}

extension Color {
    init(hex: String) {
        let hex = hex.trimmingCharacters(in: CharacterSet.alphanumerics.inverted)
        var int: UInt64 = 0
        Scanner(string: hex).scanHexInt64(&int)
        let a, r, g, b: UInt64
        switch hex.count {
        case 3:
            (a, r, g, b) = (255, (int >> 8) * 17, (int >> 4 & 0xF) * 17, (int & 0xF) * 17)
        case 6:
            (a, r, g, b) = (255, int >> 16, int >> 8 & 0xFF, int & 0xFF)
        case 8:
            (a, r, g, b) = (int >> 24, int >> 16 & 0xFF, int >> 8 & 0xFF, int & 0xFF)
        default:
            (a, r, g, b) = (255, 0, 0, 0)
        }
        self.init(
            .sRGB,
            red: Double(r) / 255,
            green: Double(g) / 255,
            blue: Double(b) / 255,
            opacity: Double(a) / 255
        )
    }
}

struct KidsButton: View {
    let title: String
    let emoji: String
    let color: Color
    let action: () -> Void

    var body: some View {
        Button(action: action) {
            HStack(spacing: 12) {
                Text(emoji)
                    .font(.system(size: 32))
                Text(title)
                    .font(AppFont.headline)
                    .foregroundStyle(.white)
            }
            .frame(maxWidth: .infinity)
            .frame(height: 72)
            .background(
                RoundedRectangle(cornerRadius: 24)
                    .fill(color)
                    .shadow(color: color.opacity(0.4), radius: 8, y: 4)
            )
        }
        .buttonStyle(.plain)
    }
}

struct FloatingEmoji: View {
    let emoji: String
    @State private var offset: CGFloat = 0
    @State private var opacity: Double = 0
    let delay: Double

    var body: some View {
        Text(emoji)
            .font(.system(size: 36))
            .offset(y: offset)
            .opacity(opacity)
            .onAppear {
                withAnimation(
                    .easeOut(duration: 1.8)
                    .delay(delay)
                    .repeatForever(autoreverses: false)
                ) {
                    offset = -120
                    opacity = 0
                }
                withAnimation(.easeIn(duration: 0.3).delay(delay)) {
                    opacity = 1
                }
            }
    }
}

struct PulsingCircle: View {
    let color: Color
    @State private var scale: CGFloat = 1.0

    var body: some View {
        Circle()
            .fill(color.opacity(0.3))
            .scaleEffect(scale)
            .onAppear {
                withAnimation(.easeInOut(duration: 1.2).repeatForever(autoreverses: true)) {
                    scale = 1.15
                }
            }
    }
}

struct StarBurst: View {
    @State private var rotation: Double = 0

    var body: some View {
        Image(systemName: "star.fill")
            .font(.system(size: 20))
            .foregroundStyle(AppColor.yellow)
            .rotationEffect(.degrees(rotation))
            .onAppear {
                withAnimation(.linear(duration: 3).repeatForever(autoreverses: false)) {
                    rotation = 360
                }
            }
    }
}
