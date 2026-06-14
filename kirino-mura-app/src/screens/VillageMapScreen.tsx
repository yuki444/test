import React, { useEffect, useState, useCallback } from 'react'
import {
  View, Text, TouchableOpacity, StyleSheet, SafeAreaView,
  ScrollView, ActivityIndicator,
} from 'react-native'
import { useNavigation, useFocusEffect } from '@react-navigation/native'
import { StackNavigationProp } from '@react-navigation/stack'
import { RootStackParamList, VillageLocation, LOCATION_LABELS, LOCATION_EMOJI, VillageState } from '../types'
import { loadState, saveState, checkDayAdvance, getMorningSummary } from '../services/GameStateService'

const LOCATIONS: { loc: VillageLocation; x: number; y: number }[] = [
  { loc: 'elderHouse', x: 0.50, y: 0.12 },
  { loc: 'plaza',      x: 0.50, y: 0.35 },
  { loc: 'bakery',     x: 0.20, y: 0.60 },
  { loc: 'smithy',     x: 0.80, y: 0.60 },
  { loc: 'riverside',  x: 0.50, y: 0.80 },
]

type Nav = StackNavigationProp<RootStackParamList, 'VillageMap'>

export default function VillageMapScreen() {
  const nav = useNavigation<Nav>()
  const [state, setState] = useState<VillageState | null>(null)
  const [loading, setLoading] = useState(true)

  useFocusEffect(
    useCallback(() => {
      let active = true
      ;(async () => {
        const loaded = await loadState()
        const { state: advanced, daysElapsed } = checkDayAdvance(loaded)
        if (active) {
          setState(advanced)
          setLoading(false)
          await saveState(advanced)
          if (daysElapsed >= 1) {
            const summary = await getMorningSummary(advanced)
            if (active) nav.navigate('MorningSummary', { summary })
          }
        }
      })()
      return () => { active = false }
    }, [])
  )

  if (loading || !state) {
    return (
      <View style={styles.center}>
        <ActivityIndicator size="large" color="#a0b8e0" />
      </View>
    )
  }

  const { currentSeason, npcs } = state

  return (
    <SafeAreaView style={styles.root}>
      <View style={styles.header}>
        <Text style={styles.title}>霧の村</Text>
        <View style={styles.seasonBadge}>
          <Text style={styles.seasonText}>
            シーズン{currentSeason.number} · {currentSeason.dayNumber}日目
          </Text>
          <View style={styles.progressBar}>
            <View style={[styles.progressFill, { width: `${(currentSeason.dayNumber / currentSeason.totalDays) * 100}%` }]} />
          </View>
        </View>
      </View>

      <View style={styles.mapArea}>
        {LOCATIONS.map(({ loc, x, y }) => {
          const npcsHere = npcs.filter((n) => n.location === loc)
          const hasAlert = npcsHere.some((n) => n.wantsToTalk)
          return (
            <TouchableOpacity
              key={loc}
              style={[styles.pin, { left: `${x * 100}%`, top: `${y * 100}%` }]}
              onPress={() => nav.navigate('Scene', { location: loc })}
            >
              {hasAlert && <View style={styles.alertDot} />}
              <View style={styles.pinBox}>
                <Text style={styles.pinEmoji}>{LOCATION_EMOJI[loc]}</Text>
                <Text style={styles.pinNpcs}>
                  {npcsHere.slice(0, 3).map((n) => n.avatarEmoji).join('')}
                </Text>
              </View>
              <Text style={styles.pinLabel}>{LOCATION_LABELS[loc]}</Text>
            </TouchableOpacity>
          )
        })}
      </View>

      <View style={styles.hint}>
        <Text style={styles.hintText}>{currentSeason.mysteryHint}</Text>
      </View>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#7db8e0' },
  center: { flex: 1, justifyContent: 'center', alignItems: 'center', backgroundColor: '#1a1028' },
  header: {
    flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center',
    paddingHorizontal: 20, paddingTop: 12, paddingBottom: 8,
  },
  title: { fontSize: 22, fontWeight: '300', color: '#fff', letterSpacing: 2 },
  seasonBadge: {
    backgroundColor: 'rgba(0,0,0,0.3)', borderRadius: 10,
    paddingHorizontal: 12, paddingVertical: 6, alignItems: 'flex-end',
  },
  seasonText: { fontSize: 12, color: '#fff', fontWeight: '600' },
  progressBar: { width: 90, height: 3, backgroundColor: 'rgba(255,255,255,0.3)', borderRadius: 2, marginTop: 4 },
  progressFill: { height: 3, backgroundColor: '#fff', borderRadius: 2 },
  mapArea: { flex: 1, position: 'relative' },
  pin: {
    position: 'absolute', alignItems: 'center',
    transform: [{ translateX: -40 }, { translateY: -40 }],
  },
  alertDot: {
    position: 'absolute', right: 2, top: 2, zIndex: 1,
    width: 12, height: 12, borderRadius: 6,
    backgroundColor: '#ff8c42', borderWidth: 2, borderColor: '#fff',
  },
  pinBox: {
    width: 76, height: 64, backgroundColor: 'rgba(255,255,255,0.88)',
    borderRadius: 14, alignItems: 'center', justifyContent: 'center',
    shadowColor: '#000', shadowOffset: { width: 0, height: 3 },
    shadowOpacity: 0.12, shadowRadius: 6, elevation: 4,
  },
  pinEmoji: { fontSize: 26 },
  pinNpcs: { fontSize: 14, marginTop: 2 },
  pinLabel: { fontSize: 11, fontWeight: '700', color: '#fff', marginTop: 4,
    textShadowColor: 'rgba(0,0,0,0.4)', textShadowOffset: { width: 0, height: 1 }, textShadowRadius: 3 },
  hint: { padding: 20, alignItems: 'center' },
  hintText: { fontSize: 13, color: 'rgba(255,255,255,0.75)', textAlign: 'center', fontStyle: 'italic' },
})
