// API service for backend communication
const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

export interface EnergyData {
  solar: number;
  wind: number;
  grid: number;
  battery: {
    level: number;
    health: number;
  };
  consumption: number;
  timestamp: Date;
}

export interface EnergyDataResponse {
  energyData: EnergyData;
  renewablePercentage: number;
  isOnline: boolean;
  alerts: string[];
  historicalData: EnergyData[];
}

export interface UserData {
  id: string;
  name: string;
  region: string;
  points: number;
  renewableUsage: number;
  rank: number;
  badges: string[];
}

export interface LeaderboardUser {
  id: string;
  name: string;
  region: string;
  points: number;
  renewableUsage: number;
  rank: number;
}

export interface PriorityRequest {
  id: string;
  facility: string;
  priority: string;
  reason: string;
  status: string;
  timestamp: Date;
}

export interface RegionalData {
  region: string;
  usage: number;
  trend: string;
}

export interface AdminDataResponse {
  energyMode: string;
  mlAutoMode: boolean;
  systemStatus: Record<string, boolean>;
  priorityRequests: PriorityRequest[];
  regionalData: RegionalData[];
}

// Energy API
export const energyApi = {
  getCurrent: async (): Promise<EnergyDataResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/energy/current`);
    if (!response.ok) throw new Error('Failed to fetch energy data');
    const data = await response.json();
    // Convert timestamp strings to Date objects
    data.energyData.timestamp = new Date(data.energyData.timestamp);
    data.historicalData = data.historicalData.map((d: any) => ({
      ...d,
      timestamp: new Date(d.timestamp)
    }));
    return data;
  },

  updateData: async (data: EnergyData): Promise<{ success: boolean; id: string }> => {
    const response = await fetch(`${API_BASE_URL}/api/energy/update`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data)
    });
    if (!response.ok) throw new Error('Failed to update energy data');
    return response.json();
  }
};

// User API
export const userApi = {
  getUser: async (userId: string): Promise<UserData> => {
    const response = await fetch(`${API_BASE_URL}/api/user/${userId}`);
    if (!response.ok) throw new Error('Failed to fetch user data');
    return response.json();
  },

  getLeaderboard: async (): Promise<LeaderboardUser[]> => {
    const response = await fetch(`${API_BASE_URL}/api/leaderboard`);
    if (!response.ok) throw new Error('Failed to fetch leaderboard');
    return response.json();
  },

  updatePoints: async (userId: string, points: number): Promise<{ success: boolean; message: string }> => {
    const response = await fetch(`${API_BASE_URL}/api/user/points`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userId, points })
    });
    if (!response.ok) throw new Error('Failed to update points');
    return response.json();
  },

  addBadge: async (userId: string, badge: string): Promise<{ success: boolean; message: string }> => {
    const response = await fetch(`${API_BASE_URL}/api/user/badge`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ userId, badge })
    });
    if (!response.ok) throw new Error('Failed to add badge');
    return response.json();
  }
};

// Admin API
export const adminApi = {
  getAdminData: async (): Promise<AdminDataResponse> => {
    const response = await fetch(`${API_BASE_URL}/api/admin/data`);
    if (!response.ok) throw new Error('Failed to fetch admin data');
    const data = await response.json();
    // Convert timestamp strings to Date objects
    data.priorityRequests = data.priorityRequests.map((req: any) => ({
      ...req,
      timestamp: new Date(req.timestamp)
    }));
    return data;
  },

  updateEnergyMode: async (mode: string): Promise<{ success: boolean; message: string }> => {
    const response = await fetch(`${API_BASE_URL}/api/admin/energy-mode?mode=${encodeURIComponent(mode)}`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to update energy mode');
    return response.json();
  },

  updateMlAutoMode: async (enabled: boolean): Promise<{ success: boolean; message: string }> => {
    const response = await fetch(`${API_BASE_URL}/api/admin/ml-auto-mode?enabled=${enabled}`, {
      method: 'POST'
    });
    if (!response.ok) throw new Error('Failed to update ML auto mode');
    return response.json();
  },

  createPriorityRequest: async (facility: string, priority: string, reason: string): Promise<{ success: boolean; id: string }> => {
    const response = await fetch(`${API_BASE_URL}/api/admin/priority-request`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ facility, priority, reason })
    });
    if (!response.ok) throw new Error('Failed to create priority request');
    return response.json();
  },

  updateRequestStatus: async (requestId: string, status: string): Promise<{ success: boolean; message: string }> => {
    const response = await fetch(`${API_BASE_URL}/api/admin/priority-request/status`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ requestId, status })
    });
    if (!response.ok) throw new Error('Failed to update request status');
    return response.json();
  }
};
