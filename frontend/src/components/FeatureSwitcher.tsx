import { Link } from 'react-router-dom';

interface Props {
  to: string;
  label: string;
  description: string;
  /** Kept for call-site compatibility; the wording carries direction now. */
  direction?: 'next' | 'prev';
}

/**
 * Was a card with a tracked-out "NEXT" eyebrow and a sliding arrow. Both are
 * template chrome, so the sentence does the work instead.
 */
export function FeatureSwitcher({ to, label, description, direction = 'next' }: Props) {
  return (
    <Link
      to={to}
      className="mt-10 block rounded-item border border-rule bg-white p-5 transition-colors hover:border-board focus-visible:border-board"
    >
      <p className="text-small text-muted">
        {direction === 'next' ? 'Carry on to' : 'Go back to'}
      </p>
      <p className="mt-0.5 text-heading text-board">{label}</p>
      <p className="mt-1 text-small text-muted">{description}</p>
    </Link>
  );
}
