import { randomUUID } from "crypto";
import { verifySession } from "@/lib/supabase/dal";
import { createClient } from "@/lib/supabase/server";
import { ProfileForm } from "./ProfileForm";

function suggestTopic() {
  return `dealtracker-${randomUUID().slice(0, 8)}`;
}

export default async function ProfilePage() {
  const { user } = await verifySession();

  const supabase = await createClient();
  const { data: profile, error } = await supabase
    .from("profiles")
    .select("ntfy_topic")
    .eq("id", user.id)
    .maybeSingle();

  if (error) {
    console.error("Failed to load profile", error);
  }

  const initialTopic = profile?.ntfy_topic || suggestTopic();

  return (
    <main className="px-4 py-8">
      <div className="mx-auto max-w-sm space-y-6">
        <h1 className="text-xl font-semibold text-gray-900">Profile</h1>

        <div>
          <p className="block text-sm font-medium text-gray-700">Email</p>
          <p className="mt-1 text-base text-gray-900">{user.email}</p>
        </div>

        <ProfileForm initialTopic={initialTopic} />
      </div>
    </main>
  );
}
