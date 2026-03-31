import React, { useState, useRef, useEffect } from 'react';
import { View, Text, TextInput, StyleSheet, ActivityIndicator, ScrollView, TouchableOpacity, Alert, Dimensions } from 'react-native';
import { SafeAreaView } from 'react-native-safe-area-context';
import { WebView } from 'react-native-webview';
import { API_URL } from '../config';

const { width } = Dimensions.get('window');

const MAP_HTML = `
<!DOCTYPE html>
<html>
<head>
    <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no" />
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        body { margin: 0; padding: 0; }
        #map { height: 100vh; width: 100vw; }
        .leaflet-div-icon { background: transparent; border: none; }
    </style>
</head>
<body>
    <div id="map"></div>
    <script>
        var map = L.map('map', { zoomControl: false }).setView([20, 78], 5);
        L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
            attribution: '© OpenStreetMap'
        }).addTo(map);

        var routeLayer = null;
        var markers = [];

        function clearMap() {
            if (routeLayer) map.removeLayer(routeLayer);
            markers.forEach(m => map.removeLayer(m));
            markers = [];
        }

        const pin = color => L.divIcon({
            html: \`<div style="width:16px;height:16px;background:\${color};border:3px solid white;border-radius:50%;box-shadow:0 2px 8px rgba(0,0,0,.4)"></div>\`,
            iconSize: [16, 16],
            iconAnchor: [8, 8]
        });

        window.drawRoute = function(data, routeIndex) {
            clearMap();
            if (!data || !data.routes || !data.routes[routeIndex]) return;
            
            var route = data.routes[routeIndex];
            var start = data.start;
            var end = data.end;

            // Draw route
            if (route.geometry) {
                routeLayer = L.geoJSON(route.geometry, {
                    style: { color: route.color || '#2563eb', weight: 6, opacity: 0.8 }
                }).addTo(map);
                
                // Fit bounds
                map.fitBounds(routeLayer.getBounds(), { padding: [30, 30] });
            }

            // Draw markers
            var mStart = L.marker([start.lat, start.lon], { icon: pin('#22c55e') }).addTo(map);
            var mEnd = L.marker([end.lat, end.lon], { icon: pin('#ef4444') }).addTo(map);
            markers.push(mStart, mEnd);
        };
    </script>
</body>
</html>
`;

