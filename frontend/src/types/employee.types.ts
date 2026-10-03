/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * Employee Access Request (subscription layer) types.
 * Mirrors backend/src/models/employee_models.py and contracts/employee-api.yaml.
 */

export type EmployeeStatus = 'pending' | 'accepted' | 'denied';

export const EMPLOYEE_STATUS_LABELS: Record<EmployeeStatus, string> = {
  pending: 'Pending',
  accepted: 'Accepted',
  denied: 'Denied',
};

export interface CompanyOption {
  /** String — CockroachDB SERIAL ids exceed JS safe-integer range. */
  id: string;
  name: string;
  /** Logo endpoint path, or null when the company has no logo (show a placeholder). */
  logo_url: string | null;
}

export interface CompanyOptionListResponse {
  companies: CompanyOption[];
}

export interface EmployeeRequestCreate {
  employee_name: string;
  /** May omit the `adam-` prefix and use any case — the server normalizes it. */
  employee_id: string;
  company_id: string;
}

export interface EmployeeRequestResponse {
  id: string;
  /** Canonical stored value, e.g. `adam-7f3k92qz`. */
  employee_id: string;
  employee_name: string;
  company_id: string;
  company_name: string;
  status: EmployeeStatus;
  created_at: string;
}

/** One employee row in the Company Dashboard's Employees table. */
export interface CompanyEmployee {
  /** String — CockroachDB SERIAL ids exceed JS safe-integer range. */
  id: string;
  employee_name: string;
  employee_id: string;
  company_id: string;
  company_name: string;
  account_email: string;
  status: EmployeeStatus;
  /** Additive Manager flag — never grants application access on its own. */
  is_manager: boolean;
  created_at: string;
}

export interface EmployeeListResponse {
  employees: CompanyEmployee[];
}

/** PATCH /api/company/employees/{id} request body. */
export interface EmployeeManagerUpdate {
  is_manager: boolean;
}

/**
 * The signed-in account's accepted company membership. It is the application
 * authorization gate and drives the membership-aware navigation.
 */
export interface Membership {
  id: string;
  employee_id: string;
  employee_name: string;
  company_id: string;
  company_name: string;
  status: 'accepted';
  is_manager: boolean;
}

export interface MembershipResponse {
  membership: Membership | null;
}

/** Generic delete acknowledgement ({success,message}) returned by DELETE routes. */
export interface DeleteResponse {
  success: boolean;
  message: string;
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
