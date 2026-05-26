/**
 * Toast system component tests.
 */
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { act, render, renderHook, screen } from '@testing-library/react';
import userEvent from '@testing-library/user-event';

import { ToastProvider, useToast } from '../ToastContext';

beforeEach(() => {
  vi.useFakeTimers({ shouldAdvanceTime: true });
});

afterEach(() => {
  vi.useRealTimers();
});

describe('useToast', () => {
  it('throws when called outside the provider', () => {
    expect(() => renderHook(() => useToast())).toThrow(/ToastProvider/);
  });

  it('renders an info toast and auto-dismisses after the default TTL', async () => {
    render(
      <ToastProvider>
        <Trigger />
      </ToastProvider>
    );
    await userEvent.click(screen.getByRole('button', { name: 'Show info' }));
    expect(screen.getByText('hi there')).toBeInTheDocument();

    act(() => {
      vi.advanceTimersByTime(4000);
    });
    expect(screen.queryByText('hi there')).not.toBeInTheDocument();
  });

  it('renders an error toast with role=alert and a longer TTL', async () => {
    render(
      <ToastProvider>
        <Trigger />
      </ToastProvider>
    );
    await userEvent.click(screen.getByRole('button', { name: 'Show error' }));
    const alert = screen.getByRole('alert');
    expect(alert).toHaveTextContent('boom');

    // 4s isn't enough — error TTL is 6s.
    act(() => {
      vi.advanceTimersByTime(4500);
    });
    expect(screen.queryByText('boom')).toBeInTheDocument();
    act(() => {
      vi.advanceTimersByTime(2000);
    });
    expect(screen.queryByText('boom')).not.toBeInTheDocument();
  });

  it('dismiss button removes the toast immediately', async () => {
    render(
      <ToastProvider>
        <Trigger />
      </ToastProvider>
    );
    await userEvent.click(screen.getByRole('button', { name: 'Show info' }));
    expect(screen.getByText('hi there')).toBeInTheDocument();
    await userEvent.click(screen.getByRole('button', { name: 'Dismiss' }));
    expect(screen.queryByText('hi there')).not.toBeInTheDocument();
  });

  it('renders multiple toasts stacked', async () => {
    render(
      <ToastProvider>
        <Trigger />
      </ToastProvider>
    );
    await userEvent.click(screen.getByRole('button', { name: 'Show info' }));
    await userEvent.click(screen.getByRole('button', { name: 'Show error' }));
    expect(screen.getByText('hi there')).toBeInTheDocument();
    expect(screen.getByText('boom')).toBeInTheDocument();
    expect(screen.getAllByRole('button', { name: 'Dismiss' })).toHaveLength(2);
  });

  it('respects an explicit durationMs override', async () => {
    const TestComponent = () => {
      const { toast } = useToast();
      return (
        <button onClick={() => toast('quick', 'info', 1000)}>
          Show 1s toast
        </button>
      );
    };
    render(
      <ToastProvider>
        <TestComponent />
      </ToastProvider>
    );
    await userEvent.click(screen.getByRole('button', { name: 'Show 1s toast' }));
    expect(screen.getByText('quick')).toBeInTheDocument();
    act(() => {
      vi.advanceTimersByTime(1100);
    });
    expect(screen.queryByText('quick')).not.toBeInTheDocument();
  });
});

const Trigger: React.FC = () => {
  const { toast } = useToast();
  return (
    <div>
      <button onClick={() => toast('hi there', 'info')}>Show info</button>
      <button onClick={() => toast('boom', 'error')}>Show error</button>
    </div>
  );
};
