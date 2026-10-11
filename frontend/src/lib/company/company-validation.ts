/* بِسْمِ اللَّهِ الرَّحْمٰنِ الرَّحِيمِ */

/**
 * Validation helpers for the cinematic onboarding's four questions.
 *
 * The clarified rule is "basic format checks": Company Name and Role must be
 * non-empty; Website/Socials must be a web address or a social handle; Email must
 * look like an email; Phone must look like a phone number with optional
 * separators. Keeping them pure makes each step's gate trivial to test by hand.
 */

export interface ValidationResult {
  valid: boolean;
  /** Shown inline beneath the field when invalid. */
  message?: string;
}

const VALID: ValidationResult = { valid: true };

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
// An optional scheme, then a dotted domain, then an optional path.
const WEB_ADDRESS_PATTERN = /^(https?:\/\/)?([\w-]+\.)+[a-z]{2,}(\/\S*)?$/i;
// A social handle, e.g. @acme or @acme.co.
const SOCIAL_HANDLE_PATTERN = /^@[a-z0-9._-]{2,}$/i;
// Digits with optional separators only.
const PHONE_ALLOWED_PATTERN = /^[+()\-\s\d]+$/;

export function validateCompanyName(value: string): ValidationResult {
  if (!value.trim()) {
    return { valid: false, message: 'Enter your company name.' };
  }
  return VALID;
}

export function validateRole(value: string): ValidationResult {
  if (!value.trim()) {
    return { valid: false, message: 'Tell us what your company does.' };
  }
  return VALID;
}

export function validateWebsiteSocials(value: string): ValidationResult {
  const trimmed = value.trim();
  if (!trimmed) {
    return { valid: false, message: 'Add a website or a social handle.' };
  }
  if (WEB_ADDRESS_PATTERN.test(trimmed) || SOCIAL_HANDLE_PATTERN.test(trimmed)) {
    return VALID;
  }
  return {
    valid: false,
    message: 'Enter a web address (e.g. acme.com) or a handle (e.g. @acme).',
  };
}

export function validateEmail(value: string): ValidationResult {
  if (!EMAIL_PATTERN.test(value.trim())) {
    return { valid: false, message: 'Enter a valid email address.' };
  }
  return VALID;
}

export function validatePhone(value: string): ValidationResult {
  const trimmed = value.trim();
  const digits = (trimmed.match(/\d/g) ?? []).length;
  if (!trimmed || !PHONE_ALLOWED_PATTERN.test(trimmed) || digits < 6) {
    return { valid: false, message: 'Enter a valid phone number.' };
  }
  return VALID;
}

/* وَإِنَّ اللَّهَ لَهُوَ خَيْرُ الرَّازِقِينَ */
