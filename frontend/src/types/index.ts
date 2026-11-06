export type Role = "admin" | "analyst";

export interface User {
  id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: Role;
}

export type TargetType = "ip" | "hostname" | "url" | "network";

export interface Target {
  id: number;
  name: string;
  target_type: TargetType;
  value: string;
  description: string;
  is_active: boolean;
  created_at: string;
}

export type ScanType = "network" | "web" | "full";

export interface Scan {
  id: number;
  name: string;
  target: number;
  scan_type: ScanType;
  status: string;
  progress: number;
  started_at: string | null;
  finished_at: string | null;
  error_message: string;
  vulnerability_count?: number;
  target_detail: { name: string; value: string };
  created_at: string;
}

export type Severity = "critical" | "high" | "medium" | "low" | "info";

export interface Finding {
  id: number;
  scan: number;
  scan_name: string;
  target_value: string;
  cve_id: string;
  title: string;
  description: string;
  severity: Severity;
  cvss_score: number | null;
  port: number | null;
  service: string;
  source: string;
  evidence: string;
  recommendation: string;
  references: string[];
  discovered_at: string;
}

export interface ScanStats {
  total: number;
  active: number;
  completed: number;
  failed: number;
}

export interface SeverityStats {
  total: number;
  by_severity: Record<Severity, number>;
}

export interface Paginated<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

/** DRF returns {results: [...]} when paginated and a bare array otherwise. */
export function listOf<T>(data: Paginated<T> | T[]): T[] {
  return Array.isArray(data) ? data : data.results;
}
