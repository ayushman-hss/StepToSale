import { useState } from 'react';
import { Copy, Check } from 'lucide-react';

export function WhatsAppPreview({ text }: { text: string }) {
  const [copied, setCopied] = useState(false);

  const copy = async () => {
    await navigator.clipboard.writeText(text);
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  return (
    <div className="rounded-xl border bg-white overflow-hidden">
      <div className="flex items-center justify-between px-4 py-3 border-b">
        <h2 className="text-sm font-medium">WhatsApp summary</h2>
        <button
          onClick={copy}
          className="text-xs inline-flex items-center gap-1 rounded-md border px-2 py-1 hover:bg-slate-50"
        >
          {copied ? <Check className="h-3 w-3" /> : <Copy className="h-3 w-3" />}
          {copied ? 'Copied' : 'Copy'}
        </button>
      </div>
      <div className="p-4 bg-[#e5ddd5]">
        <div className="max-w-md ml-auto rounded-lg bg-[#dcf8c6] p-3 text-sm whitespace-pre-wrap shadow-sm">
          {text}
        </div>
      </div>
    </div>
  );
}