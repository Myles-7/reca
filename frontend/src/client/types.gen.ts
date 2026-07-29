// Generated client snapshot. Regenerate with `bun run --filter reca-frontend generate-client`.

export type Body_login_login_access_token = {
  username: string
  password: string
  grant_type?: "password" | null
  scope?: string
  client_id?: string | null
  client_secret?: string | null
}

export type Message = { message: string }
export type NewPassword = { token: string; new_password: string }
export type Token = { access_token: string; token_type: string }
export type UpdatePassword = { current_password: string; new_password: string }

export type UserPublic = {
  id: string
  email: string
  is_active: boolean
  is_superuser: boolean
  full_name?: string | null
  created_at?: string | null
}

export type UserCreate = {
  email: string
  password: string
  is_active?: boolean
  is_superuser?: boolean
  full_name?: string | null
}

export type UserRegister = {
  email: string
  password: string
  full_name?: string | null
}

export type UserUpdate = Partial<UserCreate>
export type UserUpdateMe = { email?: string | null; full_name?: string | null }
export type UsersPublic = { data: UserPublic[]; count: number }
