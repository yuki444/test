import { NPC, Season, VillageState } from '../types'

const API_KEY = process.env.EXPO_PUBLIC_CLAUDE_API_KEY ?? ''
const MODEL = 'claude-sonnet-4-6'
const BASE_URL = 'https://api.anthropic.com/v1/messages'

interface ApiMessage {
  role: 'user' | 'assistant'
  content: string
}

async function callClaude(system: string, messages: ApiMessage[], maxTokens = 250): Promise<string> {
  const res = await fetch(BASE_URL, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'x-api-key': API_KEY,
      'anthropic-version': '2023-06-01',
    },
    body: JSON.stringify({ model: MODEL, max_tokens: maxTokens, system, messages }),
  })
  if (!res.ok) throw new Error(`Claude API error: ${res.status}`)
  const json = await res.json()
  return json.content?.find((c: { type: string }) => c.type === 'text')?.text ?? ''
}

export async function generateNPCResponse(
  npc: NPC,
  playerMessage: string,
  season: Season
): Promise<string> {
  const system = `あなたはファンタジー村「霧の村」に住む${npc.name}（${npc.occupation}）です。
性格: ${npc.personality}
背景: ${npc.backstory}
感情状態: ${npc.emotionalState}
プレイヤーとの関係スコア: ${npc.relationshipWithPlayer}/100
村の状況ヒント: ${season.mysteryHint}

【ルール】自然で短い返答（2〜4文）、日本語で、感情は行動で表現、謎は断片的にのみ語る。`

  const messages: ApiMessage[] = [
    ...npc.conversationHistory.map((m) => ({
      role: (m.role === 'player' ? 'user' : 'assistant') as 'user' | 'assistant',
      content: m.content,
    })),
    { role: 'user', content: playerMessage },
  ]

  return callClaude(system, messages, 250)
}

export async function generateMorningSummary(state: VillageState): Promise<string> {
  const npcInfo = state.npcs.map((n) => `${n.name}（${n.occupation}）: ${n.emotionalState}`).join('\n')
  const system = `あなたは「霧の村」の語り手です。昨日の村での出来事を詩的で短い文章（3〜5文）で語ってください。
村の雰囲気: ${state.atmosphere}、村人:\n${npcInfo}
ヒント: ${state.currentSeason.mysteryHint}
具体的な出来事2〜3個・自然の描写・予感を漂わせる。日本語で。`

  return callClaude(
    system,
    [{ role: 'user', content: '昨日の村での出来事を語ってください。' }],
    350
  )
}
