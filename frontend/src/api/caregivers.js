import { apiClient } from "./client";

export async function createInvite() {
  const { data } = await apiClient.post("/caregivers/invite");
  return data;
}

export async function acceptInvite(code) {
  const { data } = await apiClient.post("/caregivers/accept", { code });
  return data;
}

export async function getMyCaregivers() {
  const { data } = await apiClient.get("/caregivers/my-caregivers");
  return data;
}

export async function getMyPatients() {
  const { data } = await apiClient.get("/caregivers/my-patients");
  return data;
}

export async function revokeCaregiverLink(linkId) {
  await apiClient.post(`/caregivers/${linkId}/revoke`);
}

export async function getPatientPassport(patientUserId) {
  const { data } = await apiClient.get(`/caregivers/${patientUserId}/passport`);
  return data;
}

export async function getPatientHistory(patientUserId) {
  const { data } = await apiClient.get(`/caregivers/${patientUserId}/history`);
  return data;
}

export async function getPatientReminders(patientUserId) {
  const { data } = await apiClient.get(`/caregivers/${patientUserId}/reminders`);
  return data;
}

export async function createPatientReminder(patientUserId, payload) {
  const { data } = await apiClient.post(`/caregivers/${patientUserId}/reminders`, payload);
  return data;
}

export async function completePatientReminder(patientUserId, reminderId) {
  const { data } = await apiClient.post(
    `/caregivers/${patientUserId}/reminders/${reminderId}/complete`
  );
  return data;
}

export async function deletePatientReminder(patientUserId, reminderId) {
  await apiClient.delete(`/caregivers/${patientUserId}/reminders/${reminderId}`);
}
