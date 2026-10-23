import React from 'react';
export function Badge({ children, tone = 'neutral' }: { children: React.ReactNode; tone?: 'neutral' | 'good' | 'warn' | 'danger' }) {
  return <span className={`sf-badge sf-${tone}`}>{children}</span>;
}
export function Panel({ title, eyebrow, children, className = '' }: { title: string; eyebrow?: string; children: React.ReactNode; className?: string }) {
  return <section className={`sf-panel ${className}`}><div className="sf-panel-heading">{eyebrow && <span className="sf-eyebrow">{eyebrow}</span>}<h2>{title}</h2></div>{children}</section>;
}
export function Metric({ label, value, unit, hint }: { label: string; value: React.ReactNode; unit?: string; hint: string }) {
  return <div className="sf-metric" data-metric={label}><span>{label}</span><strong>{value}<small>{unit}</small></strong><p>{hint}</p></div>;
}
