import { auth } from "@/auth";

export type AppSession = {
  user: {
    id?: string;
    email?: string | null;
    name?: string | null;
    image?: string | null;
  };
};

export async function getCurrentSession(): Promise<AppSession | null> {
  if (!process.env.NEON_AUTH_BASE_URL) return null;

  const { data } = await auth.getSession();
  if (!data?.user?.email) return null;

  return {
    user: {
      id: data.user.id,
      email: data.user.email,
      name: data.user.name,
      image: data.user.image,
    },
  };
}
