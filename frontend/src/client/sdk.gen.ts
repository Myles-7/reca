// Generated client snapshot. Regenerate with `bun run --filter reca-frontend generate-client`.

import type { CancelablePromise } from "./core/CancelablePromise"
import { OpenAPI } from "./core/OpenAPI"
import { request } from "./core/request"
import type {
  Body_login_login_access_token,
  Message,
  NewPassword,
  Token,
  UpdatePassword,
  UserCreate,
  UserPublic,
  UserRegister,
  UserUpdate,
  UserUpdateMe,
  UsersPublic,
} from "./types.gen"

export class LoginService {
  static loginAccessToken(data: { formData: Body_login_login_access_token }): CancelablePromise<Token> {
    return request(OpenAPI, { method: "POST", url: "/api/v1/login/access-token", formData: data.formData, mediaType: "application/x-www-form-urlencoded" })
  }

  static testToken(): CancelablePromise<UserPublic> {
    return request(OpenAPI, { method: "POST", url: "/api/v1/login/test-token" })
  }

  static recoverPassword(data: { email: string }): CancelablePromise<Message> {
    return request(OpenAPI, { method: "POST", url: "/api/v1/password-recovery/{email}", path: { email: data.email } })
  }

  static resetPassword(data: { requestBody: NewPassword }): CancelablePromise<Message> {
    return request(OpenAPI, { method: "POST", url: "/api/v1/reset-password/", body: data.requestBody, mediaType: "application/json" })
  }
}

export class UsersService {
  static readUsers(data: { skip?: number; limit?: number } = {}): CancelablePromise<UsersPublic> {
    return request(OpenAPI, { method: "GET", url: "/api/v1/users/", query: data })
  }

  static createUser(data: { requestBody: UserCreate }): CancelablePromise<UserPublic> {
    return request(OpenAPI, { method: "POST", url: "/api/v1/users/", body: data.requestBody, mediaType: "application/json" })
  }

  static readUserMe(): CancelablePromise<UserPublic> {
    return request(OpenAPI, { method: "GET", url: "/api/v1/users/me" })
  }

  static deleteUserMe(): CancelablePromise<Message> {
    return request(OpenAPI, { method: "DELETE", url: "/api/v1/users/me" })
  }

  static updateUserMe(data: { requestBody: UserUpdateMe }): CancelablePromise<UserPublic> {
    return request(OpenAPI, { method: "PATCH", url: "/api/v1/users/me", body: data.requestBody, mediaType: "application/json" })
  }

  static updatePasswordMe(data: { requestBody: UpdatePassword }): CancelablePromise<Message> {
    return request(OpenAPI, { method: "PATCH", url: "/api/v1/users/me/password", body: data.requestBody, mediaType: "application/json" })
  }

  static registerUser(data: { requestBody: UserRegister }): CancelablePromise<UserPublic> {
    return request(OpenAPI, { method: "POST", url: "/api/v1/users/signup", body: data.requestBody, mediaType: "application/json" })
  }

  static readUserById(data: { userId: string }): CancelablePromise<UserPublic> {
    return request(OpenAPI, { method: "GET", url: "/api/v1/users/{user_id}", path: { user_id: data.userId } })
  }

  static updateUser(data: { userId: string; requestBody: UserUpdate }): CancelablePromise<UserPublic> {
    return request(OpenAPI, { method: "PATCH", url: "/api/v1/users/{user_id}", path: { user_id: data.userId }, body: data.requestBody, mediaType: "application/json" })
  }

  static deleteUser(data: { userId: string }): CancelablePromise<Message> {
    return request(OpenAPI, { method: "DELETE", url: "/api/v1/users/{user_id}", path: { user_id: data.userId } })
  }
}
