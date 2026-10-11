'use client';

/**
 # بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
 * Reconciling Assistant (Subh al Baqaya — AI Reconciler Advisor, feature 007;
 * unified into a single collapsible chatbox per the latest specification).
 *
 * One component replaces the former separate "Agent Suggestions" panel and
 * "Ask the Agent" chat. It renders as a single collapsible card headed
 * "Reconciling Assistant" containing:
 *   - the initial turn: the complete discrepancies list plus the agent's
 *     reconcilable suggestions (Company vs Bank, Company vs Company and
 *     Bank vs Bank), each as an actionable card with a Reconcile button;
 *   - a stateless streaming chat (FR-008a): every follow-up re-sends the
 *     CURRENT live discrepancies + history, and any suggestions the agent
 *     returns are surfaced in the SAME actionable cards inline in the feed,
 *     never trapped as plain chat text.
 *
 * The assistant is strictly advisory (FR-005): it never removes anything; the
 * user decides via Reconcile, which removes exactly the suggested items from
 * the live list (frontend-only, FR-010). State is component-local (FR-013) and
 * resets on a new reconciliation / fresh page load.
 */

import { useCallback, useEffect, useMemo, useRef, useState } from 'react';
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Tooltip, TooltipTrigger, TooltipContent } from '@/components/ui/tooltip';
import {
  Sparkles,
  CheckCircle2,
  Info,
  Wand2,
  Send,
  Square,
  Loader2,
  ChevronDown,
  ChevronRight,
} from 'lucide-react';
import { formatAmount } from '@/lib/utils/categorizationUtils';
import { runAdvisorReconcile, cancelAdvisorRun } from '@/lib/api/advisorClient';
import type {
  AdvisorDiscrepancy,
  AdvisorResponse,
  AdvisorSuggestion,
  AdvisorSuggestionItem,
  BalanceContext,
} from '@/types/advisor.types';
import type { DiscrepancyTransaction } from '@/types/reconciliation.types';

interface ReconcilingAssistantProps {
  /** Bearer JWT from the NextAuth session (/advisor is NOT auth-exempt). */
  token: string;
  /** The reconciliation request_id — keys the conversation (FR-008a). */
  requestId: string;
  /** The CURRENT live discrepancies (after any reconciles applied). */
  discrepancies: DiscrepancyTransaction[];
  buildDiscrepancies: (items: DiscrepancyTransaction[]) => AdvisorDiscrepancy[];
  buildBalanceContext: (items: DiscrepancyTransaction[]) => BalanceContext;
  /** The current live discrepancy keys — used to hide stale suggestions. */
  liveKeys: Set<string>;
  /** Called when the user approves a suggestion (exact-item frontend removal). */
  onReconcile: (keys: string[]) => void;
  /** The agent's typed response from the "Reconcile With Agent" run. */
  advisorResponse: AdvisorResponse | null;
  /** True while the initial "Reconcile With Agent" run is streaming. */
  isRunning: boolean;
}

/** One rendered turn in the assistant feed. */
interface AssistantTurn {
  id: number;
  role: 'user' | 'assistant';
  content: string;
  /** Suggestion cards carried by this assistant turn. */
  suggestions?: AdvisorSuggestion[];
  /** True for the seeding turn — also renders the full discrepancies list. */
  initial?: boolean;
}

// Module-level monotonic id, clock-seeded so a hot reload can never reuse a
// live feed id (never reset to 0).
let feedSeq = Date.now() * 1000;
const nextFeedId = () => feedSeq++;

function architectureLabel(suggestion: AdvisorSuggestion): string {
  const hasCompany = suggestion.company_items.length > 0;
  const hasBank = suggestion.bank_items.length > 0;
  if (hasCompany && hasBank) return 'Company ↔ Bank';
  if (hasCompany) return 'Company ↔ Company';
  return 'Bank ↔ Bank';
}

