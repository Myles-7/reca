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

export class HealthApi {
  static live = async () => (await healthLiveHealthGetApiV1HealthLive()).data!
  static ready = async () =>
    (await healthReadyHealthGetApiV1HealthReady()).data!
  static dependencies = async () =>
    (await healthDependenciesHealthGetApiV1HealthDependencies()).data!
}

export class AuthApi {
  static login = async (body: { username: string; password: string }) =>
    (
      await loginLoginAccessTokenPostApiV1LoginAccessToken({
        body: { ...body, grant_type: "password" },
      })
    ).data!
  static recoverPassword = async (email: string) =>
    (
      await loginRecoverPasswordPostApiV1PasswordRecoveryEmail({
        path: { email },
      })
    ).data!
  static resetPassword = async (body: {
    token: string
    new_password: string
  }) => (await loginResetPasswordPostApiV1ResetPassword({ body })).data!
}

export class UsersApi {
  static current = async () => (await usersReadUserMeGetApiV1UsersMe()).data!
  static list = async (skip = 0, limit = 100) =>
    (await usersReadUsersGetApiV1Users({ query: { skip, limit } })).data!
  static create = async (body: import("../generated/types.gen").UserCreate) =>
    (await usersCreateUserPostApiV1Users({ body })).data!
  static signup = async (body: import("../generated/types.gen").UserRegister) =>
    (await usersRegisterUserPostApiV1UsersSignup({ body })).data!
  static updateMe = async (
    body: import("../generated/types.gen").UserUpdateMe,
  ) => (await usersUpdateUserMePatchApiV1UsersMe({ body })).data!
  static changePassword = async (
    body: import("../generated/types.gen").UpdatePassword,
  ) => (await usersUpdatePasswordMePatchApiV1UsersMePassword({ body })).data!
  static deleteMe = async () =>
    (await usersDeleteUserMeDeleteApiV1UsersMe()).data!
  static update = async (
    userId: string,
    body: import("../generated/types.gen").UserUpdate,
  ) =>
    (
      await usersUpdateUserPatchApiV1UsersUserId({
        path: { user_id: userId },
        body,
      })
    ).data!
  static delete = async (userId: string) =>
    (await usersDeleteUserDeleteApiV1UsersUserId({ path: { user_id: userId } }))
      .data!
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
