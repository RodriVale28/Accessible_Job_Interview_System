export type SetupForm = { jobTitle: string; difficulty?: string; durationMin?: number };
export type FieldErrors = Partial<Record<keyof SetupForm, string>>;

export const DIFFICULTIES = ['Easy', 'Medium', 'Hard'] as const;
export const DURATIONS = [15, 30, 45] as const;

export function validateSetup(form: SetupForm): FieldErrors {
    const errors: FieldErrors = {};
    const title = form.jobTitle.trim();
    if (!title) errors.jobTitle = 'Enter the job title you are preparing for.';
    else if (title.length < 2) errors.jobTitle = 'Job title must be at least 2 characters.';
    else if (title.length > 120) errors.jobTitle = 'Job title must be 120 characters or fewer.';

    if (!form.difficulty || !(DIFFICULTIES as readonly string[]).includes(form.difficulty))
        errors.difficulty = 'Choose a difficulty: Easy, Medium or Hard.';

    if (!form.durationMin || !(DURATIONS as readonly number[]).includes(form.durationMin))
        errors.durationMin = 'Choose how long the interview lasts: 15, 30 or 45 minutes.';

    return errors;
}

// Order used to move focus to the first invalid field on submit.
export const FIELD_ORDER: (keyof SetupForm)[] = ['jobTitle', 'difficulty', 'durationMin'];