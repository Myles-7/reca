import { client } from "../generated/client.gen"
import {
  healthDependenciesHealthGetApiV1HealthDependencies,
  healthLiveHealthGetApiV1HealthLive,
  healthReadyHealthGetApiV1HealthReady,
  loginLoginAccessTokenPostApiV1LoginAccessToken,
  loginRecoverPasswordPostApiV1PasswordRecoveryEmail,
  loginResetPasswordPostApiV1ResetPassword,
  usersCreateUserPostApiV1Users,
  usersDeleteUserDeleteApiV1UsersUserId,
  usersDeleteUserMeDeleteApiV1UsersMe,
  usersReadUserMeGetApiV1UsersMe,
  usersReadUsersGetApiV1Users,
  usersRegisterUserPostApiV1UsersSignup,
  usersUpdatePasswordMePatchApiV1UsersMePassword,
  usersUpdateUserMePatchApiV1UsersMe,
  usersUpdateUserPatchApiV1UsersUserId,
} from "../generated/sdk.gen"

export type {
  BodyLoginLoginAccessTokenPostApiV1LoginAccessToken as Body_login_login_access_token_post_api_v1_login_access_token,
  DependenciesHealthResponse,
  DependencyCheck,
  DependencyStatus,
  LiveHealthResponse,
  ReadyHealthResponse,
  Token,
  UpdatePassword,
  UserCreate,
  UserPublic,
  UserRegister,
  UsersPublic,
  UserUpdate,
  UserUpdateMe,
} from "../generated/types.gen"

export class ApiError extends Error {
  public readonly body: unknown = undefined
  constructor(
    public readonly status: number,
    public readonly kind:
      | "NETWORK"
      | "TIMEOUT"
      | "UNAUTHORIZED"
      | "FORBIDDEN"
      | "VALIDATION"
      | "SERVER"
      | "SERVICE_UNAVAILABLE"
      | "UNKNOWN",
    message: string,
  ) {
    super(message)
    this.name = "ApiError"
  }
}

export function configureApi(baseUrl: string, getToken: () => string | null) {
  client.setConfig({
    baseUrl,
    headers: getToken() ? { Authorization: `Bearer ${getToken()}` } : {},
  })
}

type GeneratedResult<T> = {
  data?: T
  error?: unknown
  response?: Response
}

function errorKind(status: number): ApiError["kind"] {
  if (status === 0) return "NETWORK"
  if (status === 401) return "UNAUTHORIZED"
  if (status === 403) return "FORBIDDEN"
  if (status === 422) return "VALIDATION"
  if (status === 503) return "SERVICE_UNAVAILABLE"
  if (status >= 500) return "SERVER"
  return "UNKNOWN"
}

function errorMessage(status: number): string {
  if (status >= 500) return "The API reported a server error."
  if (status === 0) return "The API could not be reached."
  return "The API request could not be completed."
}

async function unwrap<T>(request: Promise<GeneratedResult<T>>): Promise<T> {
  try {
    const result = await request
    const status = result.response?.status ?? 0
    if (result.error || !result.response?.ok || result.data === undefined) {
      throw new ApiError(status, errorKind(status), errorMessage(status))
    }
    return result.data
  } catch (error) {
    if (error instanceof ApiError) throw error
    throw new ApiError(0, "NETWORK", "The API could not be reached.")
  }
}

export class HealthApi {
  static live = () => unwrap(healthLiveHealthGetApiV1HealthLive())
  static ready = () => unwrap(healthReadyHealthGetApiV1HealthReady())
  static dependencies = () =>
    unwrap(healthDependenciesHealthGetApiV1HealthDependencies())
}

export class AuthApi {
  static login = async (body: { username: string; password: string }) =>
    unwrap(
      loginLoginAccessTokenPostApiV1LoginAccessToken({
        body: { ...body, grant_type: "password" },
      }),
    )
  static recoverPassword = async (email: string) =>
    unwrap(
      loginRecoverPasswordPostApiV1PasswordRecoveryEmail({
        path: { email },
      }),
    )
  static resetPassword = async (body: {
    token: string
    new_password: string
  }) => unwrap(loginResetPasswordPostApiV1ResetPassword({ body }))
}

