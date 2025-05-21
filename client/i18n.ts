import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';
import * as Localization from 'expo-localization';
import AsyncStorage from '@react-native-async-storage/async-storage';

import en from './locales/en.json';
import fr from './locales/fr.json';

const resources = {
  en: { translation: en },
  fr: { translation: fr },
};

const getStoredLanguage = async () => {
  const storedLang = await AsyncStorage.getItem('language');
  return storedLang || (Localization.locale.startsWith('fr') ? 'fr' : 'en');
};

getStoredLanguage().then((language) => {
  i18n
    .use(initReactI18next)
    .init({
      resources,
      lng: language,
      fallbackLng: 'en',
      compatibilityJSON: 'v4',
      interpolation: { escapeValue: false },
    })
    .then(() => console.log('✅ i18n initialized'))
    .catch((error) => console.error('❌ i18n initialization failed:', error));
});

export default i18n;
