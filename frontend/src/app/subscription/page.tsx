/** بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";
import { getMembership } from "@/lib/membership";
import { SubscriptionPlans } from "@/components/subscription/subscription-plans";

export const dynamic = "force-dynamic";

/**
 * The post-sign-in landing page. Reachable only while signed in — an
 * unauthenticated visitor is sent back to sign in.
 *
 * An account that already holds a granted membership cannot view this page
 * without first leaving the company (FR-016), so it is redirected back to the
 * application.
 *
 * The package grid is sized to fill most of the viewport rather than sitting
 * as a small block in the middle of an empty page.
 */
export default async function SubscriptionPage() {
  const session = await auth();
  if (!session) redirect("/login");

  const token = (session.user as { access_token?: string } | undefined)?.access_token;
  if (token && (await getMembership(token))) redirect("/upload-ai");

  return (
    <div className="mx-auto w-[85%] max-w-[1500px] px-2 py-10">
      <SubscriptionPlans />
    </div>
  );
}
/** وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
