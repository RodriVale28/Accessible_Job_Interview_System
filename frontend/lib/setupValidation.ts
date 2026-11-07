
// S2-1.5 Interview setup validation — owner: Kobra Amiri

export type SetupForm = {

  jobTitle: string;
  difficulty?: string;
  durationMin?: number;
  roleId?: number | null;
  interviewType?: string;
  rolesAvailable?: boolean;
};


export type FieldName = Exclude<keyof SetupForm, 'rolesAvailable'>;

export type FieldErrors = Partial<Record<FieldName, string>>;

export const DIFFICULTIES = [
  'Easy',
  'Medium',
  'Hard',
] as const;

export const DURATIONS = [
  15,
  30,
  45,
] as const;

export const INTERVIEW_TYPES = [
  'Technical',
  'Behavioral',
  'Mixed',
] as const;

export function validateSetup(
  form: SetupForm
  
): FieldErrors {
  const errors: FieldErrors = {};
  const title = form.jobTitle.trim();

  if (!title) {
    errors.jobTitle =
      'Enter the job title you are preparing for.';
  } else if (title.length < 2) {
    errors.jobTitle =
      'Job title must be at least 2 characters.';
  } else if (title.length > 120) {
    errors.jobTitle =
      'Job title must be 120 characters or fewer.';
  } else if (!/\p{L}/u.test(title)) {
    errors.jobTitle =
      'Job title must include letters, not only numbers or special characters.';
  }

  if (
    !form.difficulty ||
    !(DIFFICULTIES as readonly string[]).includes(
      form.difficulty
    )
  ) {
    errors.difficulty =
      'Choose a difficulty: Warm-up, Standard, or Challenge.';
  }

  if (
    !form.durationMin ||
    !(DURATIONS as readonly number[]).includes(
      form.durationMin
    )
  ) {
    errors.durationMin =
      'Choose a length: Short, Medium, or Long.';
  }

  if (
    form.rolesAvailable !== false &&
    (!Number.isInteger(form.roleId) ||
    (form.roleId ?? 0) <= 0)
  ) {
    errors.roleId =
      'Choose the role you want to practice for.';
  }

  if (
    !form.interviewType ||
    !(INTERVIEW_TYPES as readonly string[]).includes(
      form.interviewType
    )
  ) {
    errors.interviewType =
      'Choose an interview type.';
  }

  return errors;
}

export const FIELD_ORDER: FieldName[] = [
  'jobTitle',
  'roleId',
  'interviewType',
  'difficulty',
  'durationMin',
];
