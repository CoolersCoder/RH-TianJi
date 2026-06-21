import { Stack } from "expo-router";
import { StatusBar } from "expo-status-bar";

export default function RootLayout() {
  return (
    <>
      <StatusBar style="dark" />
      <Stack screenOptions={{ headerStyle: { backgroundColor: "#0f172a" }, headerTintColor: "#fff" }}>
        <Stack.Screen name="index" options={{ title: "招商线索 · 长三角" }} />
        <Stack.Screen name="lead/[id]" options={{ title: "线索详情" }} />
      </Stack>
    </>
  );
}
