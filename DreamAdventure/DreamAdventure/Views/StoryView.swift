import SwiftUI

struct StoryView: View {
    @StateObject private var viewModel: StoryViewModel
    let onBack: () -> Void

    init(dreamType: DreamType, onBack: @escaping () -> Void) {
        _viewModel = StateObject(wrappedValue: StoryViewModel(dreamType: dreamType))
        self.onBack = onBack
    }

    var body: some View {
        ZStack {
            // 背景
            BackgroundSceneView(
                backgroundType: viewModel.currentNode?.background ?? .nightSky,
                dreamType: viewModel.dreamType
            )

            VStack(spacing: 0) {
                // 上部ナビゲーション
                HStack {
                    Button(action: onBack) {
                        HStack(spacing: 6) {
                            Image(systemName: "chevron.left")
                            Text("もどる")
                        }
                        .font(.system(size: 16, weight: .semibold, design: .rounded))
                        .foregroundColor(.white)
                        .padding(.horizontal, 14)
                        .padding(.vertical, 8)
                        .background(Color.black.opacity(0.3))
                        .clipShape(Capsule())
                    }
                    Spacer()

                    // シーンインジケーター
                    if let node = viewModel.currentNode {
                        SceneIndicator(scene: node.scene)
                    }
                }
                .padding(.horizontal, 20)
                .padding(.top, 50)

                Spacer()

                // キャラクターエリア
                CharacterAreaView(viewModel: viewModel)

                // ナレーションカード
                NarrationCard(viewModel: viewModel)
                    .padding(.horizontal, 16)
                    .padding(.bottom, 30)
            }

            // 選択肢オーバーレイ
            if viewModel.showChoices, let node = viewModel.currentNode {
                ChoicesOverlay(choices: node.choices) { choice in
                    viewModel.selectChoice(choice)
                }
            }

            // 選択フィードバック
            if let feedback = viewModel.choiceFeedback {
                FeedbackBanner(text: feedback)
            }

            // お祝いエフェクト
            if viewModel.isCelebrating {
                CelebrationView()
                    .allowsHitTesting(false)
            }

            // ストーリー完了画面
            if viewModel.isStoryComplete {
                StoryCompleteView(dreamType: viewModel.dreamType, onBack: onBack)
                    .transition(.opacity)
            }
        }
        .ignoresSafeArea()
        .onTapGesture {
            if !viewModel.showChoices && !viewModel.isStoryComplete {
                viewModel.handleTap()
            }
        }
        .animation(.easeInOut(duration: 0.4), value: viewModel.currentNode?.id)
    }
}

// MARK: - Background Scene
struct BackgroundSceneView: View {
    let backgroundType: BackgroundType
    let dreamType: DreamType

    var backgroundEmoji: String {
        switch backgroundType {
        case .nightSky:    return "🌙"
        case .spaceship:   return "🚀"
        case .moon:        return "🌕"
        case .stars:       return "⭐"
        case .cosmos:      return "🌌"
        case .kitchen:     return "🍳"
        case .forest:      return "🌲"
        case .bakery:      return "🥐"
        case .celebration: return "🎉"
        case .beach:       return "🏖️"
        case .ocean:       return "🌊"
        case .underwater:  return "🐠"
        case .treasure:    return "💎"
        case .storm:       return "⛈️"
        case .home:        return "🏠"
        case .meadow:      return "🌸"
        }
    }

    var gradientColors: [Color] {
        switch backgroundType {
        case .nightSky, .stars, .cosmos:
            return [Color(red: 0.02, green: 0.02, blue: 0.15), Color(red: 0.1, green: 0.0, blue: 0.25)]
        case .spaceship, .moon:
            return [Color(red: 0.1, green: 0.05, blue: 0.3), Color(red: 0.0, green: 0.0, blue: 0.1)]
        case .kitchen, .bakery:
            return [Color(red: 1.0, green: 0.95, blue: 0.85), Color(red: 0.98, green: 0.85, blue: 0.7)]
        case .forest:
            return [Color(red: 0.1, green: 0.4, blue: 0.1), Color(red: 0.2, green: 0.6, blue: 0.2)]
        case .celebration:
            return [Color(red: 1.0, green: 0.8, blue: 0.2), Color(red: 1.0, green: 0.5, blue: 0.3)]
        case .beach:
            return [Color(red: 0.5, green: 0.8, blue: 1.0), Color(red: 0.95, green: 0.85, blue: 0.6)]
        case .ocean, .underwater:
            return [Color(red: 0.0, green: 0.3, blue: 0.7), Color(red: 0.0, green: 0.5, blue: 0.8)]
        case .treasure:
            return [Color(red: 0.0, green: 0.2, blue: 0.5), Color(red: 0.3, green: 0.1, blue: 0.5)]
        case .storm:
            return [Color(red: 0.2, green: 0.2, blue: 0.3), Color(red: 0.1, green: 0.1, blue: 0.2)]
        default:
            return [Color(red: 0.4, green: 0.7, blue: 0.9), Color(red: 0.6, green: 0.9, blue: 0.6)]
        }
    }

