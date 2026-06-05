import React from 'react';
import { NavigationContainer, DefaultTheme } from '@react-navigation/native';
import { createBottomTabNavigator } from '@react-navigation/bottom-tabs';
import { createNativeStackNavigator } from '@react-navigation/native-stack';
import { Text } from 'react-native';
import HomeScreen from '../screens/HomeScreen';
import DetailScreen from '../screens/DetailScreen';
import PortfolioScreen from '../screens/PortfolioScreen';
import { theme } from '../theme';

const Tab = createBottomTabNavigator();
const Stack = createNativeStackNavigator();

const navTheme = {
  ...DefaultTheme,
  colors: {
    ...DefaultTheme.colors,
    background: theme.background,
    card: theme.surface,
    text: theme.textPrimary,
    border: theme.border,
    primary: theme.primary,
    notification: theme.primary,
  },
};

function TabIcon({ name, color }: { name: string; color: string }) {
  const icons: Record<string, string> = {
    ranking: '📊',
    portfolio: '💼',
  };
  return <Text style={{ fontSize: 22 }}>{icons[name] ?? '●'}</Text>;
}

function HomeStack() {
  return (
    <Stack.Navigator
      screenOptions={{
        headerStyle: { backgroundColor: theme.surface },
        headerTintColor: theme.textPrimary,
        headerTitleStyle: { fontWeight: '700' },
        contentStyle: { backgroundColor: theme.background },
      }}
    >
      <Stack.Screen
        name="Ranking"
        component={HomeScreen}
        options={{ title: '推奨銘柄 TOP10', headerShown: false }}
      />
      <Stack.Screen
        name="Detail"
        component={DetailScreen}
        options={{ title: '銘柄詳細', headerBackTitle: '戻る' }}
      />
    </Stack.Navigator>
  );
}

export default function Navigation() {
  return (
    <NavigationContainer theme={navTheme}>
      <Tab.Navigator
        screenOptions={{
          headerShown: false,
          tabBarStyle: {
            backgroundColor: theme.surface,
            borderTopColor: theme.border,
          },
          tabBarActiveTintColor: theme.primary,
          tabBarInactiveTintColor: theme.textMuted,
          tabBarLabelStyle: { fontSize: 11, fontWeight: '600' },
        }}
      >
        <Tab.Screen
          name="HomeStack"
          component={HomeStack}
          options={{
            tabBarLabel: 'ランキング',
            tabBarIcon: ({ color }) => <TabIcon name="ranking" color={color} />,
          }}
        />
        <Tab.Screen
          name="Portfolio"
          component={PortfolioScreen}
          options={{
            title: 'ポートフォリオ',
            tabBarLabel: 'ポートフォリオ',
            tabBarIcon: ({ color }) => <TabIcon name="portfolio" color={color} />,
            headerShown: true,
            headerStyle: { backgroundColor: theme.surface },
            headerTintColor: theme.textPrimary,
            headerTitleStyle: { fontWeight: '700' },
          }}
        />
      </Tab.Navigator>
    </NavigationContainer>
  );
}
