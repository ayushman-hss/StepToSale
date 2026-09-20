import { useState } from 'react';
import { Copy, Check, Send } from 'lucide-react';
import { Button, Section } from '../lib/ui/controls';

/**
 * Previously this imitated WhatsApp's own chrome: a #e5ddd5 wallpaper panel
 * with a #dcf8c6 bubble pinned right by `max-w-md ml-auto`. On a wide screen
 * the bubble capped at 28rem and the leftover width rendered as an empty slab
 * of beige -- the "grey box" bug. It also dragged a second, clashing palette
 * into the app.
 *
 * Now it is a plain message panel in our own system. The width is driven by
 * the content, so there is no leftover area to show through, and WhatsApp is
 * referenced only where it is true: the button that opens it.
 */
export function WhatsAppPreview({
  text,
  phone = '919007572700',
}: {
  text: string;
  phone?: string;
}) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1600);
  };

  const send = () => {
    window.open(
      `https://wa.me/${phone}?text=${encodeURIComponent(text)}`,
      '_blank',
      'noopener',
    );
  };

  return (
    <Section
      flush
      title="Message to send"
      action={
        <div className="flex gap-2">
          <Button variant="secondary" size="sm" onClick={copy}>
            {copied ? <Check size={14} aria-hidden /> : <Copy size={14} aria-hidden />}
            {copied ? 'Copied' : 'Copy'}
          </Button>
          <Button size="sm" onClick={send}>
            <Send size={14} aria-hidden />
            Send on WhatsApp
          </Button>
        </div>
      }
    >
      <div className="p-5 md:p-6">
        <div className="rounded-item border border-rule bg-chalk p-4 text-body whitespace-pre-wrap text-ink">
          {text}
        </div>
        <p className="mt-3 text-small text-muted">
          Today&rsquo;s numbers in plain language, ready to forward to your family or
          staff group.
        </p>
      </div>
    </Section>
  );
}