    var body: some View {
        ZStack {
            LinearGradient(colors: gradientColors, startPoint: .top, endPoint: .bottom)
                .ignoresSafeArea()

            // 大きな背景絵文字
            Text(backgroundEmoji)
                .font(.system(size: 180))
                .opacity(0.15)
                .blur(radius: 2)
                .offset(x: 80, y: -100)
        }
    }
}

// MARK: - Character Area
struct CharacterAreaView: View {
    @ObservedObject var viewModel: StoryViewModel

    var body: some View {
        HStack {
            Spacer()
            Button(action: { viewModel.handleCharacterTap() }) {
                VStack(spacing: 6) {
                    Text(viewModel.animal.emoji)
                        .font(.system(size: 90))
                        .scaleEffect(viewModel.characterBounce ? 1.15 : 1.0)
                        .shadow(color: .black.opacity(0.2), radius: 8)

                    Text(viewModel.animal.name)
                        .font(.system(size: 14, weight: .bold, design: .rounded))
                        .foregroundColor(.white)
                        .padding(.horizontal, 12)
                        .padding(.vertical, 4)
                        .background(Color.black.opacity(0.3))
                        .clipShape(Capsule())
                }
            }
            .buttonStyle(.plain)
            .animation(.spring(response: 0.3, dampingFraction: 0.5), value: viewModel.characterBounce)
            .padding(.trailing, 30)
        }
    }
}

// MARK: - Narration Card
struct NarrationCard: View {
    @ObservedObject var viewModel: StoryViewModel

    var body: some View {
        VStack(spacing: 16) {
            // ナレーションテキスト
            if let _ = viewModel.currentNode {
                Text(viewModel.currentNarration)
                    .font(.system(size: 22, weight: .medium, design: .rounded))
                    .foregroundColor(.white)
                    .multilineTextAlignment(.center)
                    .lineSpacing(6)
                    .padding(.horizontal, 8)
                    .transition(.opacity.combined(with: .scale(scale: 0.95)))
                    .id(viewModel.currentNarration)
            }

            // キャラクターセリフ
            if viewModel.showCharacterDialogue, let dialogue = viewModel.currentNode?.characterDialogue {
                HStack(alignment: .top, spacing: 10) {
                    Text(viewModel.animal.emoji)
                        .font(.system(size: 28))
                    Text(dialogue)
                        .font(.system(size: 18, weight: .regular, design: .rounded))
                        .foregroundColor(Color(red: 1.0, green: 0.95, blue: 0.7))
                        .multilineTextAlignment(.leading)
                        .lineSpacing(4)
                }
                .padding(.horizontal, 8)
                .transition(.move(edge: .bottom).combined(with: .opacity))
            }

            // タップヒント
            if !viewModel.showChoices && !viewModel.isStoryComplete {
                HStack(spacing: 6) {
                    Image(systemName: "hand.tap.fill")
                    Text("タップして つづける")
                }
                .font(.system(size: 13, design: .rounded))
                .foregroundColor(.white.opacity(0.6))
                .padding(.top, 4)
            }
        }
        .padding(.horizontal, 20)
        .padding(.vertical, 24)
        .background(
            RoundedRectangle(cornerRadius: 28)
                .fill(Color.black.opacity(0.45))
                .overlay(
                    RoundedRectangle(cornerRadius: 28)
                        .stroke(Color.white.opacity(0.2), lineWidth: 1)
                )
        )
        .animation(.spring(response: 0.4), value: viewModel.showCharacterDialogue)
    }
}

// MARK: - Choices Overlay
struct ChoicesOverlay: View {
    let choices: [StoryChoice]
    let onSelect: (StoryChoice) -> Void

    var body: some View {
        ZStack {
            Color.black.opacity(0.5)
                .ignoresSafeArea()

            VStack(spacing: 16) {
                Text("どうする？")
                    .font(.system(size: 24, weight: .bold, design: .rounded))
                    .foregroundColor(.white)

                ForEach(choices) { choice in
                    Button(action: { onSelect(choice) }) {
                        HStack(spacing: 14) {
                            Text(choice.emoji)
                                .font(.system(size: 36))
                            Text(choice.text)
                                .font(.system(size: 20, weight: .semibold, design: .rounded))
                                .foregroundColor(.white)
                            Spacer()
                        }
                        .padding(.horizontal, 24)
                        .padding(.vertical, 18)
                        .background(
                            RoundedRectangle(cornerRadius: 20)
                                .fill(Color.white.opacity(0.2))
                                .overlay(
                                    RoundedRectangle(cornerRadius: 20)
                                        .stroke(Color.white.opacity(0.4), lineWidth: 1.5)
                                )
                        )
                    }
                    .buttonStyle(.plain)
                }
            }
            .padding(.horizontal, 28)
        }
    }
}

