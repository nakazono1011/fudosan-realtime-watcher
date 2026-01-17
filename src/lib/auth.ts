import { betterAuth } from "better-auth";
import { drizzleAdapter } from "better-auth/adapters/drizzle";
import { emailOTP } from "better-auth/plugins";
import { db } from "@/db";
import * as schema from "@/db/schema";
import { Resend } from "resend";

const resend = process.env.RESEND_API_KEY
  ? new Resend(process.env.RESEND_API_KEY)
  : null;

export const auth = betterAuth({
  database: drizzleAdapter(db, {
    provider: "pg",
    schema: {
      user: schema.user,
      session: schema.session,
      account: schema.account,
      verification: schema.verification,
    },
  }),
  emailAndPassword: {
    enabled: false, // We use Email OTP instead
  },
  socialProviders: {
    google: {
      clientId: process.env.GOOGLE_CLIENT_ID || "",
      clientSecret: process.env.GOOGLE_CLIENT_SECRET || "",
    },
  },
  plugins: [
    emailOTP({
      async sendVerificationOTP({ email, otp, type }) {
        if (!resend) {
          console.log(`[DEV] OTP for ${email}: ${otp}`);
          return;
        }

        const subject =
          type === "sign-in"
            ? "ログイン認証コード"
            : type === "email-verification"
              ? "メールアドレス確認コード"
              : "パスワードリセットコード";

        await resend.emails.send({
          from: process.env.RESEND_FROM_EMAIL || "onboarding@resend.dev",
          to: email,
          subject,
          text: `あなたの認証コードは ${otp} です。このコードは10分間有効です。`,
          html: `
            <div style="font-family: sans-serif; max-width: 400px; margin: 0 auto;">
              <h2>${subject}</h2>
              <p>あなたの認証コードは:</p>
              <p style="font-size: 32px; font-weight: bold; letter-spacing: 4px; text-align: center; padding: 20px; background: #f5f5f5; border-radius: 8px;">
                ${otp}
              </p>
              <p style="color: #666; font-size: 14px;">このコードは10分間有効です。</p>
            </div>
          `,
        });
      },
    }),
  ],
});

export type Session = typeof auth.$Infer.Session;
