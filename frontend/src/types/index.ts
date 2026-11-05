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
  error_message: string;
  vulnerability_count?: number;
  target_detail: { name: string; value: string };
  created_at: string;
}
