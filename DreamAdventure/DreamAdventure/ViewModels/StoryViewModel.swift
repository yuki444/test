import SwiftUI
import AVFoundation

@MainActor
class StoryViewModel: ObservableObject {
    @Published var currentNode: StoryNode?
    @Published var narrationIndex: Int = 0
    @Published var showCharacterDialogue: Bool = false
    @Published var showChoices: Bool = false
    @Published var choiceFeedback: String? = nil
    @Published var isCelebrating: Bool = false
    @Published var isStoryComplete: Bool = false
    @Published var characterBounce: Bool = false

    private var story: Story
    let dreamType: DreamType
    private let synthesizer = AVSpeechSynthesizer()

    init(dreamType: DreamType) {
        self.dreamType = dreamType
        self.story = StoryData.story(for: dreamType)
        loadNode(id: story.startNodeId)
    }

    var animal: AnimalCharacter { dreamType.animal }

    var currentNarration: String {
        guard let node = currentNode, narrationIndex < node.narration.count else { return "" }
        return node.narration[narrationIndex]
    }

    var hasMoreNarration: Bool {
        guard let node = currentNode else { return false }
        return narrationIndex < node.narration.count - 1
    }

    func loadNode(id: String) {
        guard let node = story.nodes[id] else { return }
        currentNode = node
        narrationIndex = 0
        showCharacterDialogue = false
        showChoices = false
        choiceFeedback = nil
        isCelebrating = node.scene == .achievement || node.scene == .ending

        speakNarration(node.narration[0])

        if node.interaction == .celebration {
            triggerCelebration()
        }

        // キャラクター登場アニメーション
        Task {
            try? await Task.sleep(nanoseconds: 500_000_000)
            withAnimation(.spring(response: 0.4, dampingFraction: 0.6)) {
                characterBounce = true
            }
            try? await Task.sleep(nanoseconds: 300_000_000)
            characterBounce = false
        }
    }

    func advanceNarration() {
        guard let node = currentNode else { return }

        if hasMoreNarration {
            narrationIndex += 1
            speakNarration(node.narration[narrationIndex])
        } else {
            // ナレーション終了後の処理
            if node.characterDialogue != nil {
                withAnimation(.spring()) {
                    showCharacterDialogue = true
                }
                if let dialogue = node.characterDialogue {
                    speakNarration(dialogue)
                }
            }
            if node.interaction == .choice {
                Task {
                    try? await Task.sleep(nanoseconds: 800_000_000)
                    withAnimation(.spring()) {
                        showChoices = true
                    }
                }
            }
        }
    }

    func handleTap() {
        guard let node = currentNode else { return }
        switch node.interaction {
        case .tapToContinue, .tapCharacter:
            if hasMoreNarration || (!showCharacterDialogue && node.characterDialogue != nil) {
                advanceNarration()
            } else {
                goToNext()
            }
        case .celebration:
            triggerCelebration()
            if let nextId = node.nextNodeId {
                Task {
                    try? await Task.sleep(nanoseconds: 1_500_000_000)
                    loadNode(id: nextId)
                }
            } else {
                Task {
                    try? await Task.sleep(nanoseconds: 2_000_000_000)
                    isStoryComplete = true
                }
            }
        default:
            advanceNarration()
        }
    }

    func handleCharacterTap() {
        withAnimation(.spring(response: 0.3, dampingFraction: 0.5)) {
            characterBounce = true
        }
        Task {
            try? await Task.sleep(nanoseconds: 400_000_000)
            characterBounce = false
        }

        if let node = currentNode, node.interaction == .tapCharacter {
            goToNext()
        } else {
            advanceNarration()
        }
    }

    func selectChoice(_ choice: StoryChoice) {
        choiceFeedback = choice.feedback
        withAnimation(.spring()) {
            showChoices = false
        }
        speakNarration(choice.feedback)
        Task {
            try? await Task.sleep(nanoseconds: 1_800_000_000)
            loadNode(id: choice.nextNodeId)
        }
    }

    private func goToNext() {
        guard let node = currentNode else { return }
        if let nextId = node.nextNodeId {
            loadNode(id: nextId)
        } else if node.interaction != .celebration {
            isStoryComplete = true
        }
    }

    func triggerCelebration() {
        isCelebrating = true
        Task {
            try? await Task.sleep(nanoseconds: 3_000_000_000)
            isCelebrating = false
        }
    }

    private func speakNarration(_ text: String) {
        synthesizer.stopSpeaking(at: .immediate)
        let utterance = AVSpeechUtterance(string: text)
        utterance.voice = AVSpeechSynthesisVoice(language: "ja-JP")
        utterance.rate = 0.42
        utterance.pitchMultiplier = 1.1
        synthesizer.speak(utterance)
    }
}
