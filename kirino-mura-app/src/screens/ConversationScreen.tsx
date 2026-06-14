import React, { useState, useEffect, useRef } from 'react'
import {
  View, Text, TextInput, TouchableOpacity, FlatList,
  StyleSheet, SafeAreaView, KeyboardAvoidingView, Platform,
  ActivityIndicator,
} from 'react-native'
import { useRoute, RouteProp } from '@react-navigation/native'
import { RootStackParamList, NPC, Message, EMOTION_LABELS, VillageState } from '../types'
import { loadState, sendMessageToNPC } from '../services/GameStateService'

type Route = RouteProp<RootStackParamList, 'Conversation'>

const PORTRAIT_BG: Record<string, [string, string]> = {
  happy:      ['#f5a020', '#f5e040'],
  worried:    ['#6070b8', '#90a8d8'],
  sad:        ['#3050b0', '#6080c8'],
  mysterious: ['#4a2880', '#7860c0'],
  neutral:    ['#3a8880', '#60b8a8'],
  excited:    ['#d04060', '#f07060'],
}

export default function ConversationScreen() {
  const { params } = useRoute<Route>()
  const [npc, setNpc] = useState<NPC | null>(null)
  const [messages, setMessages] = useState<Message[]>([])
  const [input, setInput] = useState('')
  const [sending, setSending] = useState(false)
  const listRef = useRef<FlatList>(null)

  useEffect(() => {
    loadState().then((s: VillageState) => {
      const found = s.npcs.find((n) => n.id === params.npcId) ?? null
      setNpc(found)
      if (found) {
        const history = found.conversationHistory
        if (history.length === 0) {
          setMessages([{
            id: 'intro',
            role: 'npc',
            content: `あなたが近づくと、${found.name}が静かに振り返った。`,
            timestamp: new Date().toISOString(),
          }])
        } else {
          setMessages(history)
        }
      }
    })
  }, [params.npcId])

  const send = async () => {
    const text = input.trim()
    if (!text || sending || !npc) return
    setInput('')
    setSending(true)

    const playerMsg: Message = {
      id: `p-${Date.now()}`, role: 'player', content: text,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, playerMsg])

    const s = await loadState()
    const { state: newState, npcResponse } = await sendMessageToNPC(s, npc.id, text)
    const responseNpc = newState.npcs.find((n) => n.id === npc.id) ?? npc
    setNpc(responseNpc)

    const npcMsg: Message = {
      id: `n-${Date.now()}`, role: 'npc', content: npcResponse,
      timestamp: new Date().toISOString(),
    }
    setMessages((prev) => [...prev, npcMsg])
    setSending(false)
    setTimeout(() => listRef.current?.scrollToEnd({ animated: true }), 100)
  }

  if (!npc) return <View style={styles.center}><ActivityIndicator color="#a0b8e0" /></View>

  const [bgTop, bgBottom] = PORTRAIT_BG[npc.emotionalState] ?? ['#4a4a6a', '#7a7a9a']

  return (
    <SafeAreaView style={styles.root}>
      <View style={[styles.portrait, { backgroundColor: bgTop }]}>
        <View style={[styles.portraitInner, { backgroundColor: bgBottom + '44' }]}>
          <Text style={styles.portraitEmoji}>{npc.avatarEmoji}</Text>
          <View style={styles.emotionBadge}>
            <Text style={styles.emotionText}>{EMOTION_LABELS[npc.emotionalState]}</Text>
          </View>
        </View>
      </View>

      <KeyboardAvoidingView
        style={styles.flex}
        behavior={Platform.OS === 'ios' ? 'padding' : undefined}
        keyboardVerticalOffset={90}
      >
        <FlatList
          ref={listRef}
          data={messages}
          keyExtractor={(m) => m.id}
          contentContainerStyle={styles.messageList}
          onContentSizeChange={() => listRef.current?.scrollToEnd()}
          renderItem={({ item }) => (
            <View style={[styles.bubble, item.role === 'player' ? styles.bubblePlayer : styles.bubbleNpc]}>
              {item.role === 'npc' && (
                <Text style={styles.npcLabel}>{npc.name}</Text>
              )}
              <View style={[styles.bubbleBg, item.role === 'player' ? styles.bubbleBgPlayer : styles.bubbleBgNpc]}>
                <Text style={[styles.bubbleText, item.role === 'player' && styles.bubbleTextPlayer]}>
                  {item.content}
                </Text>
              </View>
            </View>
          )}
        />

        {sending && (
          <View style={styles.typingRow}>
            <View style={styles.typingBubble}>
              <Text style={styles.typingDots}>…</Text>
            </View>
          </View>
        )}

        <View style={styles.inputRow}>
          <TextInput
            style={styles.input}
            value={input}
            onChangeText={setInput}
            placeholder="言葉を入れる…"
            placeholderTextColor="#aaa"
            multiline
            maxLength={200}
          />
          <TouchableOpacity
            style={[styles.sendBtn, (!input.trim() || sending) && styles.sendBtnDisabled]}
            onPress={send}
            disabled={!input.trim() || sending}
          >
            <Text style={styles.sendIcon}>↑</Text>
          </TouchableOpacity>
        </View>
      </KeyboardAvoidingView>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#f5f5f7' },
  flex: { flex: 1 },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  portrait: { height: 160, justifyContent: 'center', alignItems: 'center' },
  portraitInner: { alignItems: 'center', padding: 12, borderRadius: 16 },
  portraitEmoji: { fontSize: 64 },
  emotionBadge: {
    marginTop: 6, backgroundColor: 'rgba(0,0,0,0.25)',
    borderRadius: 12, paddingHorizontal: 10, paddingVertical: 3,
  },
  emotionText: { fontSize: 12, color: 'rgba(255,255,255,0.9)' },
  messageList: { padding: 16, paddingBottom: 8 },
  bubble: { marginBottom: 10 },
  bubblePlayer: { alignItems: 'flex-end' },
  bubbleNpc: { alignItems: 'flex-start' },
  npcLabel: { fontSize: 11, color: '#999', marginBottom: 2, marginLeft: 4 },
  bubbleBg: { maxWidth: '78%', borderRadius: 18, paddingHorizontal: 14, paddingVertical: 10 },
  bubbleBgPlayer: { backgroundColor: '#5a7ec8' },
  bubbleBgNpc: { backgroundColor: '#e8e8ec' },
  bubbleText: { fontSize: 15, lineHeight: 22, color: '#222' },
  bubbleTextPlayer: { color: '#fff' },
  typingRow: { paddingHorizontal: 16, paddingBottom: 4 },
  typingBubble: {
    backgroundColor: '#e8e8ec', borderRadius: 18,
    paddingHorizontal: 16, paddingVertical: 10, alignSelf: 'flex-start',
  },
  typingDots: { fontSize: 18, color: '#999', letterSpacing: 4 },
  inputRow: {
    flexDirection: 'row', alignItems: 'flex-end', gap: 10,
    paddingHorizontal: 16, paddingVertical: 12,
    borderTopWidth: 1, borderTopColor: '#e0e0e0', backgroundColor: '#fff',
  },
  input: {
    flex: 1, backgroundColor: '#f0f0f4', borderRadius: 20,
    paddingHorizontal: 16, paddingVertical: 10, fontSize: 15,
    maxHeight: 100, color: '#222',
  },
  sendBtn: {
    width: 42, height: 42, borderRadius: 21,
    backgroundColor: '#5a7ec8', alignItems: 'center', justifyContent: 'center',
  },
  sendBtnDisabled: { backgroundColor: '#ccc' },
  sendIcon: { fontSize: 20, color: '#fff', fontWeight: '700' },
})
