import React from 'react'
import { View, Text, TouchableOpacity, StyleSheet, SafeAreaView } from 'react-native'
import { useNavigation, useRoute, RouteProp } from '@react-navigation/native'
import { RootStackParamList } from '../types'

type Route = RouteProp<RootStackParamList, 'MorningSummary'>

export default function MorningSummaryScreen() {
  const nav = useNavigation()
  const { params } = useRoute<Route>()

  return (
    <SafeAreaView style={styles.root}>
      <View style={styles.inner}>
        <View style={styles.top}>
          <Text style={styles.heading}>昨日の村</Text>
          <Text style={styles.subheading}>── 夜明けの語り ──</Text>
        </View>

        <Text style={styles.summary}>{params.summary}</Text>

        <TouchableOpacity style={styles.btn} onPress={() => nav.goBack()}>
          <Text style={styles.btnText}>村へ行く</Text>
        </TouchableOpacity>
      </View>
    </SafeAreaView>
  )
}

const styles = StyleSheet.create({
  root: { flex: 1, backgroundColor: '#12101e' },
  inner: { flex: 1, paddingHorizontal: 32, paddingTop: 60, paddingBottom: 48, justifyContent: 'space-between' },
  top: { alignItems: 'center', gap: 8 },
  heading: { fontSize: 22, fontWeight: '300', color: 'rgba(255,255,255,0.65)', letterSpacing: 3 },
  subheading: { fontSize: 13, color: 'rgba(255,255,255,0.35)', letterSpacing: 1 },
  summary: {
    fontSize: 17, lineHeight: 30, color: 'rgba(255,255,255,0.88)',
    textAlign: 'center', fontWeight: '300',
  },
  btn: {
    paddingVertical: 16, borderRadius: 16,
    borderWidth: 1, borderColor: 'rgba(255,255,255,0.25)',
    backgroundColor: 'rgba(255,255,255,0.10)', alignItems: 'center',
  },
  btnText: { color: '#fff', fontSize: 16, fontWeight: '500', letterSpacing: 1 },
})
