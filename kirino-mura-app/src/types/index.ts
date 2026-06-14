export type VillageLocation = 'plaza' | 'bakery' | 'smithy' | 'riverside' | 'elderHouse'

export const LOCATION_LABELS: Record<VillageLocation, string> = {
  plaza: '広場',
  bakery: 'パン屋',
  smithy: '鍛冶屋',
  riverside: '川沿い',
  elderHouse: '長老の家',
}

export const LOCATION_EMOJI: Record<VillageLocation, string> = {
  plaza: '🏛️',
  bakery: '🏠',
  smithy: '⚒️',
  riverside: '🌊',
  elderHouse: '🏡',
}

export type EmotionalState = 'happy' | 'worried' | 'sad' | 'mysterious' | 'neutral' | 'excited'

export const EMOTION_LABELS: Record<EmotionalState, string> = {
  happy: '明るい',
  worried: '心配そう',
  sad: '悲しそう',
  mysterious: '何かを隠している',
  neutral: '普通',
  excited: '興奮している',
}

export interface Message {
  id: string
  role: 'player' | 'npc'
  content: string
  timestamp: string
}

export interface NPC {
  id: string
  name: string
  occupation: string
  personality: string
  backstory: string
  emotionalState: EmotionalState
  relationshipWithPlayer: number
  conversationHistory: Message[]
  wantsToTalk: boolean
  location: VillageLocation
  avatarEmoji: string
}

export interface Season {
  number: number
  dayNumber: number
  totalDays: number
  mysteryTitle: string
  mysteryHint: string
  internalTruth: string
  isResolved: boolean
  startDate: string
}

export type VillageAtmosphere = 'warm' | 'tense' | 'mysterious' | 'peaceful' | 'sad'

export interface VillageState {
  atmosphere: VillageAtmosphere
  currentSeason: Season
  npcs: NPC[]
  lastLoginDate: string | null
}

export type RootStackParamList = {
  VillageMap: undefined
  Scene: { location: VillageLocation }
  Conversation: { npcId: string }
  MorningSummary: { summary: string }
}
