import SwiftUI

struct AdventureContainerView: View {
    @Environment(AppState.self) private var appState
    let adventure: Adventure
    @State private var viewModel = AdventureViewModel()

    var body: some View {
        ZStack {
            phaseView
            topBar
        }
        .onAppear {
            viewModel.start(with: adventure)
        }
    }

    @ViewBuilder
    private var phaseView: some View {
        switch viewModel.phase {
        case .locationPrompt:
            LocationPromptView(scene: viewModel.currentScene) {
                viewModel.advanceToCamera()
            }
        case .camera:
            CameraSceneView(
                scene: viewModel.currentScene,
                animal: appState.todaysAnimal
            ) {
                viewModel.advanceToNarration()
            }
        case .narration:
            NarrationView(scene: viewModel.currentScene) {
                viewModel.advanceToCharacterIntro()
            }
        case .characterIntro:
            CharacterIntroView(
                animal: appState.todaysAnimal,
                scene: viewModel.currentScene
            ) {
                viewModel.advanceToQuiz()
            }
        case .quiz:
            if let scene = viewModel.currentScene {
                QuizView(
                    quiz: scene.quiz,
                    animal: appState.todaysAnimal,
                    viewModel: viewModel
                ) {
                    withAnimation {
                        viewModel.advanceToNextScene()
                    }
                }
            }
        case .sceneComplete:
            EmptyView()
        case .adventureComplete:
            AdventureCompleteView(adventure: adventure, animal: appState.todaysAnimal) {
                appState.markTodayCompleted()
                withAnimation {
                    appState.currentScreen = .celebration
                }
            }
        }
    }

    private var topBar: some View {
        VStack {
            HStack {
                Button {
                    VoiceService.shared.stop()
                    withAnimation {
                        appState.currentScreen = .home
                    }
                } label: {
                    Image(systemName: "xmark.circle.fill")
                        .font(.system(size: 32))
                        .foregroundStyle(.white)
                        .shadow(radius: 4)
                }

                Spacer()

                progressBar

                Spacer()

                Button {
                    appState.isVoiceEnabled.toggle()
                    VoiceService.shared.isEnabled = appState.isVoiceEnabled
                    if !appState.isVoiceEnabled {
                        VoiceService.shared.stop()
                    }
                } label: {
                    Image(systemName: appState.isVoiceEnabled ? "speaker.wave.2.fill" : "speaker.slash.fill")
                        .font(.system(size: 28))
                        .foregroundStyle(.white)
                        .shadow(radius: 4)
                }
            }
            .padding(.horizontal, 20)
            .padding(.top, 60)

            Spacer()
        }
        .allowsHitTesting(viewModel.phase != .quiz)
    }

    private var progressBar: some View {
        HStack(spacing: 6) {
            ForEach(0..<adventure.scenes.count, id: \.self) { i in
                RoundedRectangle(cornerRadius: 4)
                    .fill(i < viewModel.currentSceneIndex ? AppColor.yellow :
                          i == viewModel.currentSceneIndex ? Color.white : Color.white.opacity(0.3))
                    .frame(width: i == viewModel.currentSceneIndex ? 32 : 20, height: 8)
                    .animation(.spring(duration: 0.4), value: viewModel.currentSceneIndex)
            }
        }
    }
}
