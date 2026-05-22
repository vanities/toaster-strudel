import { useEffect, useState } from 'react';

const THEMES = ['aurora', 'sunset', 'forest', 'void'] as const;
export type Theme = (typeof THEMES)[number];

export function useTheme() {
  const [idx, setIdx] = useState(() => {
    const saved = localStorage.getItem('theme') as Theme | null;
    const found = saved ? THEMES.indexOf(saved) : -1;
    return found >= 0 ? found : 0;
  });

  useEffect(() => {
    const name = THEMES[idx];
    document.documentElement.setAttribute('data-theme', name);
    localStorage.setItem('theme', name);
  }, [idx]);

  return {
    theme: THEMES[idx],
    cycle: () => setIdx((i) => (i + 1) % THEMES.length),
  };
}
