export function randomEmail(): string {
  return `test-${crypto.randomUUID()}@example.com`
}

export function randomPassword(): string {
  return `Test-${crypto.randomUUID()}-aA1!`
}
