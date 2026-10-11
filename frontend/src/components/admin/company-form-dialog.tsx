/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * CompanyFormDialog
 *
 * One dialog for both creating and editing a company. When `company` is
 * provided it edits; otherwise it creates. The logo is optional and travels as
 * a file (multipart); the password can be generated or typed, and on edit it is
 * optional ("leave blank to keep").
 */
'use client';

import React, { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import type { DateRange } from 'react-day-picker';
import {
  AlertCircle,
  CalendarDays,
  Dices,
  ImageIcon,
  Loader2,
  Plus,
  Save,
  UploadCloud,
  X,
} from 'lucide-react';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from '@/components/ui/dialog';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Calendar } from '@/components/ui/calendar';
import { Popover, PopoverContent, PopoverTrigger } from '@/components/ui/popover';
import { cn } from '@/lib/utils';
import { adminClient } from '@/lib/api/adminClient';
import {
  PAYMENT_STATUS_LABELS,
  type Company,
  type PaymentStatus,
} from '@/types/admin.types';

const STATUS_OPTIONS: PaymentStatus[] = ['pending', 'free_trial', 'paid'];

/** Local date → ISO `YYYY-MM-DD` (no timezone shift). */
function toIsoDate(value: Date): string {
  const y = value.getFullYear();
  const m = String(value.getMonth() + 1).padStart(2, '0');
  const d = String(value.getDate()).padStart(2, '0');
  return `${y}-${m}-${d}`;
}

/** ISO `YYYY-MM-DD` → a local Date (no timezone shift). */
function parseIsoDate(value: string): Date {
  const [y, m, d] = value.split('-').map(Number);
  return new Date(y, (m ?? 1) - 1, d ?? 1);
}

/** Human-readable day, e.g. "15 Jan 2026". */
function formatDisplayDate(value?: Date): string {
  return value
    ? value.toLocaleDateString('en-GB', { day: '2-digit', month: 'short', year: 'numeric' })
    : '';
}

/** A strong random password the Developer can hand to the company. */
function generatePassword(length = 16): string {
  const alphabet =
    'ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz23456789@#$%&*';
  const bytes = new Uint32Array(length);
  crypto.getRandomValues(bytes);
  return Array.from(bytes, (b) => alphabet[b % alphabet.length]).join('');
}

interface CompanyFormDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  token: string;
  /** When set, the dialog edits this company; when null it creates a new one. */
  company?: Company | null;
  /** Called after a successful save so the dashboard can refresh its list. */
  onSaved?: () => void;
}

