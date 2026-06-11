import SwiftUI

struct QuizView: View {
    let quiz: Quiz
    let animal: AnimalCharacter?
    let viewModel: AdventureViewModel
    let onComplete: () -> Void

    @State private var buttonScales: [CGFloat]
    @State private var showSuccess: Bool = false
    @State private var shakingIndex: Int? = nil
    @State private var successScale: CGFloat = 0.5

    init(quiz: Quiz, animal: AnimalCharacter?, viewModel: AdventureViewModel, onComplete: @escaping () -> Void) {
        self.quiz = quiz
        self.animal = animal
        self.viewModel = viewModel
        self.onComplete = onComplete
        _buttonScales = State(initialValue: Array(repeating: 1.0, count: quiz.options.count))
    }

    var body: some View {
        ZStack {
            backgroundView

            if showSuccess {
                successOverlay
            } else {
                quizContent
            }
        }
        .onAppear {
            VoiceService.shared.speak(quiz.question)
        }
    }

    private var backgroundView: some View {
        LinearGradient(
            colors: [Color(hex: "#E8EAF6"), Color(hex: "#FFF8E1")],
            startPoint: .top,
            endPoint: .bottom
        )
        .ignoresSafeArea()
    }

    private var quizContent: some View {
        ScrollView(showsIndicators: false) {
            VStack(spacing: 24) {
                animalHeader

                questionCard

                if viewModel.showHint {
                    hintCard
                        .transition(.move(edge: .top).combined(with: .opacity))
                }

                optionsGrid

                Spacer(minLength: 40)
            }
            .padding(.horizontal, 20)
            .padding(.top, 100)
            .padding(.bottom, 40)
        }
    }

    private var animalHeader: some View {
        HStack(spacing: 12) {
            Text(animal?.emoji ?? "🐻")
                .font(.system(size: 52))

            VStack(alignment: .leading, spacing: 4) {
                Text("クイズ！")
                    .font(.system(size: 22, weight: .black, design: .rounded))
                    .foregroundStyle(AppColor.primary)
                Text(viewModel.quizState == .incorrect ?
                     (animal?.wrongPhrase ?? "もういちど！") :
                     (animal?.cheerPhrase ?? "がんばれ！"))
                    .font(AppFont.caption)
                    .foregroundStyle(.secondary)
            }
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: 20)
                .fill(.white)
                .shadow(color: AppColor.softShadow, radius: 8, y: 2)
        )
    }

    private var questionCard: some View {
        VStack(spacing: 16) {
            if quiz.type == .katakana, let target = quiz.visualItems.first {
                Text(target)
                    .font(.system(size: 100, weight: .black, design: .rounded))
                    .foregroundStyle(AppColor.purple)
                    .shadow(color: AppColor.purple.opacity(0.2), radius: 8, y: 4)
            } else {
                FlowLayout(spacing: 8) {
                    ForEach(quiz.visualItems, id: \.self) { item in
                        Text(item)
                            .font(.system(size: 44))
                    }
                }
                .frame(maxWidth: .infinity)
            }

            Text(quiz.question)
                .font(.system(size: 22, weight: .bold, design: .rounded))
                .foregroundStyle(AppColor.darkText)
                .multilineTextAlignment(.center)
        }
        .padding(24)
        .frame(maxWidth: .infinity)
        .background(
            RoundedRectangle(cornerRadius: 24)
                .fill(.white)
                .shadow(color: AppColor.softShadow, radius: 12, y: 4)
        )
    }

    private var hintCard: some View {
        HStack(spacing: 12) {
            Text("💡")
                .font(.system(size: 28))
            Text(quiz.hintMessage)
                .font(AppFont.caption)
                .foregroundStyle(AppColor.darkText)
        }
        .padding(16)
        .frame(maxWidth: .infinity, alignment: .leading)
        .background(
            RoundedRectangle(cornerRadius: 16)
                .fill(AppColor.yellow.opacity(0.3))
                .overlay(
                    RoundedRectangle(cornerRadius: 16)
                        .stroke(AppColor.yellow, lineWidth: 2)
                )
        )
    }

    private var optionsGrid: some View {
        VStack(spacing: 16) {
            ForEach(Array(quiz.options.enumerated()), id: \.0) { i, option in
                OptionButton(
                    option: option,
                    index: i,
                    quiz: quiz,
                    viewModel: viewModel,
                    buttonScale: buttonScales.indices.contains(i) ? buttonScales[i] : 1.0
                ) {
                    tappedOption(option, index: i)
                }
            }
        }
    }

    private var successOverlay: some View {
        ZStack {
            Color.black.opacity(0.3).ignoresSafeArea()

            VStack(spacing: 24) {
                Text("🎉")
                    .font(.system(size: 80))
                    .scaleEffect(successScale)

                Text(quiz.successMessage)
                    .font(.system(size: 24, weight: .black, design: .rounded))
                    .foregroundStyle(.white)
                    .multilineTextAlignment(.center)
                    .padding(.horizontal, 32)
                    .shadow(color: .black.opacity(0.3), radius: 4)

                Text(animal?.successPhrase ?? "やったね！")
                    .font(AppFont.body)
                    .foregroundStyle(.white.opacity(0.9))

                ConfettiView()
                    .frame(maxWidth: .infinity)
                    .frame(height: 120)
            }
        }
    }

    private func tappedOption(_ option: String, index: Int) {
        guard viewModel.quizState == .waiting else { return }

        withAnimation(.spring(duration: 0.3)) {
            if buttonScales.indices.contains(index) {
                buttonScales[index] = 0.93
            }
        }
        DispatchQueue.main.asyncAfter(deadline: .now() + 0.1) {
            withAnimation(.spring(duration: 0.3)) {
                if buttonScales.indices.contains(index) {
                    buttonScales[index] = 1.0
                }
            }
        }

        viewModel.submitAnswer(index, correctAnswer: quiz.options.firstIndex(of: quiz.answer) ?? 0)

        if quiz.isCorrect(option) {
            VoiceService.shared.speak(quiz.successMessage)
            withAnimation(.spring(duration: 0.6).delay(0.3)) {
                showSuccess = true
                successScale = 1.0
            }
            DispatchQueue.main.asyncAfter(deadline: .now() + 3.5) {
                onComplete()
            }
        } else {
            VoiceService.shared.speak(animal?.wrongPhrase ?? "もういちど！")
            shakingIndex = index
            DispatchQueue.main.asyncAfter(deadline: .now() + 0.5) {
                shakingIndex = nil
            }
        }
    }
}

