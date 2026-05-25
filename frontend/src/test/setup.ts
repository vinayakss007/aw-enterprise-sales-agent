/**
 * Vitest setup — extends ``expect`` with @testing-library/jest-dom matchers
 * and stubs out a couple of jsdom-unfriendly browser APIs.
 */
import '@testing-library/jest-dom/vitest';

// Avoid pulling in real intersection-observer in tests.
class IntersectionObserverStub {
  observe(): void {}
  unobserve(): void {}
  disconnect(): void {}
  takeRecords(): IntersectionObserverEntry[] {
    return [];
  }
}
// @ts-expect-error — overriding for jsdom
globalThis.IntersectionObserver = IntersectionObserverStub;
