export default function EquityCurveChart({ points }) {
  if (!points?.length || points.length < 2) {
    return <p className="text-sm text-gray-500">暂无收益曲线数据。</p>;
  }

  const width = 760;
  const height = 240;
  const pad = 24;
  const values = points.map((item) => Number(item.value || 0));
  const min = Math.min(...values);
  const max = Math.max(...values);
  const span = max - min || 1;

  const dots = points.map((item, idx) => {
    const x = pad + (idx / (points.length - 1)) * (width - pad * 2);
    const y = height - pad - ((Number(item.value || 0) - min) / span) * (height - pad * 2);
    return { x, y };
  });

  const path = dots.map((dot) => `${dot.x},${dot.y}`).join(' ');

  return (
    <svg viewBox={`0 0 ${width} ${height}`} className="w-full h-56 bg-slate-50 border border-slate-200 rounded-lg">
      <polyline fill="none" stroke="#2563eb" strokeWidth="3" points={path} />
      {dots.map((dot, idx) => (
        <circle key={`${dot.x}-${dot.y}-${idx}`} cx={dot.x} cy={dot.y} r="2.5" fill="#1d4ed8" />
      ))}
    </svg>
  );
}
