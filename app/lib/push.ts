// Expo 免费推送：拿到 Expo Push Token 后存到 Supabase，
// 由采集器在发现「新的高置信线索」时通过 Expo Push API 推送（全免费，自动处理 APNs/FCM）。
import * as Notifications from "expo-notifications";
import * as Device from "expo-device";
import Constants from "expo-constants";
import { supabase } from "./supabase";

Notifications.setNotificationHandler({
  handleNotification: async () => ({
    shouldShowAlert: true, shouldPlaySound: true, shouldSetBadge: true,
  }),
});

export async function registerForPush(): Promise<string | null> {
  if (!Device.isDevice) return null; // 模拟器收不到推送
  const { status: existing } = await Notifications.getPermissionsAsync();
  let status = existing;
  if (existing !== "granted") {
    status = (await Notifications.requestPermissionsAsync()).status;
  }
  if (status !== "granted") return null;

  const projectId = Constants.expoConfig?.extra?.eas?.projectId;
  const token = (await Notifications.getExpoPushTokenAsync({ projectId })).data;

  // 存到 Supabase 一张 push_tokens 表（自行建：token text primary key）
  await supabase.from("push_tokens").upsert({ token }, { onConflict: "token" });
  return token;
}
