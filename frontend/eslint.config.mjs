// ESLint flat config (scaffold): Next.js core-web-vitals rules, including jsx-a11y checks.
import nextVitals from 'eslint-config-next/core-web-vitals';

const config = [
  ...nextVitals,
  { ignores: ['.next/**', 'node_modules/**', 'playwright-report/**', 'test-results/**'] },
];
export default config;
