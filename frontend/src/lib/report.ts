import api from "@/api/client";

/** Download the PDF report for a completed scan (auth header is added by the axios client). */
export async function downloadScanReport(scanId: number): Promise<void> {
  const res = await api.get<Blob>(`/reports/scans/${scanId}/pdf/`, { responseType: "blob" });
  const url = URL.createObjectURL(res.data);
  const link = document.createElement("a");
  link.href = url;
  link.download = `cvst-report-scan-${scanId}.pdf`;
  document.body.appendChild(link);
  link.click();
  link.remove();
  URL.revokeObjectURL(url);
}
