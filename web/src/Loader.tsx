// Boot + render progress overlay (the vanilla player's #loader, reused for the
// offline render's progress like the original did).
export default function Loader({
  show,
  message,
  pct,
  title = 'toaster-strudel',
}: {
  show: boolean;
  message: string;
  pct: number;
  title?: string;
}) {
  if (!show) return null;
  return (
    <div className="loader">
      <div className="loader-ring" />
      <div className="loader-text">
        <div className="loader-title">{title}</div>
        <div className="loader-step">{message}</div>
        <div className="loader-bar">
          <div className="loader-bar-fill" style={{ width: `${pct}%` }} />
        </div>
      </div>
    </div>
  );
}
