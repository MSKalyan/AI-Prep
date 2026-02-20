"use client";

import { useState, useEffect } from "react";
import { useAuth } from "@/features/auth/hooks/useAuth";

export default function ProfilePage() {

  const { user, isLoading, updateProfile } = useAuth();

  const [form, setForm] = useState({
    full_name: "",
    username: "",
    password: "",
  });

  useEffect(() => {
    if(user){
      setForm({
        full_name: user.full_name || "",
        username: user.username || "",
        password: "",
      });
    }
  }, [user]);

  if(isLoading) return <p>Loading...</p>;

  const submit = async () => {
    await updateProfile(form);
  };

  return (

    <div className="flex justify-center p-6">

      <div className="w-full max-w-md rounded-lg bg-white p-6 shadow-md">

        <h2 className="mb-6 text-xl font-semibold">
          Profile
        </h2>

        <div className="space-y-4">
          <label className="block text-sm font-medium text-gray-700">
            Full Name
          </label>
          <input
            className="w-full rounded-md border p-2"
            value={form.full_name}
            onChange={(e)=>setForm({...form,full_name:e.target.value})}
          />
          <label className="block text-sm font-medium text-gray-700">
            Username
          </label>
          <input
            className="w-full rounded-md border p-2"
            value={form.username}
            onChange={(e)=>setForm({...form,username:e.target.value})}
          />
          <label className="block text-sm font-medium text-gray-700">
            Password
            </label>
            <input
            className="w-full rounded-md border p-2"
            type="password" 
            value={form.password}
            placeholder="Leave blank to not change password"
            onChange={(e)=>setForm({...form,password:e.target.value})}
          />
          <button
            className="w-full rounded-md bg-blue-600 p-2 text-white"
            onClick={submit}
          >
            Save
          </button>

        </div>

      </div>

    </div>
  );
}
