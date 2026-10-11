/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * Company Dashboard & onboarding types.
 *
 * Mirrors the company-auth contract for the sign-in shapes, plus the
 * client-held session. Employee and company-request rows now come from the
 * backend (see @/types/employee.types and @/types/companyRequest.types).
 */

/** A company as returned by the sign-in endpoint (no password material). */
export interface CompanyIdentity {
  id: string;
  name: string;
  logo_url: string | null;
}

/** The client-held company session (localStorage), valid for 24 hours. */
export interface CompanySession {
  token: string;
  company: CompanyIdentity;
  /** ISO-8601; sign-in time + COMPANY_JWT_TTL_HOURS. */
  expires_at: string;
}

/** POST /api/company/login request body. */
export interface CompanyLoginRequest {
  company_name: string;
  password: string;
}

/** POST /api/company/login success response. */
export interface CompanyLoginResponse {
  token: string;
  expires_at: string;
  company: CompanyIdentity;
}

export type EmployeeStatus = 'pending' | 'accepted' | 'denied';

/** Free-trial lifecycle for the signed-in company (GET/POST /api/company/trial). */
export type CompanyTrialStatus =
  | 'not_assigned'
  | 'not_started'
  | 'scheduled'
  | 'active'
  | 'expired';

/** The company's assigned free-trial window and its current state. */
export interface CompanyTrialState {
  status: CompanyTrialStatus;
  /** ISO date (YYYY-MM-DD), or null when no window is assigned. */
  trial_from: string | null;
  trial_to: string | null;
  /** ISO timestamp of the Start click, or null until the company starts. */
  trial_started_at: string | null;
}

/** Generic delete acknowledgement ({success,message}) returned by DELETE routes. */
export interface DeleteResponse {
  success: boolean;
  message: string;
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
