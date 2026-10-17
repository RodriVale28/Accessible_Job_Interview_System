// Sprint 1 guest identity: a random id kept in this browser so a user's sessions
// and results stay theirs and can be reopened later. Replaced by real login in US-0.
const KEY = 'interview-studio-user-id';
let memoryId: string | null = null;

function newId(): string {
  if (typeof crypto !== 'undefined' && 'randomUUID' in crypto) return crypto.randomUUID();
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, (c) => {
    const r = (Math.random() * 16) | 0;
    return (c === 'x' ? r : (r & 0x3) | 0x8).toString(16);
  });
}

export function getUserId(): string {
  try {
    const saved = window.localStorage.getItem(KEY);
    if (saved) return saved;
    const id = newId();
    window.localStorage.setItem(KEY, id);
    return id;
  } catch {
    memoryId ??= newId(); // private mode / storage blocked
    return memoryId;
  }
}
