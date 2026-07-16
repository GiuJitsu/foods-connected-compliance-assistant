import { useState, type FormEvent } from "react";

interface BannerProps {
  onSubmit: (task: string) => void;
  busy: boolean;
}

/** ZONE 2: task input, embedded in the big banner. AC1: empty/whitespace-only
 * input is blocked client-side with a visible message, never sent. */
export function Banner({ onSubmit, busy }: BannerProps) {
  const [value, setValue] = useState("");
  const [validationError, setValidationError] = useState<string | null>(null);

  function handleSubmit(event: FormEvent) {
    event.preventDefault();
    if (busy) return;
    const trimmed = value.trim();
    if (!trimmed) {
      setValidationError("Type a question before asking.");
      return;
    }
    setValidationError(null);
    onSubmit(trimmed);
    setValue("");
  }

  return (
    <div className="banner">
      <div className="banner-inner">
        <p className="banner-eyebrow">Foods Connected — Compliance Assistant</p>
        <h1>Ask the compliance assistant.</h1>
        <p className="dek">
          One question about your suppliers, certifications, or specs — every tool the agent calls,
          why it calls it, and exactly how far it gets, shown in full below.
        </p>
        <form className="task-form" onSubmit={handleSubmit} noValidate>
          <input
            type="text"
            value={value}
            onChange={(event) => {
              setValue(event.target.value);
              if (validationError) setValidationError(null);
            }}
            placeholder="e.g. Which dairy suppliers in Italy have an expired certification?"
            aria-label="Ask a compliance question"
            aria-invalid={validationError !== null}
            disabled={busy}
          />
          <button type="submit" disabled={busy}>
            {busy ? "Working…" : "Ask"}
          </button>
        </form>
        {validationError && (
          <p className="field-note" role="alert">
            {validationError}
          </p>
        )}
      </div>
    </div>
  );
}
