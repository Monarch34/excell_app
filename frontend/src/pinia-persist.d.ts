import 'pinia';

declare module 'pinia' {
  export interface DefineSetupStoreOptions<_Id, _SS, _SG, _SA> {
    persist?: import('pinia-plugin-persistedstate').PersistedStateOptions | boolean;
  }
}