export class UsersApi {
  static current = async () => unwrap(usersReadUserMeGetApiV1UsersMe())
  static list = async (skip = 0, limit = 100) =>
    unwrap(usersReadUsersGetApiV1Users({ query: { skip, limit } }))
  static create = async (body: import("../generated/types.gen").UserCreate) =>
    unwrap(usersCreateUserPostApiV1Users({ body }))
  static signup = async (body: import("../generated/types.gen").UserRegister) =>
    unwrap(usersRegisterUserPostApiV1UsersSignup({ body }))
  static updateMe = async (
    body: import("../generated/types.gen").UserUpdateMe,
  ) => unwrap(usersUpdateUserMePatchApiV1UsersMe({ body }))
  static changePassword = async (
    body: import("../generated/types.gen").UpdatePassword,
  ) => unwrap(usersUpdatePasswordMePatchApiV1UsersMePassword({ body }))
  static deleteMe = async () => unwrap(usersDeleteUserMeDeleteApiV1UsersMe())
  static update = async (
    userId: string,
    body: import("../generated/types.gen").UserUpdate,
  ) =>
    unwrap(
      usersUpdateUserPatchApiV1UsersUserId({
        path: { user_id: userId },
        body,
      }),
    )
  static delete = async (userId: string) =>
    unwrap(usersDeleteUserDeleteApiV1UsersUserId({ path: { user_id: userId } }))
}

// Temporary names retain the upstream UI call shape while routing exclusively
// through the modern generated client. They are adapter API, not generated code.
export const HealthService = {
  liveHealthGetApiV1HealthLive: HealthApi.live,
  readyHealthGetApiV1HealthReady: HealthApi.ready,
  dependenciesHealthGetApiV1HealthDependencies: HealthApi.dependencies,
}
export const LoginService = {
  loginAccessTokenPostApiV1LoginAccessToken: ({
    formData,
  }: {
    formData: { username: string; password: string }
  }) => AuthApi.login(formData),
  recoverPasswordPostApiV1PasswordRecoveryEmail: ({
    path,
    email,
  }: {
    path?: { email: string }
    email?: string
  }) => AuthApi.recoverPassword(path?.email ?? email ?? ""),
  resetPasswordPostApiV1ResetPassword: ({
    body,
    requestBody,
  }: {
    body?: { token: string; new_password: string }
    requestBody?: { token: string; new_password: string }
  }) => AuthApi.resetPassword(body ?? requestBody!),
}
export const UsersService = {
  readUserMeGetApiV1UsersMe: UsersApi.current,
  readUsersGetApiV1Users: ({ skip = 0, limit = 100 } = {}) =>
    UsersApi.list(skip, limit),
  createUserPostApiV1Users: ({
    body,
    requestBody,
  }: {
    body?: import("../generated/types.gen").UserCreate
    requestBody?: import("../generated/types.gen").UserCreate
  }) => UsersApi.create(body ?? requestBody!),
  registerUserPostApiV1UsersSignup: ({
    body,
    requestBody,
  }: {
    body?: import("../generated/types.gen").UserRegister
    requestBody?: import("../generated/types.gen").UserRegister
  }) => UsersApi.signup(body ?? requestBody!),
  updateUserMePatchApiV1UsersMe: ({
    body,
    requestBody,
  }: {
    body?: import("../generated/types.gen").UserUpdateMe
    requestBody?: import("../generated/types.gen").UserUpdateMe
  }) => UsersApi.updateMe(body ?? requestBody!),
  updatePasswordMePatchApiV1UsersMePassword: ({
    body,
    requestBody,
  }: {
    body?: import("../generated/types.gen").UpdatePassword
    requestBody?: import("../generated/types.gen").UpdatePassword
  }) => UsersApi.changePassword(body ?? requestBody!),
  deleteUserMeDeleteApiV1UsersMe: UsersApi.deleteMe,
  updateUserPatchApiV1UsersUserId: ({
    path,
    userId,
    body,
    requestBody,
  }: {
    path?: { user_id: string }
    userId?: string
    body?: import("../generated/types.gen").UserUpdate
    requestBody?: import("../generated/types.gen").UserUpdate
  }) => UsersApi.update(path?.user_id ?? userId!, body ?? requestBody!),
  deleteUserDeleteApiV1UsersUserId: ({
    path,
    userId,
  }: {
    path?: { user_id: string }
    userId?: string
  }) => UsersApi.delete(path?.user_id ?? userId!),
}
