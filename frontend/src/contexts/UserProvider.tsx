import React, { createContext, useContext, useState, useEffect } from 'react';
import { userApi } from '../api/backend';

interface UserData {
  id: string;
  name: string;
  region: string;
  points: number;
  renewableUsage: number;
  rank: number;
  badges: string[];
}

interface LeaderboardUser {
  id: string;
  name: string;
  region: string;
  points: number;
  renewableUsage: number;
  rank: number;
}

interface UserContextType {
  userData: UserData;
  leaderboard: LeaderboardUser[];
  updatePoints: (points: number) => void;
  addBadge: (badge: string) => void;
}

const UserContext = createContext<UserContextType | undefined>(undefined);

export const useUser = () => {
  const context = useContext(UserContext);
  if (!context) throw new Error('useUser must be used within UserProvider');
  return context;
};

export const UserProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [userData, setUserData] = useState<UserData>({
    id: '1',
    name: 'Praveen Kumar',
    region: 'Mining Operations',
    points: 1850,
    renewableUsage: 78.5,
    rank: 12,
    badges: ['Efficiency Expert', 'Process Optimizer', 'Safety Champion', 'AI Pioneer']
  });

  const [leaderboard, setLeaderboard] = useState<LeaderboardUser[]>([]);

  // Fetch user data and leaderboard from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        const [user, leaderboardData] = await Promise.all([
          userApi.getUser('1'),
          userApi.getLeaderboard()
        ]);
        setUserData(user);
        setLeaderboard(leaderboardData);
      } catch (error) {
        console.error('Error fetching user data:', error);
        // Fall back to default data (already set in state)
      }
    };

    fetchData();
    // Refresh leaderboard every 10 seconds
    const interval = setInterval(() => {
      userApi.getLeaderboard()
        .then(setLeaderboard)
        .catch(console.error);
    }, 10000);
    
    return () => clearInterval(interval);
  }, []);

  const updatePoints = async (points: number) => {
    try {
      await userApi.updatePoints(userData.id, points);
      // Update local state optimistically
      setUserData(prev => ({
        ...prev,
        points: prev.points + points
      }));
      // Refresh user data and leaderboard
      const [user, leaderboardData] = await Promise.all([
        userApi.getUser(userData.id),
        userApi.getLeaderboard()
      ]);
      setUserData(user);
      setLeaderboard(leaderboardData);
    } catch (error) {
      console.error('Error updating points:', error);
    }
  };

  const addBadge = async (badge: string) => {
    try {
      await userApi.addBadge(userData.id, badge);
      // Update local state optimistically
      setUserData(prev => ({
        ...prev,
        badges: [...prev.badges, badge]
      }));
      // Refresh user data
      const user = await userApi.getUser(userData.id);
      setUserData(user);
    } catch (error) {
      console.error('Error adding badge:', error);
    }
  };

  return (
    <UserContext.Provider value={{
      userData,
      leaderboard,
      updatePoints,
      addBadge
    }}>
      {children}
    </UserContext.Provider>
  );
};