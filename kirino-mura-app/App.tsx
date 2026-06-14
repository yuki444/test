import React from 'react'
import { NavigationContainer } from '@react-navigation/native'
import { createStackNavigator } from '@react-navigation/stack'
import { GestureHandlerRootView } from 'react-native-gesture-handler'
import { StyleSheet } from 'react-native'
import VillageMapScreen from './src/screens/VillageMapScreen'
import SceneScreen from './src/screens/SceneScreen'
import ConversationScreen from './src/screens/ConversationScreen'
import MorningSummaryScreen from './src/screens/MorningSummaryScreen'
import { RootStackParamList, LOCATION_LABELS } from './src/types'

const Stack = createStackNavigator<RootStackParamList>()

export default function App() {
  return (
    <GestureHandlerRootView style={styles.flex}>
      <NavigationContainer>
        <Stack.Navigator
          screenOptions={{
            headerStyle: { backgroundColor: 'rgba(100,160,220,0.95)' },
            headerTintColor: '#fff',
            headerTitleStyle: { fontWeight: '300', letterSpacing: 1 },
          }}
        >
          <Stack.Screen
            name="VillageMap"
            component={VillageMapScreen}
            options={{ headerShown: false }}
          />
          <Stack.Screen
            name="Scene"
            component={SceneScreen}
            options={({ route }) => ({ title: LOCATION_LABELS[route.params.location] })}
          />
          <Stack.Screen
            name="Conversation"
            component={ConversationScreen}
            options={{ title: '' }}
          />
          <Stack.Screen
            name="MorningSummary"
            component={MorningSummaryScreen}
            options={{ presentation: 'modal', headerShown: false }}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </GestureHandlerRootView>
  )
}

const styles = StyleSheet.create({ flex: { flex: 1 } })
