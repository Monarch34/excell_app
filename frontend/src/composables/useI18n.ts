import { ref } from 'vue';
import trLocale from '@/locales/tr.json';

type LocalePrimitive = string | number | boolean | null;
type LocaleValue = LocalePrimitive | LocaleObject | LocaleValue[];
interface LocaleObject {
  [key: string]: LocaleValue;
}
type LocaleKey = 'tr' | 'en';

const locales: Record<LocaleKey, LocaleObject> = {
  tr: trLocale as LocaleObject,
  en: {}, // English uses fallback values provided in code
};

const currentLocale = ref<LocaleKey>('tr');

export function useI18n() {
  function t(path: string, defaultValue?: string): string {
    const keys = path.split('.');
    let value: LocaleValue | undefined = locales[currentLocale.value];

    for (const key of keys) {
      if (value && typeof value === 'object' && !Array.isArray(value)) {
        value = value[key];
      } else {
        value = undefined;
        break;
      }
    }

    return typeof value === 'string' ? value : defaultValue ?? path;
  }

  function setLocale(locale: LocaleKey) {
    currentLocale.value = locale;
  }

  return {
    t,
    setLocale,
    currentLocale,
    locales,
  };
}
