import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  TextInput,
  StyleSheet,
  TouchableOpacity,
  Alert,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import axios from 'axios';

function SettingsScreen() {
  const [serverUrl, setServerUrl] = useState('');
  const [isConnected, setIsConnected] = useState(false);

  useEffect(() => {
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const savedUrl = await AsyncStorage.getItem('server_url');
      if (savedUrl) {
        setServerUrl(savedUrl);
        testConnection(savedUrl);
      }
    } catch (error) {
      console.error('Error loading settings:', error);
    }
  };

  const saveSettings = async () => {
    try {
      await AsyncStorage.setItem('server_url', serverUrl);
      Alert.alert('Success', 'Settings saved!');
      testConnection(serverUrl);
    } catch (error) {
      Alert.alert('Error', 'Failed to save settings');
    }
  };

  const testConnection = async (url) => {
    try {
      const response = await axios.get(`${url}/api/health`, {timeout: 5000});
      if (response.data.status === 'ok') {
        setIsConnected(true);
        Alert.alert('Connected', 'Successfully connected to server!');
      }
    } catch (error) {
      setIsConnected(false);
      Alert.alert('Connection Failed', 'Could not connect to server');
    }
  };

  return (
    <View style={styles.container}>
      <Text style={styles.label}>Server URL</Text>
      <TextInput
        style={styles.input}
        value={serverUrl}
        onChangeText={setServerUrl}
        placeholder="http://192.168.1.100:5000"
        placeholderTextColor="#666"
        autoCapitalize="none"
        autoCorrect={false}
      />
      
      <View style={styles.statusContainer}>
        <View
          style={[
            styles.statusDot,
            {backgroundColor: isConnected ? '#4CAF50' : '#F44336'},
          ]}
        />
        <Text style={styles.statusText}>
          {isConnected ? 'Connected' : 'Not Connected'}
        </Text>
      </View>

      <TouchableOpacity style={styles.button} onPress={saveSettings}>
        <Text style={styles.buttonText}>Save Settings</Text>
      </TouchableOpacity>

      <TouchableOpacity
        style={[styles.button, styles.testButton]}
        onPress={() => testConnection(serverUrl)}>
        <Text style={styles.buttonText}>Test Connection</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
    padding: 20,
  },
  label: {
    color: '#fff',
    fontSize: 16,
    marginBottom: 10,
    fontWeight: 'bold',
  },
  input: {
    backgroundColor: '#1e1e1e',
    color: '#fff',
    padding: 15,
    borderRadius: 8,
    fontSize: 16,
    marginBottom: 20,
  },
  statusContainer: {
    flexDirection: 'row',
    alignItems: 'center',
    marginBottom: 20,
  },
  statusDot: {
    width: 12,
    height: 12,
    borderRadius: 6,
    marginRight: 10,
  },
  statusText: {
    color: '#fff',
    fontSize: 16,
  },
  button: {
    backgroundColor: '#2196F3',
    padding: 15,
    borderRadius: 8,
    alignItems: 'center',
    marginBottom: 10,
  },
  testButton: {
    backgroundColor: '#4CAF50',
  },
  buttonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default SettingsScreen;
