import React, { useState } from 'react';
import { View, Text, TextInput, TouchableOpacity, StyleSheet, ImageBackground, KeyboardAvoidingView, Platform, Alert, ActivityIndicator } from 'react-native';
import { BlurView } from 'expo-blur';
import { API_URL } from '../config';

export default function RegisterScreen({ navigation }) {
  const [username, setUsername] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async () => {
    if (!username || !email || !password) {
      Alert.alert("Error", "Please fill all fields");
      return;
    }

    setLoading(true);
    try {
      const response = await fetch(`${API_URL}/api/register`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username, email, password }),
      });

      const data = await response.json();

      if (response.ok) {
        Alert.alert("Success", "Account created successfully! Please login.");
        navigation.navigate('Login');
      } else {
        Alert.alert("Registration Failed", data.error || "Something went wrong");
      }
    } catch (e) {
      Alert.alert("Error", "Could not connect to the server.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <ImageBackground 
      source={{ uri: 'https://images.unsplash.com/photo-1542362567-b051c63b9a5c?q=80&w=1470&auto=format&fit=crop' }} 
      style={styles.backgroundImage}
    >
      <KeyboardAvoidingView 
        behavior={Platform.OS === "ios" ? "padding" : "height"}
        style={styles.container}
      >
        <View style={styles.topBar}>
           <Text style={styles.topBarTitle}>Method for Scheduling Content Resources</Text>
        </View>

        <View style={styles.formWrapper}>
           <BlurView intensity={60} tint="dark" style={styles.glassCard}>
              <Text style={styles.loginTitle}>Create Account</Text>
              
              <View style={styles.inputContainer}>
                <TextInput
                  style={styles.input}
                  placeholder="Username"
                  placeholderTextColor="#cbd5e1"
                  value={username}
                  onChangeText={setUsername}
                  autoCapitalize="none"
                />
              </View>

              <View style={styles.inputContainer}>
                <TextInput
                  style={styles.input}
                  placeholder="Email"
                  placeholderTextColor="#cbd5e1"
                  value={email}
                  onChangeText={setEmail}
                  keyboardType="email-address"
                  autoCapitalize="none"
                />
              </View>

              <View style={styles.inputContainer}>
                <TextInput
                  style={styles.input}
                  placeholder="Password"
                  placeholderTextColor="#cbd5e1"
                  value={password}
                  onChangeText={setPassword}
                  secureTextEntry
                />
              </View>

              <TouchableOpacity style={styles.loginButton} onPress={handleRegister} disabled={loading}>
                {loading ? <ActivityIndicator color="#fff" /> : <Text style={styles.loginButtonText}>Register</Text>}
              </TouchableOpacity>

              <View style={styles.footer}>
                <Text style={styles.footerText}>Already have an account? </Text>
                <TouchableOpacity onPress={() => navigation.navigate('Login')}>
                  <Text style={styles.linkText}>Login</Text>
                </TouchableOpacity>
              </View>
           </BlurView>
        </View>
      </KeyboardAvoidingView>
    </ImageBackground>
  );
}

const styles = StyleSheet.create({
  backgroundImage: { flex: 1, resizeMode: 'cover' },
  container: { flex: 1 },
  topBar: { 
    paddingTop: 50, paddingBottom: 15, paddingHorizontal: 20, 
    backgroundColor: 'rgba(106, 17, 203, 0.85)', alignItems: 'center' 
  },
  topBarTitle: { color: '#fff', fontSize: 13, fontWeight: 'bold', textAlign: 'center' },
  formWrapper: { flex: 1, justifyContent: 'center', alignItems: 'center', padding: 20 },
  glassCard: { 
    width: '100%', padding: 25, borderRadius: 20, overflow: 'hidden', 
    borderWidth: 1, borderColor: 'rgba(255, 255, 255, 0.2)' 
  },
  loginTitle: { fontSize: 24, fontWeight: 'bold', color: '#fff', textAlign: 'center', marginBottom: 25 },
  inputContainer: { marginBottom: 15 },
  input: { 
    height: 50, borderBottomWidth: 1.5, borderBottomColor: 'rgba(255, 255, 255, 0.5)', 
    fontSize: 16, color: '#fff', paddingHorizontal: 10 
  },
  loginButton: { 
    backgroundColor: '#ff6b6b', height: 50, borderRadius: 25, 
    justifyContent: 'center', alignItems: 'center', marginTop: 15, elevation: 5 
  },
  loginButtonText: { color: '#fff', fontSize: 18, fontWeight: 'bold' },
  footer: { flexDirection: 'row', justifyContent: 'center', marginTop: 20 },
  footerText: { color: '#fff', fontSize: 14 },
  linkText: { color: '#ff6b6b', fontSize: 14, fontWeight: 'bold' },
});
