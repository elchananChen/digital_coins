import AsyncStorage from '@react-native-async-storage/async-storage';
import * as SecureStore from 'expo-secure-store';
import { Platform } from 'react-native';

const TOKEN_KEY = 'auth_token';

// Helper to check if running on web
const isWeb = Platform.OS === 'web';

export const storeToken = async (token: string) => {
    try {
        if (isWeb) {
            // Token is handled by cookies on web
            return;
        }
        
        if (Platform.OS === 'ios' || Platform.OS === 'android') {
            // Prefer SecureStore on mobile if available (Expo)
            try {
                await SecureStore.setItemAsync(TOKEN_KEY, token);
            } catch {
                // Fallback to AsyncStorage if SecureStore is not available
                await AsyncStorage.setItem(TOKEN_KEY, token);
            }
        }
    } catch (error) {
        console.error('Error storing token:', error);
        throw error;
    }
};

export const getToken = async () => {
    try {
        if (isWeb) {
            return null; // Cookies handle web authentication
        }
        
        if (Platform.OS === 'ios' || Platform.OS === 'android') {
            try {
                return await SecureStore.getItemAsync(TOKEN_KEY);
            } catch {
                return await AsyncStorage.getItem(TOKEN_KEY);
            }
        }
    } catch (error) {
        console.error('Error getting token:', error);
        throw error;
    }
};

export const removeToken = async () => {
    try {
        if (isWeb) {
            return; // Cookies handle web authentication
        }
        
        if (Platform.OS === 'ios' || Platform.OS === 'android') {
            try {
                await SecureStore.deleteItemAsync(TOKEN_KEY);
            } catch {
                await AsyncStorage.removeItem(TOKEN_KEY);
            }
        }
    } catch (error) {
        console.error('Error removing token:', error);
        throw error;
    }
};
