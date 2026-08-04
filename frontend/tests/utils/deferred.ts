export type Deferred = {
  promise: Promise<void>
  resolve: () => void
}

export function createDeferred(): Deferred {
  let resolvePromise!: () => void
  const promise = new Promise<void>((resolve) => {
    resolvePromise = resolve
  })
  return { promise, resolve: resolvePromise }
}
