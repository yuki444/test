import SwiftUI

struct HomeView: View {
    @Environment(AppState.self) private var appState
    @State private var headerScale: CGFloat = 0.8
    @State private var showContent: Bool = false
    @State private var animalBounce: CGFloat = 0

    var body: some View {
        ZStack {
            backgroundGradient

            ScrollView(showsIndicators: false) {
                VStack(spacing: 28) {
                    headerSection
                    animalSection
                    adventureCard
                    startButton
                    progressSection
                }
                .padding(.horizontal, 20)
                .padding(.vertical, 40)
            }
        }
        .onAppear {
            withAnimation(.spring(duration: 0.8)) {
                headerScale = 1.0
                showContent = true
            }
            withAnimation(.easeInOut(duration: 1.2).repeatForever(autoreverses: true)) {
                animalBounce = -8
            }
        }
    }

    private var backgroundGradient: some View {
        LinearGradient(
            colors: [
                Color(hex: "#FFF9F0"),
                Color(hex: "#FFE4B5").opacity(0.6),
                Color(hex: "#E0F4FF").opacity(0.8)
            ],
            startPoint: .topLeading,
            endPoint: .bottomTrailing
        )
        .ignoresSafeArea()
    }

    private var headerSection: some View {
        VStack(spacing: 8) {
            Text("🏠")
                .font(.system(size: 52))
            Text("おうちたんけん")
                .font(.system(size: 34, weight: .black, design: .rounded))
                .foregroundStyle(
                    LinearGradient(
                        colors: [AppColor.primary, AppColor.purple],
                        startPoint: .leading,
                        endPoint: .trailing
                    )
                )
            Text("きょうも ぼうけんに でかけよう！")
                .font(AppFont.caption)
                .foregroundStyle(.secondary)
        }
        .scaleEffect(headerScale)
        .opacity(showContent ? 1 : 0)
    }

    private var animalSection: some View {
        Group {
            if let animal = appState.todaysAnimal {
                VStack(spacing: 12) {
                    ZStack {
                        PulsingCircle(color: AppColor.secondary)
                            .frame(width: 110, height: 110)

                        Text(animal.emoji)
                            .font(.system(size: 72))
                            .offset(y: animalBounce)
                            .shadow(color: .black.opacity(0.1), radius: 4, y: 4)
                    }
                    .frame(height: 120)

                    Text(animal.name)
                        .font(AppFont.body)
                        .foregroundStyle(AppColor.darkText)

                    Text(animal.greeting)
                        .font(AppFont.caption)
                        .foregroundStyle(.secondary)
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 20)
                }
                .padding(20)
                .background(
                    RoundedRectangle(cornerRadius: 24)
                        .fill(.white)
                        .shadow(color: AppColor.softShadow, radius: 12, y: 4)
                )
            }
        }
        .opacity(showContent ? 1 : 0)
    }

    private var adventureCard: some View {
        Group {
            if let adventure = appState.todaysAdventure {
                VStack(alignment: .leading, spacing: 12) {
                    HStack {
                        Text("⭐️ きょうの ぼうけん")
                            .font(AppFont.caption)
                            .foregroundStyle(.white.opacity(0.9))
                        Spacer()
                        if appState.isTodayCompleted {
                            Label("かんりょう！", systemImage: "checkmark.circle.fill")
                                .font(AppFont.caption)
                                .foregroundStyle(.white)
                        }
                    }

                    Text(adventure.title)
                        .font(.system(size: 28, weight: .black, design: .rounded))
                        .foregroundStyle(.white)

                    Text(adventure.subtitle)
                        .font(AppFont.caption)
                        .foregroundStyle(.white.opacity(0.9))

                    HStack(spacing: 8) {
                        Label(adventure.locationName, systemImage: "mappin.circle.fill")
                            .font(AppFont.caption)
                            .foregroundStyle(.white)
                    }
                }
                .padding(20)
                .frame(maxWidth: .infinity, alignment: .leading)
                .background(
                    RoundedRectangle(cornerRadius: 24)
                        .fill(
                            LinearGradient(
                                colors: [
                                    Color(hex: adventure.colorHex),
                                    Color(hex: adventure.colorHex).opacity(0.7)
                                ],
                                startPoint: .topLeading,
                                endPoint: .bottomTrailing
                            )
                        )
                        .shadow(color: Color(hex: adventure.colorHex).opacity(0.4), radius: 12, y: 6)
                )
            }
        }
        .opacity(showContent ? 1 : 0)
    }

    private var startButton: some View {
        KidsButton(
            title: appState.isTodayCompleted ? "もういちど あそぶ！" : "ぼうけん スタート！",
            emoji: appState.isTodayCompleted ? "🔄" : "🚀",
            color: AppColor.primary
        ) {
            withAnimation(.spring(duration: 0.5)) {
                appState.currentScreen = .intro
            }
        }
        .padding(.horizontal, 4)
        .opacity(showContent ? 1 : 0)
        .scaleEffect(showContent ? 1 : 0.8)
    }

    private var progressSection: some View {
        VStack(spacing: 12) {
            Text("こんしゅうの ぼうけん")
                .font(AppFont.caption)
                .foregroundStyle(.secondary)

            HStack(spacing: 12) {
                ForEach(weekDays, id: \.0) { day, isCompleted in
                    VStack(spacing: 4) {
                        ZStack {
                            Circle()
                                .fill(isCompleted ? AppColor.green : Color.gray.opacity(0.2))
                                .frame(width: 40, height: 40)
                            Text(isCompleted ? "⭐️" : "")
                                .font(.system(size: 20))
                        }
                        Text(day)
                            .font(.system(size: 12, weight: .medium, design: .rounded))
                            .foregroundStyle(.secondary)
                    }
                }
            }
        }
        .padding(16)
        .background(
            RoundedRectangle(cornerRadius: 20)
                .fill(.white)
                .shadow(color: AppColor.softShadow, radius: 8, y: 2)
        )
        .opacity(showContent ? 1 : 0)
    }

    private var weekDays: [(String, Bool)] {
        let calendar = Calendar.current
        let today = Date()
        let formatter = DateFormatter()
        formatter.dateFormat = "yyyy-MM-dd"
        let dayNames = ["月", "火", "水", "木", "金", "土", "日"]

        return (0..<7).map { offset in
            let date = calendar.date(byAdding: .day, value: offset - 6, to: today) ?? today
            let weekday = calendar.component(.weekday, from: date)
            let adjustedWeekday = (weekday + 5) % 7
            let key = formatter.string(from: date)
            return (dayNames[adjustedWeekday], appState.completedDates.contains(key))
        }
    }
}
