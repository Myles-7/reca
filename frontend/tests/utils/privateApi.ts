import { client } from "../../src/api/generated/client.gen"
import type { UserPublic } from "../../src/api/generated/types.gen"

client.setConfig({ baseUrl: process.env.VITE_API_URL ?? "" })

export const createUser = async ({
  email,
  password,
}: {
  email: string
  password: string
}) => {
  const response = await client.post({
    url: "/api/v1/private/users/",
    body: {
      email,
      password,
      is_verified: true,
      full_name: "Test User",
    },
    throwOnError: true,
  })
  return response.data as UserPublic
}
