/** بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */
import type { NextAuthConfig } from "next-auth";
import Google from "next-auth/providers/google";
import { SignJWT } from "jose";

/**
 * Create a raw HS256 JWT that the backend can verify via PyJWT.
 * Auth.js v5 produces encrypted JWE tokens by default, but the backend's
 * verify_auth_token() expects a plain JWS signed with HS256 using NEXTAUTH_SECRET.
 */
async function createAccessToken(sub: string, email?: string): Promise<string> {
  const secret = new TextEncoder().encode(process.env.AUTH_SECRET!);
  return await new SignJWT({ sub, email })
    .setProtectedHeader({ alg: "HS256" })
    .setExpirationTime("24h")
    .sign(secret);
}

export const authConfig: NextAuthConfig = {
  trustHost: true,
  providers: [Google],
  session: {
    strategy: "jwt",
    maxAge: 24 * 60 * 60,
  },
  pages: {
    signIn: "/",
  },
  callbacks: {
    async jwt({ token, profile }) {
      if (token.sub && !token.access_token) {
        token.access_token = await createAccessToken(token.sub, token.email ?? profile?.email ?? undefined);
      }
      return token;
    },
    async session({ session, token }) {
      if (token.sub) {
        session.user.id = token.sub;
      }
      if (token.access_token) {
        (session.user as { access_token?: string }).access_token =
          token.access_token as string;
      }
      return session;
    },
  },
};
/** وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
