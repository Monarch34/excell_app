/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL?: string;
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}

declare module '*.vue' {
  import type { DefineComponent } from 'vue'
  const component: DefineComponent<Record<string, never>, Record<string, never>, unknown>
  export default component
}

interface PlotlyHTMLElement extends HTMLDivElement {
  on(event: string, callback: (data: unknown) => void): void;
}

declare module 'plotly.js-dist-min' {
  const Plotly: {
    newPlot(
      root: HTMLDivElement,
      data: Array<Record<string, unknown>>,
      layout?: Record<string, unknown>,
      config?: Record<string, unknown>
    ): Promise<void>;
    purge(root: HTMLDivElement): void;
    react(
      root: HTMLDivElement,
      data: Array<Record<string, unknown>>,
      layout?: Record<string, unknown>,
      config?: Record<string, unknown>
    ): Promise<void>;
  };
  export = Plotly;
}
