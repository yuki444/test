import SwiftUI

struct SceneView: View {
    @EnvironmentObject var gameState: GameStateService
    let location: VillageLocation
    @State private var selectedNPCId: UUID?

    private var npcsHere: [NPC] {
        gameState.villageState.npcs.filter { $0.location == location }
    }

    var body: some View {
        ZStack {
            sceneBackground
            VStack {
                Spacer()
                HStack(alignment: .bottom, spacing: 28) {
                    ForEach(npcsHere) { npc in
                        NPCFigure(npc: npc) { selectedNPCId = npc.id }
                    }
                }
                .padding(.bottom, 48)
            }
        }
        .navigationTitle(location.rawValue)
        .navigationBarTitleDisplayMode(.inline)
        .navigationDestination(item: $selectedNPCId) { id in
            ConversationView(npcId: id)
        }
    }

    private var sceneBackground: some View {
        LinearGradient(
            colors: sceneColors,
            startPoint: .top,
            endPoint: .bottom
        )
        .ignoresSafeArea()
    }

    private var sceneColors: [Color] {
        switch location {
        case .plaza:
            return [Color(red: 0.55, green: 0.80, blue: 0.55), Color(red: 0.85, green: 0.90, blue: 0.70)]
        case .bakery:
            return [Color(red: 0.90, green: 0.65, blue: 0.40), Color(red: 0.95, green: 0.85, blue: 0.65)]
        case .smithy:
            return [Color(red: 0.40, green: 0.40, blue: 0.45), Color(red: 0.65, green: 0.60, blue: 0.55)]
        case .riverside:
            return [Color(red: 0.35, green: 0.65, blue: 0.90), Color(red: 0.70, green: 0.88, blue: 0.95)]
        case .elderHouse:
            return [Color(red: 0.40, green: 0.35, blue: 0.60), Color(red: 0.65, green: 0.60, blue: 0.80)]
        }
    }
}

struct NPCFigure: View {
    let npc: NPC
    let onTap: () -> Void

    var body: some View {
        Button(action: onTap) {
            VStack(spacing: 6) {
                ZStack(alignment: .topTrailing) {
                    Circle()
                        .fill(.white.opacity(0.90))
                        .frame(width: 76, height: 76)
                        .shadow(color: .black.opacity(0.15), radius: 8, y: 4)
                        .overlay(
                            Text(npc.avatarEmoji)
                                .font(.system(size: 38))
                        )

                    if npc.wantsToTalk {
                        Text("💬")
                            .font(.system(size: 20))
                            .offset(x: 6, y: -6)
                    }
                }

                Text(npc.name)
                    .font(.caption)
                    .fontWeight(.medium)
                    .foregroundStyle(.white)
                    .shadow(color: .black.opacity(0.4), radius: 2)
            }
        }
        .buttonStyle(.plain)
    }
}
