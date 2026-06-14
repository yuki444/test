import Foundation

struct ClaudeAPIMessage: Codable {
    let role: String
    let content: String
}

struct ClaudeRequest: Codable {
    let model: String
    let maxTokens: Int
    let system: String
    let messages: [ClaudeAPIMessage]

    enum CodingKeys: String, CodingKey {
        case model
        case maxTokens = "max_tokens"
        case system
        case messages
    }
}

struct ClaudeResponse: Codable {
    let content: [ClaudeContent]

    struct ClaudeContent: Codable {
        let type: String
        let text: String
    }
}

class ClaudeService {
    private let apiKey: String
    private let model = "claude-sonnet-4-6"
    private let baseURL = "https://api.anthropic.com/v1/messages"

    init(apiKey: String) {
        self.apiKey = apiKey
    }

    func generateNPCResponse(npc: NPC, playerMessage: String, season: Season) async throws -> String {
        let systemPrompt = """
        あなたはファンタジー村「霧の村」に住む\(npc.name)（\(npc.occupation)）です。

        あなたの性格: \(npc.personality)
        あなたの背景: \(npc.backstory)
        現在の感情状態: \(npc.emotionalState.rawValue)
        プレイヤーとの関係スコア: \(npc.relationshipWithPlayer)/100

        村の状況ヒント: \(season.mysteryHint)

        【返答ルール】
        - 自然で短い返答をする（2〜4文）
        - 村人として自然な話し方で
        - 感情は直接言わず、行動や言葉の端々で表現する
        - 村の謎については断片的にしか語らない
        - 日本語で返答する
        """

        var messages: [ClaudeAPIMessage] = npc.conversationHistory.map { msg in
            ClaudeAPIMessage(
                role: msg.role == .player ? "user" : "assistant",
                content: msg.content
            )
        }
        messages.append(ClaudeAPIMessage(role: "user", content: playerMessage))

        let request = ClaudeRequest(
            model: model,
            maxTokens: 250,
            system: systemPrompt,
            messages: messages
        )
        return try await send(request)
    }

    func generateMorningSummary(villageState: VillageState) async throws -> String {
        let npcStates = villageState.npcs
            .map { "\($0.name)（\($0.occupation)）: \($0.emotionalState.rawValue)" }
            .joined(separator: "\n")

        let systemPrompt = """
        あなたは「霧の村」の語り手です。
        昨日の村での出来事を詩的で短い文章（3〜5文）で語ってください。

        村の雰囲気: \(villageState.atmosphere.rawValue)
        村人の状況:
        \(npcStates)

        シーズンのヒント: \(villageState.currentSeason.mysteryHint)

        【ルール】
        - 具体的な出来事を2〜3個語る
        - 霧や自然の描写を交える
        - 何かが起きようとしている予感を漂わせる
        - 日本語で
        """

        let request = ClaudeRequest(
            model: model,
            maxTokens: 350,
            system: systemPrompt,
            messages: [ClaudeAPIMessage(role: "user", content: "昨日の村での出来事を語ってください。")]
        )
        return try await send(request)
    }

    private func send(_ request: ClaudeRequest) async throws -> String {
        var urlRequest = URLRequest(url: URL(string: baseURL)!)
        urlRequest.httpMethod = "POST"
        urlRequest.setValue("application/json", forHTTPHeaderField: "Content-Type")
        urlRequest.setValue(apiKey, forHTTPHeaderField: "x-api-key")
        urlRequest.setValue("2023-06-01", forHTTPHeaderField: "anthropic-version")
        urlRequest.httpBody = try JSONEncoder().encode(request)

        let (data, response) = try await URLSession.shared.data(for: urlRequest)

        guard let http = response as? HTTPURLResponse, http.statusCode == 200 else {
            throw ClaudeError.apiError
        }

        let decoded = try JSONDecoder().decode(ClaudeResponse.self, from: data)
        return decoded.content.first(where: { $0.type == "text" })?.text ?? ""
    }

    enum ClaudeError: Error {
        case apiError
    }
}
