/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * Admin Dashboard (Camri Desk) types.
 * Mirrors backend/src/models/admin_models.py and contracts/admin-api.yaml.
 */

import type { EmployeeStatus } from '@/types/employee.types';

export type PaymentStatus = 'pending' | 'free_trial' | 'paid';

export const PAYMENT_STATUS_LABELS: Record<PaymentStatus, string> = {
  pending: 'Pending',
  free_trial: 'Free Trial',
  paid: 'Paid',
};

export interface AdminLoginResponse {
  token: string;
  expires_at: string;
}

export interface Company {
  /** String — CockroachDB SERIAL ids exceed JS safe-integer range. */
  id: string;
  name: string;
  /** Logo endpoint path, or null when no logo is set. */
  logo_url: string | null;
  /** Signals a revealable password without shipping the secret. */
  has_password: boolean;
  price_rupees: number;
  payment_status: PaymentStatus;
  /** Derived, never stored: the number of employee records for this company. */
  employee_count: number;
  created_at: string;
  updated_at: string;
}

/** One employee in the admin companies-table hover roster. */
export interface AdminEmployee {
  id: string;
  employee_name: string;
  employee_id: string;
  status: EmployeeStatus;
  is_manager: boolean;
}

export interface AdminEmployeeListResponse {
  employees: AdminEmployee[];
}

export interface CompanyListResponse {
  companies: Company[];
}

export interface CompanyPasswordResponse {
  password: string;
}

export interface DeleteCompanyResponse {
  success: boolean;
  message: string;
}

/** Create/update payload. `logo` is sent as a file when present. */
export interface CompanyWriteInput {
  name: string;
  /** Required on create; on update, omit to keep the existing password. */
  password?: string;
  price_rupees: number;
  payment_status: PaymentStatus;
  logo?: File | null;
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
