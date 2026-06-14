import SwiftUI

struct ConversationView: View {
    @EnvironmentObject var gameState: GameStateService
    let npcId: UUID

    @State private var displayedMessages: [Message] = []
    @State private var inputText = ""
    @State private var isLoading = false
    @FocusState private var inputFocused: Bool

    private var npc: NPC? { gameState.npc(by: npcId) }

    var body: some View {
        VStack(spacing: 0) {
            if let npc { PortraitHeader(npc: npc) }

            Divider()

            ScrollViewReader { proxy in
                ScrollView {
                    LazyVStack(alignment: .leading, spacing: 10) {
                        ForEach(displayedMessages) { msg in
                            MessageBubble(message: msg, npcName: npc?.name ?? "")
                                .id(msg.id)
                        }
                        if isLoading { LoadingBubble().id("loading") }
                    }
                    .padding()
                }
                .onChange(of: displayedMessages.count) { _ in
                    withAnimation { proxy.scrollTo(displayedMessages.last?.id, anchor: .bottom) }
                }
                .onChange(of: isLoading) { _ in
                    if isLoading { withAnimation { proxy.scrollTo("loading", anchor: .bottom) } }
                }
            }

            Divider()

            HStack(spacing: 10) {
                TextField("言葉を入れる…", text: $inputText, axis: .vertical)
                    .lineLimit(1...4)
                    .focused($inputFocused)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 9)
                    .background(Color(.systemGray6))
                    .clipShape(RoundedRectangle(cornerRadius: 20))

                Button { sendMessage() } label: {
                    Image(systemName: "arrow.up.circle.fill")
                        .font(.system(size: 34))
                        .foregroundStyle(inputText.trimmingCharacters(in: .whitespaces).isEmpty || isLoading
                            ? Color(.systemGray3) : .accentColor)
                }
                .disabled(inputText.trimmingCharacters(in: .whitespaces).isEmpty || isLoading)
            }
            .padding(.horizontal)
            .padding(.vertical, 10)
        }
        .navigationTitle(npc?.name ?? "")
        .navigationBarTitleDisplayMode(.inline)
        .onAppear { loadHistory() }
    }

    private func loadHistory() {
        guard let npc else { return }
        displayedMessages = npc.conversationHistory

        if displayedMessages.isEmpty {
            let intro = Message(
                id: UUID(),
                role: .npc,
                content: "あなたが近づくと、\(npc.name)が静かに振り返った。",
                timestamp: Date()
            )
            displayedMessages = [intro]
        }
    }

    private func sendMessage() {
        let text = inputText.trimmingCharacters(in: .whitespacesAndNewlines)
        guard !text.isEmpty else { return }
        inputText = ""
        isLoading = true

        let playerMsg = Message(id: UUID(), role: .player, content: text, timestamp: Date())
        displayedMessages.append(playerMsg)

        Task {
            let response = await gameState.sendMessage(to: npcId, message: text)
            let npcMsg = Message(id: UUID(), role: .npc, content: response, timestamp: Date())
            displayedMessages.append(npcMsg)
            isLoading = false
        }
    }
}

struct PortraitHeader: View {
    let npc: NPC

    var body: some View {
        ZStack {
            emotionGradient.ignoresSafeArea(edges: .top)
            VStack(spacing: 6) {
                Text(npc.avatarEmoji)
                    .font(.system(size: 70))
                Text(npc.emotionalState.rawValue)
                    .font(.caption)
                    .foregroundStyle(.white.opacity(0.85))
                    .padding(.horizontal, 12)
                    .padding(.vertical, 4)
                    .background(.black.opacity(0.25))
                    .clipShape(Capsule())
            }
        }
        .frame(height: 180)
    }

    private var emotionGradient: LinearGradient {
        let colors: [Color]
        switch npc.emotionalState {
        case .happy:
            colors = [Color(red: 1.0, green: 0.75, blue: 0.30), Color(red: 1.0, green: 0.92, blue: 0.50)]
        case .worried:
            colors = [Color(red: 0.55, green: 0.60, blue: 0.75), Color(red: 0.75, green: 0.80, blue: 0.90)]
        case .sad:
            colors = [Color(red: 0.30, green: 0.40, blue: 0.70), Color(red: 0.55, green: 0.65, blue: 0.85)]
        case .mysterious:
            colors = [Color(red: 0.35, green: 0.25, blue: 0.55), Color(red: 0.60, green: 0.50, blue: 0.80)]
        case .neutral:
            colors = [Color(red: 0.40, green: 0.65, blue: 0.65), Color(red: 0.65, green: 0.85, blue: 0.80)]
        case .excited:
            colors = [Color(red: 0.85, green: 0.40, blue: 0.50), Color(red: 1.0, green: 0.70, blue: 0.55)]
        }
        return LinearGradient(colors: colors, startPoint: .topLeading, endPoint: .bottomTrailing)
    }
}

struct MessageBubble: View {
    let message: Message
    let npcName: String

    private var isPlayer: Bool { message.role == .player }

    var body: some View {
        HStack {
            if isPlayer { Spacer(minLength: 48) }
            VStack(alignment: isPlayer ? .trailing : .leading, spacing: 3) {
                if !isPlayer {
                    Text(npcName)
                        .font(.caption2)
                        .foregroundStyle(.secondary)
                }
                Text(message.content)
                    .padding(.horizontal, 14)
                    .padding(.vertical, 10)
                    .background(isPlayer ? Color.accentColor : Color(.systemGray5))
                    .foregroundStyle(isPlayer ? .white : .primary)
                    .clipShape(RoundedRectangle(cornerRadius: 18))
            }
            if !isPlayer { Spacer(minLength: 48) }
        }
    }
}

struct LoadingBubble: View {
    @State private var phase: Double = 0

    var body: some View {
        HStack(spacing: 5) {
            ForEach(0..<3, id: \.self) { i in
                Circle()
                    .fill(Color(.systemGray3))
                    .frame(width: 8, height: 8)
                    .scaleEffect(1 + 0.35 * sin(phase + Double(i) * .pi / 1.5))
            }
        }
        .padding(.horizontal, 16)
        .padding(.vertical, 12)
        .background(Color(.systemGray5))
        .clipShape(RoundedRectangle(cornerRadius: 18))
        .onAppear {
            withAnimation(.linear(duration: 1.2).repeatForever(autoreverses: false)) {
                phase = .pi * 2
            }
        }
    }
}
