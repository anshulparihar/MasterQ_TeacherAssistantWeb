import { create } from 'zustand';

interface AdminState {
  selectedUserId: string | null;
  setSelectedUserId: (id: string | null) => void;
}

export const useAdminStore = create<AdminState>((set) => ({
  selectedUserId: null,
  setSelectedUserId: (id) => set({ selectedUserId: id }),
}));