struct OptionButton: View {
    let option: String
    let index: Int
    let quiz: Quiz
    let viewModel: AdventureViewModel
    let buttonScale: CGFloat
    let action: () -> Void

    private var isSelected: Bool {
        viewModel.selectedAnswerIndex == index
    }

    private var isCorrect: Bool {
        quiz.isCorrect(option)
    }

    private var buttonColor: Color {
        if viewModel.quizState == .waiting || !isSelected {
            return optionColor
        }
        return isCorrect ? AppColor.green : Color.red.opacity(0.7)
    }

    private var optionColor: Color {
        let colors: [Color] = [AppColor.primary, AppColor.secondary, AppColor.purple, AppColor.green]
        return colors[index % colors.count]
    }

    var body: some View {
        Button(action: action) {
            HStack(spacing: 16) {
                Text(option)
                    .font(.system(
                        size: quiz.type == .katakana ? 44 : 36,
                        weight: .black,
                        design: .rounded
                    ))
                    .foregroundStyle(.white)
                    .frame(minWidth: 60)

                if quiz.type != .katakana {
                    Text(option == quiz.answer ? "✓" : "")
                        .font(.system(size: 24, weight: .black))
                        .foregroundStyle(.white.opacity(0.8))
                }

                Spacer()
            }
            .padding(.horizontal, 28)
            .frame(maxWidth: .infinity)
            .frame(height: 78)
            .background(
                RoundedRectangle(cornerRadius: 24)
                    .fill(buttonColor)
                    .shadow(color: buttonColor.opacity(0.4), radius: 8, y: 4)
            )
        }
        .buttonStyle(.plain)
        .scaleEffect(buttonScale)
        .disabled(viewModel.quizState != .waiting)
    }
}

struct FlowLayout: Layout {
    var spacing: CGFloat = 8

    func sizeThatFits(proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) -> CGSize {
        let maxWidth = proposal.width ?? 300
        var x: CGFloat = 0
        var y: CGFloat = 0
        var rowHeight: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x + size.width > maxWidth, x > 0 {
                y += rowHeight + spacing
                x = 0
                rowHeight = 0
            }
            x += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
        return CGSize(width: maxWidth, height: y + rowHeight)
    }

    func placeSubviews(in bounds: CGRect, proposal: ProposedViewSize, subviews: Subviews, cache: inout ()) {
        var x = bounds.minX
        var y = bounds.minY
        var rowHeight: CGFloat = 0

        for subview in subviews {
            let size = subview.sizeThatFits(.unspecified)
            if x + size.width > bounds.maxX, x > bounds.minX {
                y += rowHeight + spacing
                x = bounds.minX
                rowHeight = 0
            }
            subview.place(at: CGPoint(x: x, y: y), proposal: ProposedViewSize(size))
            x += size.width + spacing
            rowHeight = max(rowHeight, size.height)
        }
    }
}

struct ConfettiView: View {
    let confettiColors: [Color] = [.red, .orange, .yellow, .green, .blue, .purple, .pink]
    @State private var positions: [CGPoint] = []
    @State private var animating: Bool = false

    var body: some View {
        GeometryReader { geo in
            ForEach(0..<20, id: \.self) { i in
                Text(["🎊", "🎉", "⭐️", "✨", "🌟"][i % 5])
                    .font(.system(size: CGFloat.random(in: 20...36)))
                    .position(
                        x: positions.indices.contains(i) ? positions[i].x : geo.size.width / 2,
                        y: animating ? geo.size.height + 40 : -40
                    )
                    .animation(
                        .easeIn(duration: Double.random(in: 0.8...1.6))
                        .delay(Double(i) * 0.06),
                        value: animating
                    )
            }
        }
        .onAppear {
            positions = (0..<20).map { _ in
                CGPoint(x: CGFloat.random(in: 20...340), y: 0)
            }
            withAnimation { animating = true }
        }
    }
}
