'use client';

/**
 # بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
 * Advisor Panel (Subh al Baqaya — AI Reconciler Advisor, feature 007)
 * Renders the Reconciler Agent's suggestions in a visually distinct card.
 * Each suggestion shows items grouped under Company/Bank headers with the
 * agent's reason (via tooltip) and a Reconcile button per suggestion.
 * Removal is frontend-only (FR-010) — the agent never removes anything.
 */

import { useMemo } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';
import { Sparkles, CheckCircle2, Info, Wand2 } from 'lucide-react';
import { formatAmount } from '@/lib/utils/categorizationUtils';
import type {
  AdvisorResponse,
  AdvisorSuggestion,
  AdvisorSuggestionItem,
} from '@/types/advisor.types';

interface AdvisorPanelProps {
  /** The agent's typed response (suggestions + chat message). */
  advisorResponse: AdvisorResponse | null;
  /** The current live discrepancy keys — used to hide stale suggestions. */
  liveKeys: Set<string>;
  /** Called when the user approves a suggestion (exact-item frontend removal). */
  onReconcile: (keys: string[]) => void;
  /** True while the agent is running (streaming). */
  isRunning: boolean;
}

function SuggestionItemRow({ item }: { item: AdvisorSuggestionItem }) {
  return (
    <div className="flex items-center justify-between gap-3 rounded-md border border-border/60 bg-muted/30 px-3 py-1.5 text-sm">
      <div className="min-w-0">
        <p className="truncate font-medium">{item.details}</p>
        <p className="text-xs text-muted-foreground">{item.date}</p>
      </div>
      <div className="shrink-0 text-right">
        <p className="font-mono text-sm">{formatAmount(item.debit_credit)}</p>
        <p className="text-xs text-muted-foreground">{item.source}</p>
      </div>
    </div>
  );
}

function SuggestionCard({
  suggestion,
  liveKeys,
  onReconcile,
}: {
  suggestion: AdvisorSuggestion;
  liveKeys: Set<string>;
  onReconcile: (keys: string[]) => void;
}) {
  // Stale-suggestion fallback: resolve keys against the live list; hide any
  // suggestion whose items are gone (already reconciled / refreshed).
  const resolvable = useMemo(
    () => suggestion.keys.every((key) => liveKeys.has(key)),
    [suggestion.keys, liveKeys]
  );

  if (!resolvable) {
    return (
      <Card className="border-dashed">
        <CardContent className="flex items-center gap-2 py-3 text-sm text-muted-foreground">
          <Info className="size-4" />
          These discrepancies were already reconciled.
        </CardContent>
      </Card>
    );
  }

  // Canonical types get their friendly label; custom types the agent returns
  // when the user asks for other reconcilables render as a human-readable title.
  const typeLabel =
    suggestion.type === 'BROKEN_CHEQUE'
      ? 'Broken Cheque / Pair'
      : suggestion.type === 'REVERSAL'
        ? 'Reversal'
        : suggestion.type.replace(/_/g, ' ').toLowerCase().replace(/^\w/, (c) => c.toUpperCase());

  return (
    <Card>
      <CardContent className="space-y-3 py-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex items-center gap-2">
            <Badge variant="secondary">{typeLabel}</Badge>
            <Tooltip>
              <TooltipTrigger aria-label="Reason">
                <Info className="size-4 cursor-help text-muted-foreground" />
              </TooltipTrigger>
              <TooltipContent side="top">{suggestion.reason}</TooltipContent>
            </Tooltip>
          </div>
          <Button
            size="sm"
            onClick={() => onReconcile(suggestion.keys)}
            className="shrink-0"
          >
            <CheckCircle2 data-icon="inline-start" />
            Reconcile
          </Button>
        </div>

        {suggestion.company_items.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Company
            </p>
            {suggestion.company_items.map((item) => (
              <SuggestionItemRow key={item.discrepancy_id} item={item} />
            ))}
          </div>
        )}

        {suggestion.bank_items.length > 0 && (
          <div className="space-y-1.5">
            <p className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              Bank
            </p>
            {suggestion.bank_items.map((item) => (
              <SuggestionItemRow key={item.discrepancy_id} item={item} />
            ))}
          </div>
        )}
      </CardContent>
    </Card>
  );
}

export function AdvisorPanel({
  advisorResponse,
  liveKeys,
  onReconcile,
  isRunning,
}: AdvisorPanelProps) {
  const suggestions = advisorResponse?.suggestions ?? [];

  return (
    <Card className="border-primary/30 bg-gradient-to-br from-card via-card to-primary/5">
      <CardHeader>
        <CardTitle className="flex items-center gap-2">
          <Sparkles className="size-4 text-primary" />
          Agent Suggestions
        </CardTitle>
        <CardDescription>
          The Reconciler Agent&apos;s advisory suggestions — the agent never
          removes anything; you decide with Reconcile.
        </CardDescription>
      </CardHeader>
      <CardContent className="space-y-3">
        {isRunning && (
          <div className="flex items-center gap-2 text-sm text-muted-foreground">
            <Wand2 className="size-4 animate-pulse" />
            The agent is analyzing the discrepancies…
          </div>
        )}

        {!isRunning && advisorResponse && suggestions.length === 0 && (
          <div className="rounded-lg border border-dashed px-4 py-6 text-center text-sm text-muted-foreground">
            The agent found no broken cheques/pairs or reversals in the
            discrepancies list.
          </div>
        )}

        {!isRunning &&
          advisorResponse &&
          suggestions.map((suggestion) => (
            <SuggestionCard
              key={suggestion.keys.join('|')}
              suggestion={suggestion}
              liveKeys={liveKeys}
              onReconcile={onReconcile}
            />
          ))}

        {!isRunning && advisorResponse?.chat_message && (
          <p className="rounded-lg bg-muted/40 px-3 py-2 text-sm text-muted-foreground">
            {advisorResponse.chat_message}
          </p>
        )}
      </CardContent>
    </Card>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
