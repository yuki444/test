import SwiftUI

struct HomeView: View {
    let onSelectTheme: (Theme) -> Void
    let onGallery: () -> Void

    @State private var animateLogo = false

    var body: some View {
        ZStack {
            // Background
            LinearGradient(
                colors: [Color(hex: "#1a0533"), Color(hex: "#3d1a6e"), Color(hex: "#6b1fa8")],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            // Twinkling stars
            StarField()

            VStack(spacing: 0) {
                // Header
                header
                    .padding(.top, 16)
                    .padding(.bottom, 20)

                // Theme grid – scrollable
                ScrollView(showsIndicators: false) {
                    LazyVGrid(
                        columns: [GridItem(.flexible(), spacing: 16), GridItem(.flexible(), spacing: 16)],
                        spacing: 16
                    ) {
                        ForEach(Theme.all) { theme in
                            ThemeCardView(theme: theme) {
                                onSelectTheme(theme)
                            }
                        }
                    }
                    .padding(.horizontal, 20)
                    .padding(.bottom, 24)
                }

                // Gallery button
                galleryButton
                    .padding(.bottom, 24)
            }
        }
    }

    private var header: some View {
        VStack(spacing: 8) {
            HStack(spacing: 0) {
                Text("🎵")
                    .font(.system(size: 44))
                    .rotationEffect(.degrees(animateLogo ? -15 : 15))
                    .animation(.easeInOut(duration: 0.9).repeatForever(autoreverses: true), value: animateLogo)
                    .onAppear { animateLogo = true }

                Text("リズムあそび")
                    .font(.system(size: 32, weight: .black, design: .rounded))
                    .foregroundColor(.white)
                    .shadow(color: Color(hex: "#C850C0"), radius: 8)

                Text("🎶")
                    .font(.system(size: 44))
                    .rotationEffect(.degrees(animateLogo ? 15 : -15))
                    .animation(.easeInOut(duration: 0.9).repeatForever(autoreverses: true).delay(0.15), value: animateLogo)
            }

            Text("すきなせかいをえらんでね")
                .font(.system(size: 18, weight: .semibold, design: .rounded))
                .foregroundColor(.white.opacity(0.8))
        }
    }

    private var galleryButton: some View {
        Button(action: onGallery) {
            HStack(spacing: 12) {
                Text("🖼️")
                    .font(.system(size: 28))
                Text("ギャラリー")
                    .font(.system(size: 22, weight: .black, design: .rounded))
                    .foregroundColor(.white)
                Text("🎵")
                    .font(.system(size: 28))
            }
            .padding(.horizontal, 36)
            .padding(.vertical, 14)
            .background(
                Capsule()
                    .fill(Color.white.opacity(0.15))
                    .overlay(Capsule().stroke(Color.white.opacity(0.3), lineWidth: 2))
            )
        }
        .buttonStyle(PressableButtonStyle())
    }
}

struct ThemeCardView: View {
    let theme: Theme
    let onTap: () -> Void

    @State private var bouncing = false

    var body: some View {
        Button(action: onTap) {
            ZStack {
                // Card background
                RoundedRectangle(cornerRadius: 24)
                    .fill(
                        LinearGradient(
                            colors: [theme.gradientTop, theme.gradientBottom],
                            startPoint: .topLeading,
                            endPoint: .bottomTrailing
                        )
                    )
                    .overlay(
                        RoundedRectangle(cornerRadius: 24)
                            .stroke(Color.white.opacity(0.35), lineWidth: 2.5)
                    )
                    .shadow(color: theme.gradientBottom.opacity(0.5), radius: 10, y: 5)

                VStack(spacing: 8) {
                    Text(theme.emoji)
                        .font(.system(size: 52))
                        .scaleEffect(bouncing ? 1.18 : 1.0)
                        .animation(.spring(response: 0.35, dampingFraction: 0.45).repeatForever(autoreverses: true).delay(Double(theme.id) * 0.12), value: bouncing)

                    Text(theme.nameJP)
                        .font(.system(size: 20, weight: .black, design: .rounded))
                        .foregroundColor(.white)
                        .shadow(radius: 3)

                    // Mini button row
                    HStack(spacing: 4) {
                        ForEach(theme.buttons) { btn in
                            Text(btn.emoji)
                                .font(.system(size: 16))
                        }
                    }
                }
                .padding(.vertical, 18)
            }
            .aspectRatio(1.0, contentMode: .fit)
        }
        .buttonStyle(PressableButtonStyle())
        .onAppear { bouncing = true }
    }
}

// Simple twinkling star field
struct StarField: View {
    @State private var stars: [StarItem] = StarField.generateStars(count: 60)

    static func generateStars(count: Int) -> [StarItem] {
        (0..<count).map { _ in
            StarItem(
                x: CGFloat.random(in: 0...1),
                y: CGFloat.random(in: 0...1),
                size: CGFloat.random(in: 1.5...4),
                opacity: Double.random(in: 0.2...0.8),
                delay: Double.random(in: 0...2)
            )
        }
    }

    var body: some View {
        GeometryReader { geo in
            ForEach(stars) { star in
                TwinklingDot(size: star.size, opacity: star.opacity, delay: star.delay)
                    .position(x: star.x * geo.size.width, y: star.y * geo.size.height)
            }
        }
        .ignoresSafeArea()
        .allowsHitTesting(false)
    }
}

struct TwinklingDot: View {
    let size: CGFloat
    let opacity: Double
    let delay: Double
    @State private var visible = true

    var body: some View {
        Circle()
            .fill(Color.white)
            .frame(width: size, height: size)
            .opacity(visible ? opacity : opacity * 0.2)
            .onAppear {
                withAnimation(.easeInOut(duration: Double.random(in: 1.2...2.5)).repeatForever(autoreverses: true).delay(delay)) {
                    visible = false
                }
            }
    }
}

struct StarItem: Identifiable {
    let id = UUID()
    let x, y, size: CGFloat
    let opacity: Double
    let delay: Double
}
