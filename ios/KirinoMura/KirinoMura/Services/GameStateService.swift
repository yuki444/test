import Foundation
import Combine

@MainActor
class GameStateService: ObservableObject {
    @Published var villageState: VillageState
    @Published var morningSummary: String = ""
    @Published var isShowingMorningSummary: Bool = false

    private let claude: ClaudeService
    private let saveKey = "villageState_v1"

    init() {
        self.claude = ClaudeService(apiKey: Config.claudeAPIKey)

        if let data = UserDefaults.standard.data(forKey: "villageState_v1"),
           let saved = try? JSONDecoder().decode(VillageState.self, from: data) {
            self.villageState = saved
        } else {
            self.villageState = VillageState(
                currentSeason: .firstSeason,
                npcs: NPC.defaultNPCs
            )
        }

        checkDayAdvance()
    }

    func save() {
        if let data = try? JSONEncoder().encode(villageState) {
            UserDefaults.standard.set(data, forKey: saveKey)
        }
    }

    private func checkDayAdvance() {
        guard let lastLogin = villageState.lastLoginDate else {
            villageState.lastLoginDate = Date()
            save()
            return
        }

        let days = Calendar.current.dateComponents([.day], from: lastLogin, to: Date()).day ?? 0
        guard days >= 1 else { return }

        for _ in 0..<days {
            villageState.advanceDay()
        }
        save()

        Task {
            await generateMorningSummary()
        }
    }

    func generateMorningSummary() async {
        do {
            morningSummary = try await claude.generateMorningSummary(villageState: villageState)
        } catch {
            morningSummary = "静かな朝。霧がゆっくりと晴れていく。村は今日も続く。"
        }
        isShowingMorningSummary = true
    }

    func sendMessage(to npcId: UUID, message: String) async -> String {
        guard let index = villageState.npcs.firstIndex(where: { $0.id == npcId }) else {
            return "…"
        }

        let playerMsg = Message(id: UUID(), role: .player, content: message, timestamp: Date())
        villageState.npcs[index].conversationHistory.append(playerMsg)

        do {
            let npc = villageState.npcs[index]
            let response = try await claude.generateNPCResponse(
                npc: npc,
                playerMessage: message,
                season: villageState.currentSeason
            )

            let npcMsg = Message(id: UUID(), role: .npc, content: response, timestamp: Date())
            villageState.npcs[index].conversationHistory.append(npcMsg)
            villageState.npcs[index].relationshipWithPlayer = min(100, npc.relationshipWithPlayer + 2)
            save()
            return response
        } catch {
            return "…"
        }
    }

    func npc(by id: UUID) -> NPC? {
        villageState.npcs.first { $0.id == id }
    }
}
