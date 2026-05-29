import React, {useState, useEffect} from 'react';
import {
  View,
  Text,
  StyleSheet,
  FlatList,
  TouchableOpacity,
  Alert,
  ActivityIndicator,
  Image,
} from 'react-native';
import AsyncStorage from '@react-native-async-storage/async-storage';
import RNFS from 'react-native-fs';
import axios from 'axios';

function LibraryScreen({navigation}) {
  const [books, setBooks] = useState([]);
  const [loading, setLoading] = useState(false);
  const [serverUrl, setServerUrl] = useState('');
  const [downloading, setDownloading] = useState({});

  useEffect(() => {
    loadServerUrl();
  }, []);

  const loadServerUrl = async () => {
    const url = await AsyncStorage.getItem('server_url');
    if (url) {
      setServerUrl(url);
      fetchBooks(url);
    } else {
      Alert.alert(
        'No Server Configured',
        'Please set your server URL in Settings first',
        [{text: 'OK', onPress: () => navigation.navigate('Settings')}],
      );
    }
  };

  const fetchBooks = async (url) => {
    setLoading(true);
    try {
      const response = await axios.get(`${url}/api/books`);
      setBooks(response.data.books);
    } catch (error) {
      Alert.alert('Error', 'Failed to fetch books from server');
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const downloadBook = async (book) => {
    setDownloading({...downloading, [book.id]: true});

    try {
      // Use the first available format, or EPUB as default
      const format = book.formats && book.formats.length > 0 ? book.formats[0] : 'epub';
      const downloadUrl = `${serverUrl}/api/books/${book.id}/download?format=${format.toLowerCase()}`;

      // Create a safe filename
      const safeTitle = book.title.replace(/[^a-zA-Z0-9 -]/g, '').trim();
      const filename = `${safeTitle}.${format.toLowerCase()}`;
      const localPath = `${RNFS.DocumentDirectoryPath}/${filename}`;

      await RNFS.downloadFile({
        fromUrl: downloadUrl,
        toFile: localPath,
      }).promise;

      // Save book metadata
      const localBooksJson = await AsyncStorage.getItem('local_books');
      const localBooks = localBooksJson ? JSON.parse(localBooksJson) : [];

      const bookWithPath = {...book, localPath, filename};
      const existingIndex = localBooks.findIndex(b => b.id === book.id);

      if (existingIndex >= 0) {
        localBooks[existingIndex] = bookWithPath;
      } else {
        localBooks.push(bookWithPath);
      }

      await AsyncStorage.setItem('local_books', JSON.stringify(localBooks));

      Alert.alert('Success', `${book.title} downloaded successfully!`);
    } catch (error) {
      Alert.alert('Error', 'Failed to download book');
      console.error(error);
    } finally {
      setDownloading({...downloading, [book.id]: false});
    }
  };

  const formatFileSize = (bytes) => {
    if (bytes < 1024) return bytes + ' B';
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB';
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB';
  };

  if (loading) {
    return (
      <View style={[styles.container, styles.centered]}>
        <ActivityIndicator size="large" color="#2196F3" />
        <Text style={styles.loadingText}>Loading library...</Text>
      </View>
    );
  }

  return (
    <View style={styles.container}>
      <TouchableOpacity
        style={styles.refreshButton}
        onPress={() => fetchBooks(serverUrl)}>
        <Text style={styles.refreshText}>🔄 Refresh</Text>
      </TouchableOpacity>

      <FlatList
        data={books}
        keyExtractor={(item) => item.id}
        renderItem={({item}) => (
          <View style={styles.bookItem}>
            {item.thumbnail && (
              <Image
                source={{uri: item.thumbnail}}
                style={styles.bookCover}
                resizeMode="cover"
              />
            )}
            <View style={styles.bookInfo}>
              <Text style={styles.bookTitle} numberOfLines={2}>
                {item.title}
              </Text>
              {item.author && (
                <Text style={styles.bookAuthor} numberOfLines={1}>
                  {item.author}
                </Text>
              )}
              <Text style={styles.bookMeta}>
                {item.format}
                {item.series && ` • ${item.series}`}
              </Text>
            </View>
            <TouchableOpacity
              style={[
                styles.downloadButton,
                downloading[item.id] && styles.downloadingButton,
              ]}
              onPress={() => downloadBook(item)}
              disabled={downloading[item.id]}>
              <Text style={styles.downloadText}>
                {downloading[item.id] ? '⏳' : '⬇️'}
              </Text>
            </TouchableOpacity>
          </View>
        )}
        ListEmptyComponent={
          <Text style={styles.emptyText}>No books found on server</Text>
        }
      />
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#121212',
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  loadingText: {
    color: '#fff',
    marginTop: 10,
    fontSize: 16,
  },
  refreshButton: {
    backgroundColor: '#1e1e1e',
    padding: 15,
    alignItems: 'center',
  },
  refreshText: {
    color: '#2196F3',
    fontSize: 16,
    fontWeight: 'bold',
  },
  bookItem: {
    backgroundColor: '#1e1e1e',
    padding: 15,
    marginHorizontal: 10,
    marginVertical: 5,
    borderRadius: 8,
    flexDirection: 'row',
    alignItems: 'center',
  },
  bookInfo: {
    flex: 1,
  },
  bookTitle: {
    color: '#fff',
    fontSize: 16,
    marginBottom: 5,
  },
  bookAuthor: {
    color: '#aaa',
    fontSize: 14,
    marginBottom: 4,
  },
  bookMeta: {
    color: '#888',
    fontSize: 12,
  },
  bookCover: {
    width: 60,
    height: 90,
    borderRadius: 4,
    marginRight: 15,
    backgroundColor: '#333',
  },
  downloadButton: {
    backgroundColor: '#2196F3',
    padding: 10,
    borderRadius: 5,
    minWidth: 50,
    alignItems: 'center',
  },
  downloadingButton: {
    backgroundColor: '#666',
  },
  downloadText: {
    fontSize: 20,
  },
  emptyText: {
    color: '#888',
    textAlign: 'center',
    marginTop: 50,
    fontSize: 16,
  },
});

export default LibraryScreen;
