import AsyncStorage from '@react-native-async-storage/async-storage'
import { VillageState, Message } from '../types'
import { DEFAULT_VILLAGE_STATE } from '../data/defaultData'
import { generateNPCResponse, generateMorningSummary } from './ClaudeService'

const STORAGE_KEY = 'villageState_v1'

const genId = () => `${Date.now()}-${Math.random().toString(36).slice(2, 7)}`

export async function loadState(): Promise<VillageState> {
  try {
    const raw = await AsyncStorage.getItem(STORAGE_KEY)
    if (raw) return JSON.parse(raw) as VillageState
  } catch {}
  return { ...DEFAULT_VILLAGE_STATE }
}

export async function saveState(state: VillageState): Promise<void> {
  await AsyncStorage.setItem(STORAGE_KEY, JSON.stringify(state))
}

export function checkDayAdvance(state: VillageState): { state: VillageState; daysElapsed: number } {
  if (!state.lastLoginDate) {
    return { state: { ...state, lastLoginDate: new Date().toISOString() }, daysElapsed: 0 }
  }
  const last = new Date(state.lastLoginDate)
  const now = new Date()
  const daysElapsed = Math.floor((now.getTime() - last.getTime()) / 86_400_000)

  if (daysElapsed < 1) return { state, daysElapsed: 0 }

  let next = { ...state }
  for (let i = 0; i < daysElapsed; i++) {
    next = {
      ...next,
      currentSeason: {
        ...next.currentSeason,
        dayNumber: next.currentSeason.dayNumber + 1,
      },
    }
  }
  next.lastLoginDate = new Date().toISOString()
  return { state: next, daysElapsed }
}

export async function getMorningSummary(state: VillageState): Promise<string> {
  try {
    return await generateMorningSummary(state)
  } catch {
    return '静かな朝。霧がゆっくりと晴れていく。村は今日も続く。'
  }
}

export async function sendMessageToNPC(
  state: VillageState,
  npcId: string,
  playerText: string
): Promise<{ state: VillageState; npcResponse: string }> {
  const idx = state.npcs.findIndex((n) => n.id === npcId)
  if (idx < 0) return { state, npcResponse: '…' }

  const npc = state.npcs[idx]
  const playerMsg: Message = { id: genId(), role: 'player', content: playerText, timestamp: new Date().toISOString() }

  const updatedNPC = { ...npc, conversationHistory: [...npc.conversationHistory, playerMsg] }

  let npcResponse = '…'
  try {
    npcResponse = await generateNPCResponse(updatedNPC, playerText, state.currentSeason)
  } catch {}

  const npcMsg: Message = { id: genId(), role: 'npc', content: npcResponse, timestamp: new Date().toISOString() }
  const finalNPC = {
    ...updatedNPC,
    conversationHistory: [...updatedNPC.conversationHistory, npcMsg],
    relationshipWithPlayer: Math.min(100, updatedNPC.relationshipWithPlayer + 2),
  }

  const newNPCs = [...state.npcs]
  newNPCs[idx] = finalNPC
  const newState = { ...state, npcs: newNPCs }
  await saveState(newState)

  return { state: newState, npcResponse }
}
