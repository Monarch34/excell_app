import { defineStore } from 'pinia';
import { ref } from 'vue';

export const usePreferencesStore = defineStore(
  'preferences',
  () => {
    const isDarkMode = ref(true);

    function toggleDarkMode() {
      isDarkMode.value = !isDarkMode.value;
    }

    function setDarkMode(value: boolean) {
      isDarkMode.value = value;
    }

    return {
      isDarkMode,
      toggleDarkMode,
      setDarkMode,
    };
  },
  {
    persist: {
      key: 'excell-preferences',
      pick: ['isDarkMode'],
    },
  }
);
