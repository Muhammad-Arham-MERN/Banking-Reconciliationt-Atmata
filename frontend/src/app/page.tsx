/** بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
import { auth } from "@/lib/auth";
import { redirect } from "next/navigation";

export const dynamic = "force-dynamic";

/**
 * Root route — a pure gate, no UI of its own. Sign-in lives on its own
 * dedicated route (/login); a signed-in user belongs on the subscription page.
 */
export default async function Home() {
  const session = await auth();
  redirect(session ? "/subscription" : "/login");
}
/** وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