export function CompanyFormDialog({
  open,
  onOpenChange,
  token,
  company = null,
  onSaved,
}: CompanyFormDialogProps) {
  const isCreate = company == null;

  const [name, setName] = useState('');
  const [password, setPassword] = useState('');
  const [price, setPrice] = useState('');
  const [status, setStatus] = useState<PaymentStatus>('pending');
  const [trialRange, setTrialRange] = useState<DateRange | undefined>(undefined);
  const [logo, setLogo] = useState<File | null>(null);
  const [saving, setSaving] = useState(false);
  const [error, setError] = useState<string | null>(null);

  // Reset the working copy whenever the dialog opens for a different target
  // (done during render, before paint, to avoid a cascading effect).
  const [seededFor, setSeededFor] = useState<string | null>(null);
  const seedKey = `${open ? 'open' : 'closed'}:${company?.id ?? 'create'}:${company?.updated_at ?? ''}`;
  if (seedKey !== seededFor) {
    setSeededFor(seedKey);
    if (open) {
      setName(company?.name ?? '');
      setPassword('');
      setPrice(company ? String(company.price_rupees) : '');
      setStatus(company?.payment_status ?? 'pending');
      setTrialRange(
        company?.trial_from && company?.trial_to
          ? { from: parseIsoDate(company.trial_from), to: parseIsoDate(company.trial_to) }
          : undefined
      );
      setLogo(null);
      setError(null);
      setSaving(false);
    }
  }

  const onDrop = useCallback((accepted: File[]) => {
    if (accepted.length > 0) {
      setLogo(accepted[0]);
      setError(null);
    }
  }, []);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: {
      'image/png': ['.png'],
      'image/jpeg': ['.jpg', '.jpeg'],
      'image/svg+xml': ['.svg'],
    },
    maxFiles: 1,
    multiple: false,
  });

  const priceValue = price.trim() === '' ? NaN : Number(price);
  const priceValid = Number.isInteger(priceValue) && priceValue >= 0;
  const nameValid = name.trim().length > 0;
  const passwordValid = isCreate ? password.length > 0 : true;
  const trialValid =
    status !== 'free_trial' || (trialRange?.from != null && trialRange?.to != null);
  const canSave = nameValid && priceValid && passwordValid && trialValid && !saving;

  const trialDays =
    trialRange?.from && trialRange?.to
      ? Math.round((trialRange.to.getTime() - trialRange.from.getTime()) / 86_400_000) + 1
      : null;

  const handleSave = async () => {
    if (!nameValid) {
      setError('Company name is required.');
      return;
    }
    if (!priceValid) {
      setError('Enter the price as a whole number of Rupees (0 or more).');
      return;
    }
    if (isCreate && !passwordValid) {
      setError('A company password is required — generate one or type your own.');
      return;
    }
    if (status === 'free_trial' && !(trialRange?.from && trialRange?.to)) {
      setError('Pick a From and To date for the free trial.');
      return;
    }

    setSaving(true);
    setError(null);
    try {
      const payload = {
        name: name.trim(),
        // On edit, an empty field means "keep the existing password".
        password: password || undefined,
        price_rupees: priceValue,
        payment_status: status,
        // The window only travels for a free trial; other statuses leave it be.
        trial_from:
          status === 'free_trial' && trialRange?.from
            ? toIsoDate(trialRange.from)
            : undefined,
        trial_to:
          status === 'free_trial' && trialRange?.to
            ? toIsoDate(trialRange.to)
            : undefined,
        logo: logo ?? undefined,
      };

      if (isCreate) {
        await adminClient.createCompany(token, payload);
      } else {
        await adminClient.updateCompany(token, company.id, payload);
      }

      onSaved?.();
      onOpenChange(false);
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Failed to save the company.');
    } finally {
      setSaving(false);
    }
  };

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[90dvh] overflow-y-auto sm:max-w-lg">
        <DialogHeader>
          <DialogTitle className="flex items-center gap-2">
            {isCreate ? (
              <Plus className="size-4 text-emerald-600 dark:text-emerald-400" />
            ) : (
              <Save className="size-4 text-emerald-600 dark:text-emerald-400" />
            )}
            {isCreate ? 'Add Company' : 'Edit Company'}
          </DialogTitle>
          <DialogDescription>
            {isCreate
              ? 'Register a client company. The password is encrypted before it is stored.'
              : 'Update this company. Leave the password blank to keep the current one.'}
          </DialogDescription>
        </DialogHeader>

        {error && (
          <div className="flex items-center gap-2 rounded-md border border-destructive/30 bg-destructive/5 px-3 py-2 text-xs text-destructive">
            <AlertCircle className="size-4 shrink-0" /> {error}
          </div>
        )}

        <div className="space-y-4">
          {/* Company name */}
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">
              Company Name <span className="text-destructive">*</span>
            </label>
            <Input
              value={name}
              onChange={(e) => setName(e.target.value)}
              placeholder="e.g. Greaves Pakistan"
              className="h-9 text-sm"
              disabled={saving}
            />
          </div>

          {/* Logo */}
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">
              Company Logo <span className="text-muted-foreground">(optional)</span>
            </label>
            <div
              {...getRootProps()}
              className={cn(
                'relative flex min-h-[92px] cursor-pointer flex-col items-center justify-center rounded-lg border-2 border-dashed p-3 text-center transition-all duration-200',
                isDragActive
                  ? 'border-emerald-500 bg-emerald-50 dark:bg-emerald-950/40'
                  : 'border-border bg-background hover:border-emerald-400 hover:bg-muted/50'
              )}
            >
              <input {...getInputProps()} />
              {logo ? (
                <div className="flex items-center gap-3">
                  <ImageIcon className="size-6 text-emerald-600 dark:text-emerald-400" />
                  <div className="text-left">
                    <p className="text-sm font-medium">{logo.name}</p>
                    <p className="text-xs text-muted-foreground">
                      {(logo.size / 1024).toFixed(1)} KB — ready to upload
                    </p>
                  </div>
                  <button
                    type="button"
                    onClick={(e) => {
                      e.stopPropagation();
                      setLogo(null);
                    }}
                    title="Remove logo"
                    className="rounded p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
                  >
                    <X className="size-4" />
                  </button>
                </div>
              ) : (
                <>
                  <UploadCloud className="mb-1 size-6 text-muted-foreground" />
                  <p className="text-xs font-medium">
                    Drop a logo here, or click to browse
                  </p>
                  <p className="text-[11px] text-muted-foreground">
                    PNG, JPG or SVG
                    {!isCreate && company?.logo_url ? ' — a logo is already set' : ''}
                  </p>
                </>
              )}
            </div>
          </div>

          {/* Password */}
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">
              Company Password{' '}
              {isCreate ? (
                <span className="text-destructive">*</span>
              ) : (
                <span className="text-muted-foreground">(leave blank to keep)</span>
              )}
            </label>
            <div className="flex items-center gap-2">
              <Input
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                placeholder={isCreate ? 'Generate or type a password' : 'Unchanged'}
                className="h-9 flex-1 text-sm"
                disabled={saving}
              />
              <Button
                type="button"
                variant="outline"
                size="sm"
                onClick={() => {
                  setPassword(generatePassword());
                  setError(null);
                }}
                disabled={saving}
                title="Generate a random password"
              >
                <Dices className="size-3.5" /> Generate
              </Button>
            </div>
          </div>

          {/* Price */}
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">
              Price (Rupees) <span className="text-destructive">*</span>
            </label>
            <Input
              type="number"
              min={0}
              step={1}
              value={price}
              onChange={(e) => setPrice(e.target.value)}
              placeholder="e.g. 15000"
              className="h-9 text-sm"
              disabled={saving}
            />
          </div>

          {/* Payment status */}
          <div>
            <label className="mb-1 block text-xs font-medium text-muted-foreground">
              Payment Status
            </label>
            <div className="flex h-9 items-center overflow-hidden rounded-md border">
              {STATUS_OPTIONS.map((option) => (
                <button
                  key={option}
                  type="button"
                  onClick={() => setStatus(option)}
                  disabled={saving}
                  className={cn(
                    'flex-1 px-3 py-1.5 text-xs font-medium transition-colors',
                    status === option
                      ? 'bg-emerald-600 text-white'
                      : 'bg-transparent text-muted-foreground hover:bg-muted'
                  )}
                >
                  {PAYMENT_STATUS_LABELS[option]}
                </button>
              ))}
            </div>
          </div>

          {/* Free-trial window — only relevant while the status is Free Trial */}
          {status === 'free_trial' && (
            <div>
              <label className="mb-1 block text-xs font-medium text-muted-foreground">
                Free Trial Period <span className="text-destructive">*</span>
              </label>
              <Popover>
                <PopoverTrigger
                  render={
                    <Button
                      type="button"
                      variant="outline"
                      disabled={saving}
                      className="h-9 w-full justify-start gap-2 text-sm font-normal"
                    />
                  }
                >
                  <CalendarDays className="size-4 text-muted-foreground" />
                  {trialRange?.from ? (
                    trialRange.to ? (
                      <span>
                        {formatDisplayDate(trialRange.from)} → {formatDisplayDate(trialRange.to)}
                      </span>
                    ) : (
                      <span>{formatDisplayDate(trialRange.from)} → …</span>
                    )
                  ) : (
                    <span className="text-muted-foreground">Pick a From and To date</span>
                  )}
                </PopoverTrigger>
                <PopoverContent align="start" className="w-auto p-2">
                  <Calendar
                    mode="range"
                    numberOfMonths={2}
                    defaultMonth={trialRange?.from}
                    selected={trialRange}
                    onSelect={setTrialRange}
                    autoFocus
                  />
                </PopoverContent>
              </Popover>
              <p className="mt-1 text-[11px] text-muted-foreground">
                {trialDays
                  ? `${trialDays} day${trialDays === 1 ? '' : 's'} — employees unlock when the company clicks Start.`
                  : 'Employees unlock only after the company clicks Start.'}
              </p>
            </div>
          )}
        </div>

        <DialogFooter>
          <Button
            type="button"
            variant="outline"
            onClick={() => onOpenChange(false)}
            disabled={saving}
          >
            Cancel
          </Button>
          <Button type="button" onClick={handleSave} disabled={!canSave}>
            {saving ? (
              <>
                <Loader2 className="size-4 animate-spin" /> Saving…
              </>
            ) : (
              <>
                <Save className="size-4" /> {isCreate ? 'Add Company' : 'Save Changes'}
              </>
            )}
          </Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
