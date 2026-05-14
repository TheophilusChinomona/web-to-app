import { test as base } from '@playwright/test';

// Extend test with custom helpers if needed
export const test = base.extend({
  // Add fixtures here
});

export { expect } from '@playwright/test';
