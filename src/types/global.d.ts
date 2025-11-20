export {};

declare global {
  interface JsonWebKey {
    [key: string]: unknown;
  }
}
