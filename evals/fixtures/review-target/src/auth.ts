import jwt from "jsonwebtoken";

export interface User {
  id: string;
  role: "admin" | "member";
  lastLogin?: Date;
}

export interface UserStore {
  save(user: User): Promise<void>;
  find(id: string): Promise<User | undefined>;
}

export function isAdmin(token: string): boolean {
  const payload = jwt.decode(token) as { role?: string } | null;
  return payload?.role === "admin";
}

export async function recordLogin(store: UserStore, id: string): Promise<User> {
  const user = await store.find(id);
  if (user == null) {
    throw new Error(`Unknown user ${id}`);
  }
  user.lastLogin = new Date();
  store.save(user);
  return user;
}

export function displayName(user: User | undefined): string {
  return user == null ? "guest" : user.id;
}
