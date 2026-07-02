import type {
  ButtonHTMLAttributes,
  InputHTMLAttributes,
  ReactNode,
  SelectHTMLAttributes,
  TextareaHTMLAttributes,
} from 'react'

export function cx(...parts: Array<string | false | null | undefined>): string {
  return parts.filter(Boolean).join(' ')
}

export function Card({ className, children }: { className?: string; children: ReactNode }) {
  return (
    <div className={cx('rounded-xl border border-line bg-card shadow-sm', className)}>
      {children}
    </div>
  )
}

type ButtonProps = ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: 'primary' | 'soft' | 'ghost' | 'danger'
}

export function Button({ variant = 'primary', className, ...props }: ButtonProps) {
  const base =
    'inline-flex items-center justify-center gap-2 rounded-lg px-3.5 py-2 text-sm font-medium transition disabled:opacity-50 disabled:cursor-not-allowed'
  const styles: Record<string, string> = {
    primary: 'bg-accent text-white hover:brightness-95 shadow-sm',
    soft: 'bg-accent-soft text-ink hover:brightness-95',
    ghost: 'text-ink hover:bg-accent-soft/60',
    danger: 'text-danger hover:bg-danger/10',
  }
  return <button className={cx(base, styles[variant], className)} {...props} />
}

export function Badge({ children, className }: { children: ReactNode; className?: string }) {
  return (
    <span
      className={cx(
        'inline-flex items-center rounded-full border border-line bg-paper px-2 py-0.5 text-xs text-muted',
        className,
      )}
    >
      {children}
    </span>
  )
}

export function Input({ className, ...props }: InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cx(
        'w-full rounded-lg border border-line bg-white/70 px-3 py-2 text-sm outline-none focus:border-accent',
        className,
      )}
      {...props}
    />
  )
}

export function Textarea({ className, ...props }: TextareaHTMLAttributes<HTMLTextAreaElement>) {
  return (
    <textarea
      className={cx(
        'w-full rounded-lg border border-line bg-white/70 px-3 py-2 text-sm outline-none focus:border-accent',
        className,
      )}
      {...props}
    />
  )
}

export function Select({ className, ...props }: SelectHTMLAttributes<HTMLSelectElement>) {
  return (
    <select
      className={cx(
        'rounded-lg border border-line bg-white/70 px-3 py-2 text-sm outline-none focus:border-accent',
        className,
      )}
      {...props}
    />
  )
}

export function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="block space-y-1">
      <span className="text-xs font-medium text-muted">{label}</span>
      {children}
    </label>
  )
}

export function Spinner() {
  return (
    <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-accent border-t-transparent" />
  )
}
