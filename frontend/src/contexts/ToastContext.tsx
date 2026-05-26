/**
 * Lightweight toast notification system.
 *
 * Three primitives:
 *   * ``ToastProvider``   — wraps the app, owns the toast queue.
 *   * ``useToast()``      — returns ``{ toast, dismiss }`` for callers.
 *   * ``ToastViewport``   — renders toasts in a fixed-position stack.
 *
 * Each toast auto-dismisses after ``durationMs`` (default 4 s for info /
 * success, 6 s for warning / error). Errors stay on screen longer so the
 * user can read what went wrong before they vanish.
 */
import React, {
  createContext,
  useCallback,
  useContext,
  useMemo,
  useRef,
  useState,
} from 'react';
import type { ReactNode } from 'react';
import {
  CheckCircleIcon,
  ExclamationTriangleIcon,
  InformationCircleIcon,
  XCircleIcon,
  XMarkIcon,
} from '@heroicons/react/24/outline';

export type ToastLevel = 'info' | 'success' | 'warning' | 'error';

export interface Toast {
  id: number;
  message: string;
  level: ToastLevel;
}

interface ToastContextValue {
  toast: (message: string, level?: ToastLevel, durationMs?: number) => number;
  dismiss: (id: number) => void;
}

const ToastContext = createContext<ToastContextValue | undefined>(undefined);

const ICON_FOR_LEVEL: Record<
  ToastLevel,
  React.ComponentType<{ className?: string }>
> = {
  info: InformationCircleIcon,
  success: CheckCircleIcon,
  warning: ExclamationTriangleIcon,
  error: XCircleIcon,
};

const STYLES_FOR_LEVEL: Record<ToastLevel, string> = {
  info: 'bg-blue-50 border-blue-200 text-blue-900',
  success: 'bg-green-50 border-green-200 text-green-900',
  warning: 'bg-yellow-50 border-yellow-200 text-yellow-900',
  error: 'bg-red-50 border-red-200 text-red-900',
};

const DEFAULT_DURATION: Record<ToastLevel, number> = {
  info: 4000,
  success: 4000,
  warning: 6000,
  error: 6000,
};

export const ToastProvider: React.FC<{ children: ReactNode }> = ({ children }) => {
  const [toasts, setToasts] = useState<Toast[]>([]);
  const idCounter = useRef(0);
  const timers = useRef<Map<number, ReturnType<typeof setTimeout>>>(new Map());

  const dismiss = useCallback((id: number) => {
    const timer = timers.current.get(id);
    if (timer) {
      clearTimeout(timer);
      timers.current.delete(id);
    }
    setToasts((current) => current.filter((t) => t.id !== id));
  }, []);

  const toast = useCallback(
    (message: string, level: ToastLevel = 'info', durationMs?: number) => {
      idCounter.current += 1;
      const id = idCounter.current;
      const ttl = durationMs ?? DEFAULT_DURATION[level];
      setToasts((current) => [...current, { id, message, level }]);
      const timer = setTimeout(() => dismiss(id), ttl);
      timers.current.set(id, timer);
      return id;
    },
    [dismiss]
  );

  const value = useMemo<ToastContextValue>(() => ({ toast, dismiss }), [
    toast,
    dismiss,
  ]);

  return (
    <ToastContext.Provider value={value}>
      {children}
      <ToastViewport toasts={toasts} dismiss={dismiss} />
    </ToastContext.Provider>
  );
};

export const ToastViewport: React.FC<{
  toasts: Toast[];
  dismiss: (id: number) => void;
}> = ({ toasts, dismiss }) => (
  <div
    aria-live="polite"
    className="fixed bottom-4 right-4 z-50 flex flex-col space-y-2 max-w-sm pointer-events-none"
  >
    {toasts.map((t) => {
      const Icon = ICON_FOR_LEVEL[t.level];
      return (
        <div
          key={t.id}
          role={t.level === 'error' ? 'alert' : 'status'}
          className={`pointer-events-auto flex items-start space-x-3 rounded-md border px-4 py-3 shadow ${STYLES_FOR_LEVEL[t.level]}`}
        >
          <Icon className="h-5 w-5 flex-shrink-0 mt-0.5" />
          <p className="text-sm flex-1">{t.message}</p>
          <button
            type="button"
            onClick={() => dismiss(t.id)}
            aria-label="Dismiss"
            className="text-gray-500 hover:text-gray-700"
          >
            <XMarkIcon className="h-4 w-4" />
          </button>
        </div>
      );
    })}
  </div>
);

export const useToast = (): ToastContextValue => {
  const ctx = useContext(ToastContext);
  if (!ctx) {
    throw new Error('useToast must be used within a ToastProvider');
  }
  return ctx;
};

export default ToastContext;
