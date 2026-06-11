import SwiftUI
import Observation

@Observable
class AdventureViewModel {
    var currentSceneIndex: Int = 0
    var phase: AdventurePhase = .locationPrompt
    var quizState: QuizState = .waiting
    var selectedAnswerIndex: Int? = nil
    var attemptCount: Int = 0
    var showHint: Bool = false
    var isVoicePlaying: Bool = false

    enum AdventurePhase: Equatable {
        case locationPrompt
        case camera
        case narration
        case characterIntro
        case quiz
        case sceneComplete
        case adventureComplete
    }

    enum QuizState: Equatable {
        case waiting
        case correct
        case incorrect
    }

    var currentScene: AdventureScene? {
        guard let adventure = currentAdventure,
              currentSceneIndex < adventure.scenes.count else { return nil }
        return adventure.scenes[currentSceneIndex]
    }

    var isLastScene: Bool {
        guard let adventure = currentAdventure else { return true }
        return currentSceneIndex >= adventure.scenes.count - 1
    }

    var progress: Double {
        guard let adventure = currentAdventure, !adventure.scenes.isEmpty else { return 0 }
        let sceneProgress = Double(currentSceneIndex) / Double(adventure.scenes.count)
        let phaseBonus: Double = {
            switch phase {
            case .locationPrompt: return 0
            case .camera: return 0.1
            case .narration: return 0.2
            case .characterIntro: return 0.3
            case .quiz: return 0.4
            case .sceneComplete: return 1.0 / Double(adventure.scenes.count)
            case .adventureComplete: return 1.0 / Double(adventure.scenes.count)
            }
        }()
        return min(sceneProgress + phaseBonus, 1.0)
    }

    private var currentAdventure: Adventure?

    func start(with adventure: Adventure) {
        currentAdventure = adventure
        currentSceneIndex = 0
        phase = .locationPrompt
        quizState = .waiting
        selectedAnswerIndex = nil
        attemptCount = 0
        showHint = false
    }

    func advanceToCamera() {
        withAnimation(.spring(duration: 0.5)) {
            phase = .camera
        }
    }

    func advanceToNarration() {
        withAnimation(.easeInOut(duration: 0.4)) {
            phase = .narration
        }
    }

    func advanceToCharacterIntro() {
        withAnimation(.spring(duration: 0.5)) {
            phase = .characterIntro
        }
    }

    func advanceToQuiz() {
        withAnimation(.spring(duration: 0.5)) {
            phase = .quiz
            quizState = .waiting
            selectedAnswerIndex = nil
            showHint = false
        }
    }

    func submitAnswer(_ answerIndex: Int, correctAnswer: Int) {
        selectedAnswerIndex = answerIndex
        if answerIndex == correctAnswer {
            withAnimation(.spring(duration: 0.6)) {
                quizState = .correct
            }
        } else {
            attemptCount += 1
            withAnimation(.spring(duration: 0.4)) {
                quizState = .incorrect
            }
            if attemptCount >= 2 {
                showHint = true
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 1.5) { [weak self] in
                withAnimation {
                    self?.quizState = .waiting
                    self?.selectedAnswerIndex = nil
                }
            }
        }
    }

    func advanceToNextScene() {
        if isLastScene {
            withAnimation(.easeInOut(duration: 0.5)) {
                phase = .adventureComplete
            }
        } else {
            withAnimation(.easeInOut(duration: 0.4)) {
                currentSceneIndex += 1
                phase = .locationPrompt
                quizState = .waiting
                selectedAnswerIndex = nil
                attemptCount = 0
                showHint = false
            }
        }
    }
}
