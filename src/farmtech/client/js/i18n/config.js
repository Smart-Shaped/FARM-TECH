import i18n from 'i18next';
import { initReactI18next } from 'react-i18next';

// Import translation files
import indexIT from '../locales/it/index.json';
import indexEN from '../locales/en/index.json';
import researchIT from '../locales/it/research.json';
import researchEN from '../locales/en/research.json';
import inferenceIT from '../locales/it/inference.json';
import inferenceEN from '../locales/en/inference.json';
import uploaderIT from '../locales/it/uploader.json';
import uploaderEN from '../locales/en/uploader.json';
import permissionIT from '../locales/it/permission.json';
import permissionEN from '../locales/en/permission.json';
import loginIT from '../locales/it/login.json';
import loginEN from '../locales/en/login.json';
import registerIT from '../locales/it/register.json';
import registerEN from '../locales/en/register.json';
import changePasswordIT from '../locales/it/changePassword.json';
import changePasswordEN from '../locales/en/changePassword.json';

// Get initial language from Django (via HTML lang attribute or fallback)
const getInitialLanguage = () => {
  // Check Django language passed via global variable
  if (window.DJANGO_LANGUAGE) {
    return window.DJANGO_LANGUAGE.split('-')[0].toLowerCase();
  }

  // Check HTML lang attribute set by Django
  const htmlLang = document.documentElement.lang;
  if (htmlLang) {
    // Convert Django language codes to i18next format
    // Django uses 'it-it', 'en-us', we want 'it', 'en'
    return htmlLang.split('-')[0].toLowerCase();
  }

  // Fallback to browser language
  const browserLang = navigator.language.split('-')[0];
  return browserLang === 'it' || browserLang === 'en' ? browserLang : 'it';
};

// Configure i18next
i18n
  .use(initReactI18next)
  .init({
    resources: {
      it: {
        index: indexIT,
        research: researchIT,
        inference: inferenceIT,
        uploader: uploaderIT,
        permission: permissionIT,
        login: loginIT,
        register: registerIT,
        changePassword: changePasswordIT
      },
      en: {
        index: indexEN,
        research: researchEN,
        inference: inferenceEN,
        uploader: uploaderEN,
        permission: permissionEN,
        login: loginEN,
        register: registerEN,
        changePassword: changePasswordEN
      }
    },
    lng: getInitialLanguage(),
    fallbackLng: 'it',
    defaultNS: 'index',
    interpolation: {
      escapeValue: false // React already escapes values
    },
    react: {
      useSuspense: false // Disable suspense for SSR compatibility
    }
  });

export default i18n;
