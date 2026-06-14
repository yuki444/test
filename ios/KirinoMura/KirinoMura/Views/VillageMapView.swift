import SwiftUI

struct VillageMapView: View {
    @EnvironmentObject var gameState: GameStateService
    @State private var selectedLocation: VillageLocation?

    private let locationLayout: [(VillageLocation, x: Double, y: Double)] = [
        (.elderHouse,  0.50, 0.18),
        (.plaza,       0.50, 0.38),
        (.bakery,      0.22, 0.60),
        (.smithy,      0.78, 0.60),
        (.riverside,   0.50, 0.78),
    ]

    var body: some View {
        NavigationStack {
            ZStack {
                villageBackground

                GeometryReader { geo in
                    ForEach(locationLayout, id: \.0) { location, x, y in
                        LocationPin(
                            location: location,
                            npcs: gameState.villageState.npcs.filter { $0.location == location }
                        ) {
                            selectedLocation = location
                        }
                        .position(x: geo.size.width * x, y: geo.size.height * y)
                    }
                }

                VStack {
                    HStack {
                        Spacer()
                        SeasonBadge(season: gameState.villageState.currentSeason)
                            .padding()
                    }
                    Spacer()
                    Text(gameState.villageState.currentSeason.mysteryHint)
                        .font(.caption)
                        .foregroundStyle(.white.opacity(0.75))
                        .multilineTextAlignment(.center)
                        .padding(.horizontal, 24)
                        .padding(.bottom, 32)
                }
            }
            .navigationDestination(item: $selectedLocation) { location in
                SceneView(location: location)
            }
            .sheet(isPresented: $gameState.isShowingMorningSummary) {
                MorningSummaryView()
            }
            .navigationBarHidden(true)
        }
    }

    private var villageBackground: some View {
        LinearGradient(
            colors: [
                Color(red: 0.52, green: 0.78, blue: 0.95),
                Color(red: 0.82, green: 0.92, blue: 0.80),
                Color(red: 0.72, green: 0.85, blue: 0.65),
            ],
            startPoint: .top,
            endPoint: .bottom
        )
        .ignoresSafeArea()
    }
}

struct LocationPin: View {
    let location: VillageLocation
    let npcs: [NPC]
    let onTap: () -> Void

    private var hasAlert: Bool { npcs.contains { $0.wantsToTalk } }

    var body: some View {
        Button(action: onTap) {
            VStack(spacing: 4) {
                ZStack(alignment: .topTrailing) {
                    RoundedRectangle(cornerRadius: 14)
                        .fill(.white.opacity(0.88))
                        .shadow(color: .black.opacity(0.12), radius: 6, x: 0, y: 3)
                        .frame(width: 76, height: 66)
                        .overlay(
                            VStack(spacing: 2) {
                                Text(locationEmoji)
                                    .font(.system(size: 26))
                                HStack(spacing: -6) {
                                    ForEach(npcs.prefix(3)) { npc in
                                        Text(npc.avatarEmoji)
                                            .font(.system(size: 14))
                                    }
                                }
                            }
                        )

                    if hasAlert {
                        ZStack {
                            Circle().fill(.white).frame(width: 16, height: 16)
                            Circle().fill(.orange).frame(width: 12, height: 12)
                        }
                        .offset(x: 5, y: -5)
                    }
                }

                Text(location.rawValue)
                    .font(.caption2)
                    .fontWeight(.semibold)
                    .foregroundStyle(.white)
                    .shadow(color: .black.opacity(0.3), radius: 2)
            }
        }
        .buttonStyle(.plain)
    }

    private var locationEmoji: String {
        switch location {
        case .plaza:       return "🏛️"
        case .bakery:      return "🏠"
        case .smithy:      return "⚒️"
        case .riverside:   return "🌊"
        case .elderHouse:  return "🏡"
        }
    }
}

struct SeasonBadge: View {
    let season: Season

    var body: some View {
        VStack(alignment: .trailing, spacing: 3) {
            Text("シーズン\(season.number) · \(season.dayNumber)日目")
                .font(.caption)
                .fontWeight(.semibold)
                .foregroundStyle(.white)
            ProgressView(value: season.progress)
                .tint(.white)
                .frame(width: 90)
        }
        .padding(.horizontal, 12)
        .padding(.vertical, 8)
        .background(.black.opacity(0.28))
        .clipShape(RoundedRectangle(cornerRadius: 10))
    }
}
