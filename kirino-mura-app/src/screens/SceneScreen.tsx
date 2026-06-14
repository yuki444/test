import React, { useState, useEffect } from 'react'
import { View, Text, TouchableOpacity, StyleSheet, SafeAreaView } from 'react-native'
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native'
import { StackNavigationProp } from '@react-navigation/stack'
import { RootStackParamList, LOCATION_LABELS, VillageState, NPC } from '../types'
import { loadState } from '../services/GameStateService'

type Nav = StackNavigationProp<RootStackParamList, 'Scene'>
type Route = RouteProp<RootStackParamList, 'Scene'>

const SCENE_BG: Record<string, readonly [string, string]> = {
  plaza:      ['#4da86a', '#b8d87a'],
  bakery:     ['#d97a3a', '#f5d87a'],
  smithy:     ['#5a5a62', '#8a8070'],
  riverside:  ['#3a7ad9', '#7ac8f5'],
  elderHouse: ['#5a3a8a', '#8a7ac8'],
}

export default function SceneScreen() {
  const nav = useNavigation<Nav>()
  const { params } = useRoute<Route>()
  const [npcs, setNpcs] = useState<NPC[]>([])

  useEffect(() => {
    loadState().then((s: VillageState) => {
      setNpcs(s.npcs.filter((n) => n.location === params.location))
    })
  }, [params.location])

  const [top, bottom] = SCENE_BG[params.location] ?? ['#4a4a6a', '#7a7a9a']

  return (
    <SafeAreaView style={[styles.root, { backgroundColor: top }]}>
      <View style={[styles.sky, { backgroundColor: top }]} />
      <View style={[styles.ground, { backgroundColor: bottom }]}>
        <View style={styles.npcRow}>
          {npcs.map((npc) => (
            <TouchableOpacity
              key={npc.id}
              style={styles.npcWrap}
              onPress={() => nav.navigate('Conversation', { npcId: npc.id })}
            >
              {npc.wantsToTalk && <Text style={styles.bubble}>💬</Text>}
              <View style={styles.avatar}>
                <Text style={styles.avatarEmoji}>{npc.avatarEmoji}</Text>
              </View>
              <Text style={styles.npcName}>{npc.name}</Text>
            </TouchableOpacity>
          ))}
          {npcs.length === 0 && (
            <Text style={styles.empty}>誰もいない</Text>
          )}
        </View>
      </View>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  root: { flex: 1 },
  sky: { flex: 1 },
  ground: {
    height: 220, borderTopLeftRadius: 32, borderTopRightRadius: 32,
    alignItems: 'center', justifyContent: 'center',
  },
  npcRow: { flexDirection: 'row', gap: 28, alignItems: 'flex-end', paddingBottom: 24 },
  npcWrap: { alignItems: 'center' },
  bubble: { fontSize: 20, marginBottom: -8, zIndex: 1 },
  avatar: {
    width: 76, height: 76, borderRadius: 38,
    backgroundColor: 'rgba(255,255,255,0.92)',
    alignItems: 'center', justifyContent: 'center',
    shadowColor: '#000', shadowOffset: { width: 0, height: 4 },
    shadowOpacity: 0.15, shadowRadius: 8, elevation: 6,
  },
  avatarEmoji: { fontSize: 38 },
  npcName: {
    marginTop: 6, fontSize: 13, fontWeight: '600', color: '#fff',
    textShadowColor: 'rgba(0,0,0,0.4)', textShadowOffset: { width: 0, height: 1 }, textShadowRadius: 3,
  },
  empty: { color: 'rgba(255,255,255,0.6)', fontSize: 15 },
})
