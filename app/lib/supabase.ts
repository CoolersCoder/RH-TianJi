import { createClient } from "@supabase/supabase-js";
import Constants from "expo-constants";

// 用 anon key（只读，受 RLS 保护）。service_role 密钥绝不进 App。
const url = Constants.expoConfig?.extra?.supabaseUrl as string;
const anonKey = Constants.expoConfig?.extra?.supabaseAnonKey as string;

export const supabase = createClient(url, anonKey, {
  auth: { persistSession: false },
});

export type Lead = {
  company_key: string;
  company_name: string;
  intent_score: number;
  status: string;
  signal_count: number;
  distinct_sources: number;
  top_industry: string | null;
  top_location: string | null;
  max_amount_wan: number | null;
  contact_public: string | null;
  last_active: string | null;
};

export type Signal = {
  signal_id: number;
  source_type: string;
  event_type: string | null;
  title: string | null;
  source_url: string;
  amount_wan: number | null;
  location_city: string | null;
  industry: string | null;
  published_at: string | null;
};

// 线索列表：可按行业/状态过滤，按意向分降序。
export async function fetchLeads(opts: { industry?: string; minScore?: number } = {}) {
  let q = supabase
    .from("leads")
    .select("*")
    .order("intent_score", { ascending: false })
    .limit(100);
  if (opts.industry) q = q.eq("top_industry", opts.industry);
  if (opts.minScore) q = q.gte("intent_score", opts.minScore);
  const { data, error } = await q;
  if (error) throw error;
  return (data ?? []) as Lead[];
}

export async function fetchSignals(companyKey: string) {
  const { data, error } = await supabase
    .from("signals")
    .select("signal_id,source_type,event_type,title,source_url,amount_wan,location_city,industry,published_at")
    .eq("company_key", companyKey)
    .order("published_at", { ascending: false });
  if (error) throw error;
  return (data ?? []) as Signal[];
}
