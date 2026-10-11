/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * Company onboarding-request types.
 * Mirrors backend/src/models/company_request_models.py and
 * contracts/membership-api.yaml + contracts/admin-api.yaml.
 *
 * A company request is a standalone, view-only record: it never creates, links
 * to, or modifies a company account.
 */

/** POST /api/company-requests request body. Only company_name is required. */
export interface CompanyRequestCreate {
  company_name: string;
  role: string;
  website_socials: string;
  email: string;
  phone: string;
}

/** A stored onboarding request as listed in the Admin Dashboard. */
export interface CompanyRequest {
  /** String — CockroachDB SERIAL ids exceed JS safe-integer range. */
  id: string;
  company_name: string;
  role: string;
  website_socials: string;
  email: string;
  phone: string;
  submitted_at: string;
}

export interface CompanyRequestListResponse {
  requests: CompanyRequest[];
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