export default function TrafficAnalysisScreen({ navigation }) {
  const [start, setStart] = useState('');
  const [end, setEnd] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState(null);
  const [activeRouteIndex, setActiveRouteIndex] = useState(0);
  const webViewRef = useRef(null);
  const apiUrl = API_URL;

  const handleAnalyze = async () => {
    if (!start || !end) {
      Alert.alert("Notice", "Please enter start and end locations.");
      return;
    }
    setLoading(true);
    setResult(null);

    try {
      const res = await fetch(`${apiUrl}/api/traffic`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ start, end })
      });
      
      const data = await res.json();
      if (res.ok) {
        setResult(data);
        setActiveRouteIndex(0);
        // Inject data into WebView
        const script = `window.drawRoute(${JSON.stringify(data)}, 0);`;
        webViewRef.current?.injectJavaScript(script);
      } else {
        Alert.alert("Error", data.error || "Failed to analyze traffic.");
      }
    } catch (e) {
      Alert.alert("Network Error", `Could not connect to ${apiUrl}.\nDetails: ${e.message}`);
    } finally {
      setLoading(false);
    }
  };

  const handleRouteSwitch = (index) => {
    setActiveRouteIndex(index);
    if (result) {
      const script = `window.drawRoute(${JSON.stringify(result)}, ${index});`;
      webViewRef.current?.injectJavaScript(script);
    }
  };

  return (
    <SafeAreaView style={styles.container}>
      <View style={styles.header}>
        <TouchableOpacity onPress={() => navigation.goBack()}>
          <Text style={styles.backButton}>← Back</Text>
        </TouchableOpacity>
        <Text style={styles.title}>Traffic Analysis</Text>
      </View>

      <View style={styles.mapContainer}>
        <WebView
          ref={webViewRef}
          originWhitelist={['*']}
          source={{ html: MAP_HTML }}
          style={styles.map}
        />
        {loading && (
          <View style={styles.mapLoading}>
            <ActivityIndicator size="large" color="#2563eb" />
          </View>
        )}
      </View>

      <ScrollView contentContainerStyle={styles.scrollContent}>
        <View style={styles.card}>
          <Text style={styles.label}>Start Location:</Text>
          <TextInput 
            style={styles.input} 
            placeholder="e.g. Ameerpet, Hyderabad"
            value={start}
            onChangeText={setStart}
          />
          
          <Text style={styles.label}>End Location:</Text>
          <TextInput 
            style={styles.input} 
            placeholder="e.g. Hitech City, Hyderabad"
            value={end}
            onChangeText={setEnd}
          />

          <TouchableOpacity style={styles.analyzeButton} onPress={handleAnalyze} disabled={loading}>
            {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.buttonText}>Analyze Route</Text>}
          </TouchableOpacity>
        </View>

        {result && (
          <View style={styles.tabsContainer}>
            <ScrollView horizontal showsHorizontalScrollIndicator={false} contentContainerStyle={styles.tabsScroll}>
              {result.routes.map((route, i) => (
                <TouchableOpacity 
                  key={i} 
                  onPress={() => handleRouteSwitch(i)}
                  style={[styles.tab, activeRouteIndex === i ? styles.activeTab : null]}
                >
                  <Text style={[styles.tabText, activeRouteIndex === i ? styles.activeTabText : null]}>
                    {route.label}
                  </Text>
                  <Text style={[styles.tabSub, activeRouteIndex === i ? styles.activeTabSub : null]}>
                    {route.eta_traffic_min} min
                  </Text>
                </TouchableOpacity>
              ))}
            </ScrollView>
          </View>
        )}

        {result && result.routes[activeRouteIndex] && (
          <View style={[styles.card, result.routes[activeRouteIndex].recommended ? styles.recommendedCard : null]}>
            <View style={styles.routeHeader}>
              <Text style={styles.routeLabel}>{result.routes[activeRouteIndex].label}</Text>
              {result.routes[activeRouteIndex].recommended && <Text style={styles.badge}>Best Route</Text>}
            </View>
            
            <View style={styles.statusBox}>
              <Text style={[styles.statusText, { color: result.routes[activeRouteIndex].color || '#f59e0b' }]}>
                Status: {result.routes[activeRouteIndex].status}
              </Text>
              <Text style={styles.descriptionText}>
                {result.routes[activeRouteIndex].description}
              </Text>
            </View>

            <View style={styles.routeDetails}>
              <View style={styles.statBox}>
                <Text style={styles.statLabel}>Distance</Text>
                <Text style={styles.statValue}>{result.routes[activeRouteIndex].distance_km} km</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statLabel}>ETA Traffic</Text>
                <Text style={styles.statValue}>{result.routes[activeRouteIndex].eta_traffic_min} min</Text>
              </View>
              <View style={styles.statBox}>
                <Text style={styles.statLabel}>Avg Speed</Text>
                <Text style={styles.statValue}>{result.routes[activeRouteIndex].avg_speed_kmh} km/h</Text>
              </View>
            </View>
          </View>
        )}
      </ScrollView>
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  container: { flex: 1, backgroundColor: '#f1f5f9' },
  header: { padding: 16, flexDirection: 'row', alignItems: 'center', backgroundColor: '#ffffff', borderBottomWidth: 1, borderBottomColor: '#e2e8f0' },
  backButton: { fontSize: 16, color: '#2563eb', marginRight: 16 },
  title: { fontSize: 20, fontWeight: 'bold', color: '#0f172a' },
  mapContainer: { height: 300, width: '100%', backgroundColor: '#e2e8f0', position: 'relative' },
  map: { flex: 1 },
  mapLoading: { position: 'absolute', inset: 0, justifyContent: 'center', alignItems: 'center', backgroundColor: 'rgba(255,255,255,0.4)' },
  scrollContent: { padding: 16 },
  card: { backgroundColor: '#ffffff', borderRadius: 12, padding: 16, marginBottom: 16, elevation: 1 },
  recommendedCard: { borderColor: '#22c55e', borderWidth: 2 },
  label: { fontSize: 14, fontWeight: '600', color: '#475569', marginBottom: 8, marginTop: 8 },
  input: { backgroundColor: '#f8fafc', borderWidth: 1, borderColor: '#cbd5e1', borderRadius: 8, padding: 12, fontSize: 16 },
  analyzeButton: { backgroundColor: '#e84393', padding: 16, borderRadius: 10, alignItems: 'center', marginTop: 16, shadowColor: '#e84393', shadowOffset: { width: 0, height: 4 }, shadowOpacity: 0.3, shadowRadius: 5, elevation: 5 },
  buttonText: { color: '#ffffff', fontSize: 16, fontWeight: 'bold', textTransform: 'uppercase', letterSpacing: 1 },
  tabsContainer: { marginBottom: 16 },
  tabsScroll: { gap: 10 },
  tab: { backgroundColor: '#fff', paddingHorizontal: 16, paddingVertical: 10, borderRadius: 10, borderWidth: 1, borderColor: '#e2e8f0', minWidth: 100, alignItems: 'center' },
  activeTab: { backgroundColor: '#2563eb', borderColor: '#2563eb' },
  tabText: { fontSize: 14, fontWeight: 'bold', color: '#64748b' },
  activeTabText: { color: '#fff' },
  tabSub: { fontSize: 12, color: '#94a3b8', marginTop: 2 },
  activeTabSub: { color: 'rgba(255,255,255,0.8)' },
  routeHeader: { flexDirection: 'row', justifyContent: 'space-between', alignItems: 'center' },
  routeLabel: { fontSize: 18, fontWeight: 'bold', color: '#1e293b' },
  badge: { backgroundColor: '#22c55e', color: '#fff', fontSize: 12, fontWeight: 'bold', paddingHorizontal: 8, paddingVertical: 4, borderRadius: 12 },
  statusBox: { marginTop: 12 },
  statusText: { fontSize: 16, fontWeight: 'bold' },
  descriptionText: { fontSize: 14, color: '#475569', marginTop: 4 },
  routeDetails: { flexDirection: 'row', justifyContent: 'space-between', marginTop: 16, borderTopWidth: 1, borderTopColor: '#e2e8f0', paddingTop: 16 },
  statBox: { alignItems: 'center' },
  statLabel: { fontSize: 12, color: '#64748b' },
  statValue: { fontSize: 16, fontWeight: 'bold', color: '#0f172a', marginTop: 4 }
});
