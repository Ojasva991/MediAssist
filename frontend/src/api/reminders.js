import { apiClient } from "./client";

export async function getReminders({ includeInactive = false } = {}) {
  const { data } = await apiClient.get("/reminders", {
    params: { include_inactive: includeInactive },
  });
  return data;
}

export async function createReminder({ title, notes, category, remindAt, repeatEveryDays }) {
  const { data } = await apiClient.post("/reminders", {
    title,
    notes: notes || null,
    category,
    remind_at: remindAt,
    repeat_every_days: repeatEveryDays ?? null,
  });
  return data;
}

export async function completeReminder(id) {
  const { data } = await apiClient.post(`/reminders/${id}/complete`);
  return data;
}

export async function deleteReminder(id) {
  await apiClient.delete(`/reminders/${id}`);
}
