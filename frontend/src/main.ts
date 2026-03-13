import { createApp } from 'vue';
import { createPinia } from 'pinia';
import piniaPluginPersistedstate from 'pinia-plugin-persistedstate';
import PrimeVue from 'primevue/config';
import ToastService from 'primevue/toastservice';
import ConfirmationService from 'primevue/confirmationservice';
import Tooltip from 'primevue/tooltip';
import App from './App.vue';
import router from './router';
import { excellThemePreset } from './theme/excellThemePreset';
import { invalidateStorageForSchema } from './utils/storageVersioning';
import { initDerivedColumnLimits } from './stores/derivedColumns';
import { logError, toUserMessage } from './utils/errors';

import 'primeicons/primeicons.css';
import 'primeflex/primeflex.css';
import './ui-foundation/index.css';

const SCHEMA_VERSION = '1.0.0';
invalidateStorageForSchema(SCHEMA_VERSION);

const app = createApp(App);
const pinia = createPinia();

pinia.use(piniaPluginPersistedstate);

app.use(pinia);
// Fetch authoritative limits from backend (e.g. max derived columns) once at startup.
void initDerivedColumnLimits();
app.use(router);
app.use(PrimeVue, {
  theme: {
    preset: excellThemePreset,
    options: {
      prefix: 'p',
      darkModeSelector: '.app-dark',
      cssLayer: false,
    },
  },
});
app.use(ToastService);
app.use(ConfirmationService);
app.directive('tooltip', Tooltip);

app.config.errorHandler = (err, _instance, info) => {
  logError(err, `Vue [${info}]`);
  window.dispatchEvent(
    new CustomEvent('app:unhandled-error', {
      detail: { message: toUserMessage(err) },
    }),
  );
};

if (import.meta.env.DEV) {
  app.config.performance = true;
}

app.mount('#app');