// MARK: - Feedback Banner
struct FeedbackBanner: View {
    let text: String

    var body: some View {
        VStack {
            Spacer()
            Text(text)
                .font(.system(size: 16, weight: .semibold, design: .rounded))
                .foregroundColor(.white)
                .multilineTextAlignment(.center)
                .padding(.horizontal, 20)
                .padding(.vertical, 12)
                .background(
                    Capsule()
                        .fill(Color(red: 0.4, green: 0.2, blue: 0.8).opacity(0.9))
                )
                .padding(.bottom, 220)
        }
        .transition(.move(edge: .bottom).combined(with: .opacity))
    }
}

// MARK: - Scene Indicator
struct SceneIndicator: View {
    let scene: SceneType

    var label: (String, Color) {
        switch scene {
        case .opening:      return ("はじまり", .blue)
        case .challenge:    return ("ちょうせん", .orange)
        case .cooperation:  return ("きょうりょく", .green)
        case .achievement:  return ("たっせい！", .yellow)
        case .ending:       return ("おわり", .purple)
        }
    }

    var body: some View {
        let (text, color) = label
        Text(text)
            .font(.system(size: 12, weight: .bold, design: .rounded))
            .foregroundColor(.white)
            .padding(.horizontal, 12)
            .padding(.vertical, 5)
            .background(color.opacity(0.7))
            .clipShape(Capsule())
    }
}

// MARK: - Celebration
struct CelebrationView: View {
    @State private var particles: [CelebrationParticle] = CelebrationParticle.generate(count: 30)
    @State private var animate: Bool = false

    var body: some View {
        ForEach(particles) { p in
            Text(p.emoji)
                .font(.system(size: p.size))
                .position(
                    x: p.x,
                    y: animate ? p.endY : p.startY
                )
                .opacity(animate ? 0 : 1)
        }
        .onAppear {
            withAnimation(.easeOut(duration: 2.5)) {
                animate = true
            }
        }
    }
}

struct CelebrationParticle: Identifiable {
    let id = UUID()
    let emoji: String
    let x: CGFloat
    let startY: CGFloat
    let endY: CGFloat
    let size: CGFloat

    static func generate(count: Int) -> [CelebrationParticle] {
        let emojis = ["⭐", "✨", "🌟", "💫", "🎉", "🎊", "🌈", "💖", "🎵"]
        return (0..<count).map { _ in
            CelebrationParticle(
                emoji: emojis.randomElement()!,
                x: CGFloat.random(in: 20...380),
                startY: CGFloat.random(in: 300...700),
                endY: CGFloat.random(in: 0...200),
                size: CGFloat.random(in: 20...40)
            )
        }
    }
}

// MARK: - Story Complete
struct StoryCompleteView: View {
    let dreamType: DreamType
    let onBack: () -> Void

    @State private var visible: Bool = false

    var body: some View {
        ZStack {
            LinearGradient(
                colors: dreamType.gradientColors,
                startPoint: .topLeading,
                endPoint: .bottomTrailing
            )
            .ignoresSafeArea()
            .opacity(0.9)

            VStack(spacing: 28) {
                Text(dreamType.emoji)
                    .font(.system(size: 100))
                    .scaleEffect(visible ? 1.0 : 0.3)

                VStack(spacing: 12) {
                    Text("おめでとう！")
                        .font(.system(size: 36, weight: .bold, design: .rounded))
                        .foregroundColor(.white)

                    Text("「\(dreamType.title)」の\nぼうけん を クリア！")
                        .font(.system(size: 22, weight: .medium, design: .rounded))
                        .foregroundColor(.white.opacity(0.9))
                        .multilineTextAlignment(.center)
                        .lineSpacing(6)
                }
                .opacity(visible ? 1.0 : 0)

                VStack(spacing: 12) {
                    Text(dreamType.animal.emoji + " " + dreamType.animal.name)
                        .font(.system(size: 18))
                    Text("「ありがとう！ また あそぼうね！」")
                        .font(.system(size: 16, weight: .medium, design: .rounded))
                        .foregroundColor(.white.opacity(0.85))
                        .italic()
                }
                .opacity(visible ? 1.0 : 0)

                Button(action: onBack) {
                    HStack(spacing: 8) {
                        Image(systemName: "house.fill")
                        Text("ほかの ゆめも みる")
                    }
                    .font(.system(size: 20, weight: .bold, design: .rounded))
                    .foregroundColor(dreamType.color)
                    .padding(.horizontal, 30)
                    .padding(.vertical, 16)
                    .background(Color.white)
                    .clipShape(Capsule())
                    .shadow(radius: 10)
                }
                .opacity(visible ? 1.0 : 0)
            }
            .padding(30)
        }
        .onAppear {
            withAnimation(.spring(response: 0.7, dampingFraction: 0.7).delay(0.2)) {
                visible = true
            }
        }
    }
}
