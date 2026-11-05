import axios from "axios";
import api from "@/api/client";

export function isNotFound(error: unknown): boolean {
  return axios.isAxiosError(error) && error.response?.status === 404;
}

export async function restartScan(scanId: number): Promise<void> {
  await api.post(`/scans/${scanId}/restart/`);
}

export function statusKind(status: string): "completed" | "failed" | "active" {
  if (status === "completed") return "completed";
  if (status === "failed") return "failed";
  return "active";
}
