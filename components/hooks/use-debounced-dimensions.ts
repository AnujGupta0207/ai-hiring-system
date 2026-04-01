import { useEffect, useMemo, useState } from "react";

interface Dimensions {
  width: number;
  height: number;
}

function debounce<T extends (...args: any[]) => void>(fn: T, delay = 100): T {
  let timer: NodeJS.Timeout | null = null;

  return ((...args: any[]) => {
    if (timer) clearTimeout(timer);
    timer = setTimeout(() => fn(...args), delay);
  }) as T;
}

export function useDebouncedDimensions(
  target: React.RefObject<HTMLElement>,
  delay = 120
): Dimensions {
  const [dimensions, setDimensions] = useState<Dimensions>({ width: 0, height: 0 });

  const update = useMemo(
    () =>
      debounce(() => {
        const el = target.current;
        if (!el) return;
        const rect = el.getBoundingClientRect();
        setDimensions({ width: Math.round(rect.width), height: Math.round(rect.height) });
      }, delay),
    [target, delay]
  );

  useEffect(() => {
    const el = target.current;
    if (!el) return;

    update();

    const observer = new ResizeObserver(() => update());
    observer.observe(el);

    window.addEventListener("resize", update);

    return () => {
      observer.disconnect();
      window.removeEventListener("resize", update);
    };
  }, [target, update]);

  return dimensions;
}
