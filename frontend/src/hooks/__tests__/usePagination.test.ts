/**
 * usePagination hook tests.
 */
import { describe, expect, it } from 'vitest';
import { renderHook, act } from '@testing-library/react';

import { usePagination } from '../usePagination';

describe('usePagination', () => {
  it('has correct initial state (page=0, skip=0)', () => {
    const { result } = renderHook(() => usePagination());
    expect(result.current.page).toBe(0);
    expect(result.current.skip).toBe(0);
    expect(result.current.limit).toBe(20);
  });

  it('setPage updates skip correctly', () => {
    const { result } = renderHook(() => usePagination(10));

    act(() => {
      result.current.setPage(3);
    });

    expect(result.current.page).toBe(3);
    expect(result.current.skip).toBe(30); // 3 * 10
  });

  it('hasNext returns true when totalLoaded === limit', () => {
    const { result } = renderHook(() => usePagination(20));

    // When totalLoaded equals the limit, there might be more pages.
    expect(result.current.hasNext(20)).toBe(true);
    // When totalLoaded is less than limit, we're on the last page.
    expect(result.current.hasNext(15)).toBe(false);
  });
});
