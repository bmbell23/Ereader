import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  FlatList,
  StatusBar,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';

function HomeScreen({navigation}) {
  const [localBooks, setLocalBooks] = useState([]);

  useEffect(() => {
    loadLocalBooks();
  }, []);

  const loadLocalBooks = async () => {
    try {
      const booksJson = await AsyncStorage.getItem('local_books');
      if (booksJson) {
        setLocalBooks(JSON.parse(booksJson));
      }
    } catch (error) {
      console.error('Error loading local books:', error);
    }
  };

  const openBook = (book) => {
    navigation.navigate('Reader', {book});
  };

  return (
    <View style={styles.container}>
      <StatusBar barStyle="light-content" backgroundColor="#1a1a1a" />
      
      <View style={styles.buttonContainer}>
        <TouchableOpacity
          style={styles.button}
          onPress={() => navigation.navigate('Library')}>
          <Text style={styles.buttonText}>📚 Browse Server Library</Text>
        </TouchableOpacity>
        
        <TouchableOpacity
          style={styles.button}
          onPress={() => navigation.navigate('Settings')}>
          <Text style={styles.buttonText}>⚙️ Settings</Text>
        </TouchableOpacity>
      </View>

      <View style={styles.section}>
        <Text style={styles.sectionTitle}>Downloaded Books</Text>
        {localBooks.length === 0 ? (
          <Text style={styles.emptyText}>
            No books downloaded yet. Visit the library to download books!
          </Text>
        ) : (
          <FlatList
            data={localBooks}
            keyExtractor={(item) => item.id}
            renderItem={({item}) => (
              <TouchableOpacity
                style={styles.bookItem}
                onPress={() => openBook(item)}>
                <Text style={styles.bookTitle}>{item.title}</Text>
                <Text style={styles.bookFormat}>{item.format}</Text>
              </TouchableOpacity>
            )}
          />
        )}
      </View>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  buttonContainer: {
    padding: 20,
  },
  button: {
    backgroundColor: '#2196F3',
    padding: 20,
    borderRadius: 10,
    marginBottom: 15,
    alignItems: 'center',
  },
  buttonText: {
    color: '#fff',
    fontSize: 18,
    fontWeight: 'bold',
  },
  section: {
    flex: 1,
    padding: 20,
  },
  sectionTitle: {
    color: '#fff',
    fontSize: 20,
    fontWeight: 'bold',
    marginBottom: 15,
  },
  emptyText: {
    color: '#888',
    fontSize: 16,
    textAlign: 'center',
    marginTop: 20,
  },
  bookItem: {
    backgroundColor: '#1e1e1e',
    padding: 15,
    borderRadius: 8,
    marginBottom: 10,
    flexDirection: 'row',
    justifyContent: 'space-between',
    alignItems: 'center',
  },
  bookTitle: {
    color: '#fff',
    fontSize: 16,
    flex: 1,
  },
  bookFormat: {
    color: '#2196F3',
    fontSize: 12,
    fontWeight: 'bold',
  },
});

export default HomeScreen;