function typeLabel(type: string): string {
  switch (type) {
    case 'BROKEN_CHEQUE':
      return 'Broken Cheque / Pair';
    case 'REVERSAL':
      return 'Reversal';
    case 'CROSS_SIDE_PAIR':
      return 'Cross-side Pair';
    case 'COMPANY_PAIR':
      return 'Company Pair';
    case 'BANK_PAIR':
      return 'Bank Pair';
    default:
      return type.replace(/_/g, ' ').toLowerCase().replace(/^\w/, (c) => c.toUpperCase());
  }
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

  return (
    <Card>
      <CardContent className="space-y-3 py-4">
        <div className="flex items-center justify-between gap-3">
          <div className="flex flex-wrap items-center gap-2">
            <Badge variant="secondary">{architectureLabel(suggestion)}</Badge>
            <Badge variant="outline">{typeLabel(suggestion.type)}</Badge>
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

export function ReconcilingAssistant({
  token,
  requestId,
  discrepancies,
  buildDiscrepancies,
  buildBalanceContext,
  liveKeys,
  onReconcile,
  advisorResponse,
  isRunning,
}: ReconcilingAssistantProps) {
  const [collapsed, setCollapsed] = useState(false);
  const [feed, setFeed] = useState<AssistantTurn[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamText, setStreamText] = useState('');
  const [chatError, setChatError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);
  const seededRef = useRef<AdvisorResponse | null>(null);

  // Seed the feed from the initial "Reconcile With Agent" run; reset it when a
  // fresh run starts (FR-013).
  useEffect(() => {
    if (advisorResponse && advisorResponse !== seededRef.current) {
      seededRef.current = advisorResponse;
      setFeed([
        {
          id: nextFeedId(),
          role: 'assistant',
          content: advisorResponse.chat_message,
          suggestions: advisorResponse.suggestions,
          initial: true,
        },
      ]);
      setInput('');
      setStreamText('');
      setChatError(null);
    } else if (!advisorResponse && isRunning) {
      seededRef.current = null;
      setFeed([]);
      setInput('');
      setStreamText('');
      setChatError(null);
    }
  }, [advisorResponse, isRunning]);

  const handleSend = useCallback(async () => {
    const question = input.trim();
    if (!question || isStreaming || isRunning) return;

    setInput('');
    setChatError(null);
    const userTurn: AssistantTurn = { id: nextFeedId(), role: 'user', content: question };
    const nextFeed = [...feed, userTurn];
    setFeed(nextFeed);
    setIsStreaming(true);
    setStreamText('');

    const controller = new AbortController();
    abortRef.current = controller;

    try {
      const response = await runAdvisorReconcile(
        token,
        {
          request_id: requestId,
          // Re-send the CURRENT live discrepancies + balance context in full
          // (FR-008a) — the agent treats the latest provided context as
          // authoritative.
          discrepancies: buildDiscrepancies(discrepancies),
          context: buildBalanceContext(discrepancies),
          history: nextFeed.map((turn) => ({ role: turn.role, content: turn.content })),
          question,
        },
        (delta) => setStreamText((prev) => prev + delta),
        controller.signal
      );
      setFeed((prev) => [
        ...prev,
        {
          id: nextFeedId(),
          role: 'assistant',
          content: response.chat_message,
          suggestions: response.suggestions,
        },
      ]);
      setStreamText('');
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        setChatError('Response cancelled.');
      } else {
        setChatError(
          err instanceof Error
            ? err.message
            : 'The assistant is unable to respond due to a technical failure.'
        );
      }
      setStreamText('');
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }, [
    input,
    isStreaming,
    isRunning,
    feed,
    token,
    requestId,
    discrepancies,
    buildDiscrepancies,
    buildBalanceContext,
  ]);

  const handleCancel = useCallback(() => {
    abortRef.current?.abort();
    cancelAdvisorRun(requestId);
    setIsStreaming(false);
  }, [requestId]);

  return (
    <Card className="border-primary/30 bg-gradient-to-br from-card via-card to-primary/5">
      <CardHeader>
        <div className="flex flex-wrap items-center justify-between gap-3">
          <div className="flex min-w-0 items-center gap-2">
            <button
              type="button"
              onClick={() => setCollapsed((prev) => !prev)}
              className="rounded-md p-1 text-muted-foreground hover:bg-muted hover:text-foreground"
              aria-label={collapsed ? 'Expand Reconciling Assistant' : 'Collapse Reconciling Assistant'}
            >
              {collapsed ? <ChevronRight className="size-4" /> : <ChevronDown className="size-4" />}
            </button>
            <CardTitle className="flex items-center gap-2">
              <Sparkles className="size-4 text-primary" />
              Reconciling Assistant
            </CardTitle>
          </div>
          {isRunning && (
            <span className="flex items-center gap-2 text-sm text-muted-foreground">
              <Wand2 className="size-4 animate-pulse" />
              Analyzing the discrepancies…
            </span>
          )}
        </div>
        <CardDescription>
          Reviews every discrepancy and suggests reconcilable sets — Company vs
          Bank, Company vs Company and Bank vs Bank. The assistant never removes
          anything; you decide with Reconcile.
        </CardDescription>
      </CardHeader>

      {!collapsed && (
        <CardContent className="space-y-3">
          <div className="max-h-96 space-y-3 overflow-y-auto pr-1">
            {isRunning && feed.length === 0 && (
              <div className="flex items-center gap-2 text-sm text-muted-foreground">
                <Loader2 className="size-4 animate-spin" />
                The assistant is analyzing the discrepancies…
              </div>
            )}

            {feed.map((turn) =>
              turn.role === 'user' ? (
                <div
                  key={turn.id}
                  className="ml-auto max-w-[85%] rounded-lg bg-primary/10 px-3 py-2 text-sm"
                >
                  {turn.content}
                </div>
              ) : (
                <div key={turn.id} className="space-y-3">
                  {turn.content && (
                    <div className="max-w-[85%] whitespace-pre-wrap rounded-lg bg-muted/40 px-3 py-2 text-sm">
                      {turn.content}
                    </div>
                  )}

                  {turn.suggestions && turn.suggestions.length > 0 && (
                    <div className="space-y-3">
                      {turn.suggestions.map((suggestion, index) => (
                        <SuggestionCard
                          key={`${turn.id}-${suggestion.keys.join('|')}-${index}`}
                          suggestion={suggestion}
                          liveKeys={liveKeys}
                          onReconcile={onReconcile}
                        />
                      ))}
                    </div>
                  )}

                  {turn.initial && turn.suggestions && turn.suggestions.length === 0 && (
                    <div className="rounded-lg border border-dashed px-4 py-4 text-center text-sm text-muted-foreground">
                      The assistant found no reconcilable sets in these discrepancies.
                    </div>
                  )}

                  {!turn.initial && turn.suggestions && turn.suggestions.length === 0 && (
                    <p className="text-sm text-muted-foreground">
                      No further reconcilable sets found.
                    </p>
                  )}
                </div>
              )
            )}

            {isStreaming && (
              <div className="flex max-w-[85%] items-start gap-2 rounded-lg bg-muted/40 px-3 py-2 text-sm">
                <Loader2 className="mt-0.5 size-3.5 animate-spin" />
                <span className="whitespace-pre-wrap">{streamText || '…'}</span>
              </div>
            )}
          </div>

          {chatError && <p className="text-sm text-destructive">{chatError}</p>}

          <div className="flex items-center gap-2">
            <Input
              placeholder="Ask the assistant, or request other reconcilables…"
              value={input}
              onChange={(e) => setInput(e.target.value)}
              onKeyDown={(e) => {
                if (e.key === 'Enter' && !e.shiftKey) {
                  e.preventDefault();
                  handleSend();
                }
              }}
              disabled={isStreaming || isRunning}
              className="flex-1"
            />
            {isStreaming ? (
              <Button variant="outline" onClick={handleCancel} aria-label="Stop">
                <Square data-icon="inline-start" />
                Stop
              </Button>
            ) : (
              <Button onClick={handleSend} disabled={!input.trim() || isRunning}>
                <Send data-icon="inline-start" />
                Send
              </Button>
            )}
          </div>
        </CardContent>
      )}
    </Card>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
