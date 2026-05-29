import React, {useState} from 'react';
import {
  View,
  Text,
  StyleSheet,
  TouchableOpacity,
  StatusBar,
  Alert,
} from 'react-native';
import Pdf from 'react-native-pdf';

function ReaderScreen({route, navigation}) {
  const {book} = route.params;
  const [showControls, setShowControls] = useState(true);
  const [currentPage, setCurrentPage] = useState(1);
  const [totalPages, setTotalPages] = useState(0);

  const isPdf = book.format?.toUpperCase() === 'PDF';
  const isEpub = book.format?.toUpperCase() === 'EPUB';

  const toggleControls = () => {
    setShowControls(!showControls);
  };

  if (!book.localPath) {
    return (
      <View style={[styles.container, styles.centered]}>
        <Text style={styles.errorText}>Book file not found</Text>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}>
          <Text style={styles.backButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  if (isPdf) {
    return (
      <View style={styles.container}>
        <StatusBar hidden={!showControls} />
        
        {showControls && (
          <View style={styles.header}>
            <TouchableOpacity onPress={() => navigation.goBack()}>
              <Text style={styles.headerButton}>← Back</Text>
            </TouchableOpacity>
            <Text style={styles.headerTitle} numberOfLines={1}>
              {book.title}
            </Text>
            <Text style={styles.pageInfo}>
              {currentPage}/{totalPages}
            </Text>
          </View>
        )}

        <TouchableOpacity
          style={styles.touchArea}
          activeOpacity={1}
          onPress={toggleControls}>
          <Pdf
            source={{uri: `file://${book.localPath}`}}
            onLoadComplete={(numberOfPages) => {
              setTotalPages(numberOfPages);
            }}
            onPageChanged={(page) => {
              setCurrentPage(page);
            }}
            onError={(error) => {
              console.error(error);
              Alert.alert('Error', 'Failed to load PDF');
            }}
            style={styles.pdf}
            trustAllCerts={false}
            enablePaging={true}
          />
        </TouchableOpacity>
      </View>
    );
  }

  if (isEpub) {
    // For EPUB, we'll use a simpler approach for now
    // In production, you'd use @epubjs-react-native/core
    return (
      <View style={[styles.container, styles.centered]}>
        <Text style={styles.infoText}>
          EPUB reader coming soon!
        </Text>
        <Text style={styles.subText}>
          Currently only PDF is supported.
        </Text>
        <TouchableOpacity
          style={styles.backButton}
          onPress={() => navigation.goBack()}>
          <Text style={styles.backButtonText}>Go Back</Text>
        </TouchableOpacity>
      </View>
    );
  }

  return (
    <View style={[styles.container, styles.centered]}>
      <Text style={styles.errorText}>
        Unsupported format: {book.format}
      </Text>
      <TouchableOpacity
        style={styles.backButton}
        onPress={() => navigation.goBack()}>
        <Text style={styles.backButtonText}>Go Back</Text>
      </TouchableOpacity>
    </View>
  );
}

const styles = StyleSheet.create({
  container: {
    flex: 1,
    backgroundColor: '#000',
  },
  centered: {
    justifyContent: 'center',
    alignItems: 'center',
  },
  header: {
    backgroundColor: '#1a1a1a',
    flexDirection: 'row',
    alignItems: 'center',
    justifyContent: 'space-between',
    padding: 15,
    paddingTop: 40,
  },
  headerButton: {
    color: '#2196F3',
    fontSize: 16,
    fontWeight: 'bold',
  },
  headerTitle: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
    flex: 1,
    marginHorizontal: 15,
  },
  pageInfo: {
    color: '#888',
    fontSize: 14,
  },
  touchArea: {
    flex: 1,
  },
  pdf: {
    flex: 1,
    backgroundColor: '#000',
  },
  errorText: {
    color: '#F44336',
    fontSize: 18,
    marginBottom: 20,
  },
  infoText: {
    color: '#fff',
    fontSize: 18,
    marginBottom: 10,
  },
  subText: {
    color: '#888',
    fontSize: 14,
    marginBottom: 30,
  },
  backButton: {
    backgroundColor: '#2196F3',
    padding: 15,
    borderRadius: 8,
    paddingHorizontal: 30,
  },
  backButtonText: {
    color: '#fff',
    fontSize: 16,
    fontWeight: 'bold',
  },
});

export default ReaderScreen;
