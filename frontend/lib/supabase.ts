/**
 * frontend/lib/supabase.ts
 * ========================
 * PURPOSE:
 *   Creates and exports the Supabase JavaScript client for use in the
 *   Next.js frontend. Used for optional direct Realtime subscriptions
 *   (e.g., listening to DB changes without going through FastAPI).
 *
 * ARCHITECTURE ROLE:
 *   Sits alongside lib/api.ts. While api.ts wraps FastAPI REST calls,
 *   this file gives the frontend direct Supabase access for Realtime.
 *   For example, the frontend could subscribe directly to INSERT events
 *   on the transactions table instead of relying solely on FastAPI WebSocket.
 *
 * DESIGN DECISION — Public Anon Key:
 *   The NEXT_PUBLIC_SUPABASE_ANON_KEY is intentionally exposed in the browser.
 *   This is Supabase's design — the anon key has LIMITED permissions by default.
 *   Row Level Security (RLS) policies on the Supabase side control what data
 *   this key can read/write. The key itself is not a secret.
 *   See: https://supabase.com/docs/guides/api/api-keys
 */

// createClient: factory function from @supabase/supabase-js that returns
// a fully configured Supabase client with REST, Realtime, Auth, and Storage APIs.
import { createClient } from '@supabase/supabase-js';

// Read Supabase credentials from Next.js environment variables.
// NEXT_PUBLIC_ prefix makes these available in the browser bundle.
// Without NEXT_PUBLIC_, the variable is only available in server-side code.
const supabaseUrl = process.env.NEXT_PUBLIC_SUPABASE_URL!;
const supabaseAnonKey = process.env.NEXT_PUBLIC_SUPABASE_ANON_KEY!;

// Validate at module load time — fail fast with a clear error if misconfigured
if (!supabaseUrl || !supabaseAnonKey) {
  console.error(
    '❌ Missing Supabase environment variables.\n' +
    'Copy frontend/.env.local.example to frontend/.env.local and fill in your values.'
  );
}

// Create and export the Supabase client singleton.
// createClient initialises the HTTP client — no persistent connection is opened
// until you subscribe to Realtime channels or make an API call.
export const supabase = createClient(supabaseUrl, supabaseAnonKey);
