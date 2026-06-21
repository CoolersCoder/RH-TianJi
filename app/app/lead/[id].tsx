import { useEffect, useState } from "react";
import { View, Text, FlatList, TouchableOpacity, Linking, StyleSheet } from "react-native";
import { useLocalSearchParams } from "expo-router";
import { fetchSignals, type Signal } from "../../lib/supabase";

const SOURCE_LABEL: Record<string, string> = {
  listed_announce: "上市公告",
  invest_record: "投资备案",
  tender: "招标公告",
  news: "新闻",
  qualification: "资质公示",
  gov_project: "政府项目",
};

export default function LeadDetail() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const [signals, setSignals] = useState<Signal[]>([]);

  useEffect(() => {
    if (id) fetchSignals(id).then(setSignals).catch(console.warn);
  }, [id]);

  return (
    <FlatList
      style={styles.list}
      data={signals}
      keyExtractor={(s) => String(s.signal_id)}
      ListHeaderComponent={
        <Text style={styles.header}>{id}</Text>
      }
      ListEmptyComponent={<Text style={styles.empty}>加载中…</Text>}
      renderItem={({ item }) => (
        <TouchableOpacity style={styles.card} onPress={() => item.source_url && Linking.openURL(item.source_url)}>
          <View style={styles.row}>
            <Text style={styles.tag}>{SOURCE_LABEL[item.source_type] ?? item.source_type}</Text>
            {item.event_type ? <Text style={styles.evt}>{item.event_type}</Text> : null}
            <Text style={styles.date}>{item.published_at ?? ""}</Text>
          </View>
          <Text style={styles.title}>{item.title}</Text>
          <Text style={styles.meta}>
            {[item.industry, item.location_city,
              item.amount_wan ? `投资约 ${(item.amount_wan / 10000).toFixed(1)} 亿` : null]
              .filter(Boolean).join(" · ")}
          </Text>
          <Text style={styles.link}>查看原文(证据) →</Text>
        </TouchableOpacity>
      )}
    />
  );
}

const styles = StyleSheet.create({
  list: { flex: 1, backgroundColor: "#f1f5f9" },
  header: { fontSize: 17, fontWeight: "700", color: "#0f172a", padding: 16 },
  card: { backgroundColor: "#fff", marginHorizontal: 12, marginVertical: 5, borderRadius: 12, padding: 14 },
  row: { flexDirection: "row", alignItems: "center", gap: 8, marginBottom: 6 },
  tag: { backgroundColor: "#e0e7ff", color: "#3730a3", fontSize: 11, paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  evt: { backgroundColor: "#fee2e2", color: "#991b1b", fontSize: 11, paddingHorizontal: 8, paddingVertical: 2, borderRadius: 6 },
  date: { marginLeft: "auto", color: "#94a3b8", fontSize: 12 },
  title: { fontSize: 14, color: "#0f172a", lineHeight: 20 },
  meta: { fontSize: 12, color: "#64748b", marginTop: 6 },
  link: { fontSize: 12, color: "#2563eb", marginTop: 8 },
  empty: { textAlign: "center", color: "#94a3b8", marginTop: 48 },
});
