const KEYS: [string, string][] = [
  ['space', 'play / stop'],
  ['← →', 'previous / next track'],
  [', .', 'previous / next section'],
  ['a', 'toggle auto-advance'],
  ['t', 'cycle theme'],
  ['c', 'open chat'],
  ['shift-click', 'send a note to the chat'],
  ['click (stopped)', 'audition a note'],
  ['?', 'this help'],
  ['esc', 'close'],
];

export default function Help({ open, onClose }: { open: boolean; onClose: () => void }) {
  if (!open) return null;
  return (
    <div className="help-overlay" onClick={onClose}>
      <div className="help-card" onClick={(e) => e.stopPropagation()}>
        <header className="help-head">
          <span>keybindings</span>
          <button className="cbtn" onClick={onClose}>
            ×
          </button>
        </header>
        <table>
          <tbody>
            {KEYS.map(([k, d]) => (
              <tr key={k}>
                <td>
                  <kbd>{k}</kbd>
                </td>
                <td>{d}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
