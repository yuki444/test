import SwiftUI

struct MorningSummaryView: View {
    @EnvironmentObject var gameState: GameStateService

    var body: some View {
        ZStack {
            LinearGradient(
                colors: [Color(red: 0.12, green: 0.10, blue: 0.20), Color(red: 0.25, green: 0.22, blue: 0.35)],
                startPoint: .top,
                endPoint: .bottom
            )
            .ignoresSafeArea()

            VStack(spacing: 0) {
                Spacer()

                VStack(spacing: 12) {
                    Text("昨日の村")
                        .font(.title3)
                        .fontWeight(.light)
                        .foregroundStyle(.white.opacity(0.60))

                    Text("── \(gameState.villageState.currentSeason.dayNumber)日目の朝 ──")
                        .font(.caption)
                        .foregroundStyle(.white.opacity(0.40))
                }

                Spacer().frame(height: 40)

                Text(gameState.morningSummary)
                    .font(.body)
                    .lineSpacing(9)
                    .multilineTextAlignment(.center)
                    .foregroundStyle(.white.opacity(0.88))
                    .padding(.horizontal, 36)

                Spacer()

                Button {
                    gameState.isShowingMorningSummary = false
                } label: {
                    Text("村へ行く")
                        .fontWeight(.medium)
                        .frame(maxWidth: .infinity)
                        .padding(.vertical, 16)
                        .background(.white.opacity(0.15))
                        .foregroundStyle(.white)
                        .clipShape(RoundedRectangle(cornerRadius: 16))
                        .overlay(
                            RoundedRectangle(cornerRadius: 16)
                                .stroke(.white.opacity(0.25), lineWidth: 1)
                        )
                }
                .padding(.horizontal, 32)
                .padding(.bottom, 52)
            }
        }
    }
}
