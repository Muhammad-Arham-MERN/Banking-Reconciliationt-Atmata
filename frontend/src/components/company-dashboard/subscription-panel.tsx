/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * SubscriptionPanel — the company dashboard's Subscription section.
 *
 * A single card inviting the company to start a 30-day free trial. It is
 * deliberately inert (FR-022): billing and payments belong to a later
 * specification, so the card is visible and clickable but does nothing.
 */
'use client';

import { Sparkles } from 'lucide-react';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';

export function SubscriptionPanel() {
  return (
    <div className="max-w-md">
      <Card className="border-dashed">
        <CardHeader>
          <div className="flex items-center gap-2 text-xs font-medium uppercase tracking-wide text-muted-foreground">
            <Sparkles className="size-4" /> Subscription
          </div>
          <CardTitle className="mt-2 text-lg">Start 30 days free trial</CardTitle>
          <CardDescription>
            Unlock the full reconciliation workflow for your whole team.
          </CardDescription>
        </CardHeader>
        <CardContent>
          <p className="text-xs text-muted-foreground">
            Payments open up in a later release — nothing is charged yet.
          </p>
        </CardContent>
      </Card>
    </div>
  );
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
