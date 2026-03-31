import React from 'react';
import { View, Text, StyleSheet, TouchableOpacity, ScrollView, ImageBackground, SafeAreaView } from 'react-native';
import { BlurView } from 'expo-blur';

export default function DashboardScreen({ navigation, route }) {
  const user = route.params?.user || { username: 'User', role: 'user' };

  return (
    <ImageBackground 
      source={{ uri: 'https://images.unsplash.com/photo-1542362567-b051c63b9a5c?q=80&w=1470&auto=format&fit=crop' }} 
      style={styles.backgroundImage}
    >
      <SafeAreaView style={styles.container}>
        <View style={styles.topBar}>
           <Text style={styles.topBarTitle}>Machine Learning Dashboard</Text>
           <TouchableOpacity onPress={() => navigation.replace('Login')}>
             <Text style={styles.logoutText}>Logout</Text>
           </TouchableOpacity>
        </View>

        <ScrollView contentContainerStyle={styles.content}>
          <View style={styles.welcomeSection}>
            <Text style={styles.welcomeText}>Welcome <Text style={styles.userName}>{user.username}</Text></Text>
            <View style={styles.divider} />
          </View>

          <View style={styles.grid}>
            <TouchableOpacity 
              style={styles.card} 
              onPress={() => navigation.navigate('TrafficAnalysis')}
            >
              <BlurView intensity={50} tint="dark" style={styles.cardBlur}>
                <Text style={styles.icon}>🚦</Text>
                <Text style={styles.cardTitle}>Traffic Analysis</Text>
                <Text style={styles.cardDesc}>Analyze real-time routes and congestion</Text>
              </BlurView>
            </TouchableOpacity>

            <TouchableOpacity 
              style={styles.card} 
              onPress={() => navigation.navigate('ModelPerformance')}
            >
              <BlurView intensity={50} tint="dark" style={styles.cardBlur}>
                <Text style={styles.icon}>📊</Text>
                <Text style={styles.cardTitle}>Model Metrics</Text>
                <Text style={styles.cardDesc}>Check ML model training performance</Text>
              </BlurView>
            </TouchableOpacity>

            {user.role === 'admin' && (
              <TouchableOpacity style={styles.card}>
                <BlurView intensity={50} tint="dark" style={styles.cardBlur}>
                  <Text style={styles.icon}>👥</Text>
                  <Text style={styles.cardTitle}>Manage Users</Text>
                  <Text style={styles.cardDesc}>Admin panel for user management</Text>
                </BlurView>
              </TouchableOpacity>
            )}

            <TouchableOpacity style={styles.card}>
              <BlurView intensity={50} tint="dark" style={styles.cardBlur}>
                <Text style={styles.icon}>⚙️</Text>
                <Text style={styles.cardTitle}>Settings</Text>
                <Text style={styles.cardDesc}>Configure app and account preferences</Text>
              </BlurView>
            </TouchableOpacity>
          </View>
        </ScrollView>
      </SafeAreaView>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  backgroundImage: { flex: 1, resizeMode: 'cover' },
  container: { flex: 1, backgroundColor: 'rgba(0,0,0,0.3)' },
  topBar: { 
    paddingTop: 50, paddingBottom: 15, paddingHorizontal: 20, 
    backgroundColor: 'rgba(106, 17, 203, 0.85)', flexDirection: 'row', 
    justifyContent: 'space-between', alignItems: 'center' 
  },
  topBarTitle: { color: '#fff', fontSize: 13, fontWeight: 'bold' },
  logoutText: { color: '#fff', fontSize: 13, textDecorationLine: 'underline' },
  content: { padding: 20 },
  welcomeSection: { alignItems: 'center', marginVertical: 40 },
  welcomeText: { fontSize: 32, fontWeight: 'bold', color: '#fff' },
  userName: { color: '#ff6b6b' },
  divider: { width: 60, height: 4, backgroundColor: '#ff6b6b', marginTop: 10, borderRadius: 2 },
  grid: { flexDirection: 'row', flexWrap: 'wrap', justifyContent: 'space-between' },
  card: { width: '47%', height: 160, marginBottom: 20, borderRadius: 15, overflow: 'hidden' },
  cardBlur: { flex: 1, padding: 15, justifyContent: 'center', alignItems: 'center' },
  icon: { fontSize: 30, marginBottom: 10 },
  cardTitle: { color: '#fff', fontSize: 16, fontWeight: 'bold', textAlign: 'center' },
  cardDesc: { color: 'rgba(255,255,255,0.7)', fontSize: 11, textAlign: 'center', marginTop: 5 }
});
