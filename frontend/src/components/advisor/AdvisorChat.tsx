'use client';

/**
 # بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ
 * Advisor Chat (Subh al Baqaya — AI Reconciler Advisor, feature 007)
 * Stateless streaming chat (FR-008a): every follow-up re-sends the CURRENT
 * live discrepancy context (reflecting all reconciles applied so far) plus
 * the conversation history, keyed by the reconciliation request_id. No
 * server-side session store exists for the advisor chat. State is
 * component-local (FR-013): resets on new reconciliation / fresh page load.
 */

import { useCallback, useRef, useState } from 'react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Send, Square, Loader2 } from 'lucide-react';
import { runAdvisorReconcile, cancelAdvisorRun } from '@/lib/api/advisorClient';
import type {
  AdvisorDiscrepancy,
  BalanceContext,
  ChatMessage,
} from '@/types/advisor.types';
import type { DiscrepancyTransaction } from '@/types/reconciliation.types';

interface AdvisorChatProps {
  /** Bearer JWT from the NextAuth session (/advisor is NOT auth-exempt). */
  token: string;
  /** The reconciliation request_id — keys the conversation (FR-008a). */
  requestId: string;
  /** The CURRENT live discrepancies (after any reconciles applied). */
  discrepancies: DiscrepancyTransaction[];
  buildDiscrepancies: (items: DiscrepancyTransaction[]) => AdvisorDiscrepancy[];
  buildBalanceContext: (items: DiscrepancyTransaction[]) => BalanceContext;
}

export function AdvisorChat({
  token,
  requestId,
  discrepancies,
  buildDiscrepancies,
  buildBalanceContext,
}: AdvisorChatProps) {
  const [messages, setMessages] = useState<ChatMessage[]>([]);
  const [input, setInput] = useState('');
  const [isStreaming, setIsStreaming] = useState(false);
  const [streamText, setStreamText] = useState('');
  const [chatError, setChatError] = useState<string | null>(null);
  const abortRef = useRef<AbortController | null>(null);

  const handleSend = useCallback(async () => {
    const question = input.trim();
    if (!question || isStreaming) return;

    setInput('');
    setChatError(null);
    const userMessage: ChatMessage = { role: 'user', content: question };
    const nextHistory = [...messages, userMessage];
    setMessages(nextHistory);
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
          history: nextHistory,
          question,
        },
        (delta) => setStreamText((prev) => prev + delta),
        controller.signal
      );
      setMessages((prev) => [
        ...prev,
        { role: 'assistant', content: response.chat_message },
      ]);
      setStreamText('');
    } catch (err) {
      if (err instanceof DOMException && err.name === 'AbortError') {
        setChatError('Response cancelled.');
      } else {
        setChatError(
          err instanceof Error
            ? err.message
            : 'The agent is unable to respond due to a technical failure.'
        );
      }
      setStreamText('');
    } finally {
      setIsStreaming(false);
      abortRef.current = null;
    }
  }, [input, isStreaming, messages, token, requestId, discrepancies, buildDiscrepancies, buildBalanceContext]);

  const handleCancel = useCallback(() => {
    abortRef.current?.abort();
    cancelAdvisorRun(requestId);
    setIsStreaming(false);
  }, [requestId]);

  return (
    <div className="space-y-3">
      <div className="max-h-64 space-y-2 overflow-y-auto pr-1">
        {messages.map((message, index) => (
          <div
            key={index}
            className={
              message.role === 'user'
                ? 'ml-auto max-w-[85%] rounded-lg bg-primary/10 px-3 py-2 text-sm'
                : 'max-w-[85%] rounded-lg bg-muted/40 px-3 py-2 text-sm'
            }
          >
            {message.content}
          </div>
        ))}
        {isStreaming && (
          <div className="flex max-w-[85%] items-start gap-2 rounded-lg bg-muted/40 px-3 py-2 text-sm">
            <Loader2 className="mt-0.5 size-3.5 animate-spin" />
            <span className="whitespace-pre-wrap">{streamText || '…'}</span>
          </div>
        )}
        {messages.length === 0 && !isStreaming && (
          <p className="text-sm text-muted-foreground">
            Ask the agent anything about this reconciliation — it always sees
            the current discrepancies and may additionally return suggestions.
          </p>
        )}
      </div>

      {chatError && (
        <p className="text-sm text-destructive">{chatError}</p>
      )}

      <div className="flex items-center gap-2">
        <Input
          placeholder="Ask the agent about the discrepancies…"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          onKeyDown={(e) => {
            if (e.key === 'Enter' && !e.shiftKey) {
              e.preventDefault();
              handleSend();
            }
          }}
          disabled={isStreaming}
          className="flex-1"
        />
        {isStreaming ? (
          <Button variant="outline" onClick={handleCancel} aria-label="Stop">
            <Square data-icon="inline-start" />
            Stop
          </Button>
        ) : (
          <Button onClick={handleSend} disabled={!input.trim()}>
            <Send data-icon="inline-start" />
            Send
          </Button>
        )}
      </div>
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
