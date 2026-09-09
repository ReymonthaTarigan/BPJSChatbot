/**
 * client.js
 * Wrapper untuk semua pemanggilan ke backend FastAPI kita.
 * Disatukan di sini supaya kalau nanti base URL berubah (misal saat
 * deploy), cuma perlu ubah 1 tempat.
 */

import axios from "axios";

const API_BASE_URL = "http://localhost:8000";

export async function sendChatMessage(question) {
  const response = await axios.post(`${API_BASE_URL}/chat`, { question });
  return response.data;
}

export async function getStatus() {
  const response = await axios.get(`${API_BASE_URL}/status`);
  return response.data;
}

export async function triggerUpdate() {
  const response = await axios.post(`${API_BASE_URL}/update-data`);
  return response.data;
}