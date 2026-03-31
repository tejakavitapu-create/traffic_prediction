import React, { useState, useEffect } from 'react';
import { View, Text, StyleSheet, ScrollView, Image, ActivityIndicator, Alert, TouchableOpacity } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';

import { API_URL } from '../config';

export default function ModelPerformanceScreen({ navigation }) {
  const [loading, setLoading] = useState(true);
  const [data, setData] = useState(null);
  const apiUrl = API_URL;

  useEffect(() => {
    fetchData();
  }, []);

  const fetchData = async () => {
    setLoading(true);
    try {
      // We will create this API endpoint in the next step
      const response = await fetch(`${apiUrl}/api/model-performance`);
      const json = await response.json();
      if (response.ok) {
        setData(json);
      } else {
        Alert.alert("Error", "Failed to fetch performance data.");
      }
    } catch (error) {
      Alert.alert("Network Error", "Could not connect to the server.");
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <View style={styles.centered}>
        <ActivityIndicator size="large" color="#2563eb" />
        <Text style={styles.loadingText}>Loading Model Performance...</Text>
      </View>
    );
  }

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backButton}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Model Performance</Text>
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.metricsContainer}>
          <View style={styles.metricBox}>
            <Text style={styles.metricLabel}>MAE</Text>
            <Text style={styles.metricValue}>{data?.mae?.toFixed(4)}</Text>
          </View>
          <View style={styles.metricBox}>
            <Text style={styles.metricLabel}>MSE</Text>
            <Text style={styles.metricValue}>{data?.mse?.toFixed(4)}</Text>
          </View>
          <View style={styles.metricBox}>
            <Text style={styles.metricLabel}>R² Score</Text>
            <Text style={styles.metricValue}>{data?.r2?.toFixed(4)}</Text>
          </View>
        </View>

        <Text style={styles.sectionTitle}>Actual vs Predicted</Text>
        {data?.graph1 && (
          <Image 
            source={{ uri: `data:image/png;base64,${data.graph1}` }} 
            style={styles.graphImage} 
            resizeMode="contain"
          />
        )}

        <Text style={styles.sectionTitle}>Residual Plot</Text>
        {data?.graph2 && (
          <Image 
            source={{ uri: `data:image/png;base64,${data.graph2}` }} 
            style={styles.graphImage} 
            resizeMode="contain"
          />
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f8fafc' },
  header: { padding: 16, flexDirection: 'row', alignItems: 'center', backgroundColor: '#fff', elevation: 2 },
  backButton: { fontSize: 16, color: '#2563eb', marginRight: 16 },
  title: { fontSize: 20, fontWeight: 'bold', color: '#0f172a' },
  scrollContent: { padding: 16 },
  centered: { flex: 1, justifyContent: 'center', alignItems: 'center' },
  loadingText: { marginTop: 12, color: '#64748b' },
  metricsContainer: { flexDirection: 'row', justifyContent: 'space-between', marginBottom: 24 },
  metricBox: { backgroundColor: '#fff', padding: 12, borderRadius: 12, width: '31%', alignItems: 'center', elevation: 2 },
  metricLabel: { fontSize: 12, color: '#64748b', fontWeight: 'bold' },
  metricValue: { fontSize: 14, color: '#2563eb', fontWeight: 'bold', marginTop: 4 },
  sectionTitle: { fontSize: 18, fontWeight: 'bold', color: '#1e293b', marginBottom: 12, marginTop: 8 },
  graphImage: { width: '100%', height: 250, backgroundColor: '#fff', borderRadius: 12, marginBottom: 20 }
});
