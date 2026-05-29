import React from 'react';
import {NavigationContainer} from '@react-navigation/native';
import {createStackNavigator} from '@react-navigation/stack';
import {GestureHandlerRootView} from 'react-native-gesture-handler';
import {StyleSheet} from 'react-native';

import HomeScreen from './screens/HomeScreen';
import LibraryScreen from './screens/LibraryScreen';
import ReaderScreen from './screens/ReaderScreen';
import SettingsScreen from './screens/SettingsScreen';

const Stack = createStackNavigator();

function App() {
  return (
    <GestureHandlerRootView style={styles.container}>
      <NavigationContainer>
        <Stack.Navigator
          initialRouteName="Home"
          screenOptions={{
            headerStyle: {
              backgroundColor: '#1a1a1a',
            },
            headerTintColor: '#fff',
            headerTitleStyle: {
              fontWeight: 'bold',
            },
          }}>
          <Stack.Screen 
            name="Home" 
            component={HomeScreen}
            options={{title: 'My Ereader'}}
          />
          <Stack.Screen 
            name="Library" 
            component={LibraryScreen}
            options={{title: 'Library'}}
          />
          <Stack.Screen 
            name="Reader" 
            component={ReaderScreen}
            options={{headerShown: false}}
          />
          <Stack.Screen 
            name="Settings" 
            component={SettingsScreen}
            options={{title: 'Settings'}}
          />
        </Stack.Navigator>
      </NavigationContainer>
    </GestureHandlerRootView>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
  },
});

export default App;
