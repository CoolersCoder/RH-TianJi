import { useEffect, useState, useCallback } from "react";
import { View, Text, FlatList, TouchableOpacity, RefreshControl, StyleSheet } from "react-native";
import { SafeAreaView } from "react-native-safe-area-context";
import { Link } from "expo-router";
import { fetchLeads, type Lead } from "../lib/supabase";

const FILTERS = [
  { label: "全部", industry: undefined as string | undefined, minScore: undefined as number | undefined },
  { label: "高置信", industry: undefined, minScore: 70 },
  { label: "新能源", industry: "新能源", minScore: undefined },
  { label: "新材料", industry: "新材料", minScore: undefined },
];

function scoreColor(s: number) {
  if (s >= 70) return "#dc2626";
  if (s >= 40) return "#f59e0b";
  return "#94a3b8";
}

export default function LeadsScreen() {
  const [leads, setLeads] = useState<Lead[]>([]);
  const [filter, setFilter] = useState(0);
  const [loading, setLoading] = useState(false);

  const load = useCallback(async () => {
    setLoading(true);
    try {
      const f = FILTERS[filter];
      setLeads(await fetchLeads({ industry: f.industry, minScore: f.minScore }));
    } catch (e) {
      console.warn(e);
    } finally {
      setLoading(false);
    }
  }, [filter]);

  useEffect(() => { load(); }, [load]);

  return (
    <SafeAreaView style={styles.safe} edges={["bottom"]}>
      <View style={styles.chips}>
        {FILTERS.map((f, i) => (
          <TouchableOpacity key={f.label} onPress={() => setFilter(i)}
            style={[styles.chip, filter === i && styles.chipOn]}>
            <Text style={[styles.chipText, filter === i && styles.chipTextOn]}>{f.label}</Text>
          </TouchableOpacity>
        ))}
      </View>
      <FlatList
        data={leads}
        keyExtractor={(l) => l.company_key}
        refreshControl={<RefreshControl refreshing={loading} onRefresh={load} />}
        ListEmptyComponent={<Text style={styles.empty}>暂无线索，下拉刷新（采集器每天 09:00 更新）</Text>}
        renderItem={({ item }) => (
          <Link href={{ pathname: "/lead/[id]", params: { id: item.company_key } }} asChild>
            <TouchableOpacity style={styles.card}>
              <View style={[styles.scoreBox, { backgroundColor: scoreColor(item.intent_score) }]}>
                <Text style={styles.score}>{item.intent_score}</Text>
                <Text style={styles.status}>{item.status}</Text>
              </View>
              <View style={styles.info}>
                <Text style={styles.name} numberOfLines={1}>{item.company_name}</Text>
                <Text style={styles.meta}>
                  {[item.top_industry, item.top_location].filter(Boolean).join(" · ") || "—"}
                </Text>
                <Text style={styles.sub}>
                  {item.max_amount_wan ? `投资约 ${(item.max_amount_wan / 10000).toFixed(1)} 亿 · ` : ""}
                  {item.signal_count} 条信号 / {item.distinct_sources} 个独立源
                </Text>
              </View>
            </TouchableOpacity>
          </Link>
        )}
      />
    </SafeAreaView>
  );
}

const styles = StyleSheet.create({
  safe: { flex: 1, backgroundColor: "#f1f5f9" },
  chips: { flexDirection: "row", gap: 8, padding: 12, flexWrap: "wrap" },
  chip: { paddingHorizontal: 14, paddingVertical: 6, borderRadius: 16, backgroundColor: "#e2e8f0" },
  chipOn: { backgroundColor: "#0f172a" },
  chipText: { color: "#334155", fontSize: 13 },
  chipTextOn: { color: "#fff" },
  card: { flexDirection: "row", backgroundColor: "#fff", marginHorizontal: 12, marginVertical: 5,
          borderRadius: 12, overflow: "hidden", elevation: 1 },
  scoreBox: { width: 64, alignItems: "center", justifyContent: "center", paddingVertical: 12 },
  score: { color: "#fff", fontSize: 22, fontWeight: "700" },
  status: { color: "#fff", fontSize: 10, marginTop: 2 },
  info: { flex: 1, padding: 12, justifyContent: "center" },
  name: { fontSize: 15, fontWeight: "600", color: "#0f172a" },
  meta: { fontSize: 13, color: "#475569", marginTop: 3 },
  sub: { fontSize: 12, color: "#94a3b8", marginTop: 3 },
  empty: { textAlign: "center", color: "#94a3b8", marginTop: 48, paddingHorizontal: 24 },
});
