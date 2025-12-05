import React, { createContext, useContext, useState, useEffect } from 'react';
import { adminApi } from '../api/backend';

interface PriorityRequest {
  id: string;
  facility: string;
  priority: 'Low' | 'Medium' | 'High' | 'Critical';
  reason: string;
  status: 'Pending' | 'Approved' | 'Rejected';
  timestamp: Date;
}

interface RegionalData {
  region: string;
  usage: number;
  trend: string;
}

interface AdminContextType {
  energyMode: string;
  setEnergyMode: (mode: string) => void;
  mlAutoMode: boolean;
  setMlAutoMode: (enabled: boolean) => void;
  systemStatus: Record<string, boolean>;
  priorityRequests: PriorityRequest[];
  regionalData: RegionalData[];
  addPriorityRequest: (request: Omit<PriorityRequest, 'id' | 'timestamp' | 'status'>) => void;
  updateRequestStatus: (id: string, status: 'Approved' | 'Rejected') => void;
  syncHardware: () => Promise<void>;
}

const AdminContext = createContext<AdminContextType | undefined>(undefined);

export const useAdmin = () => {
  const context = useContext(AdminContext);
  if (!context) throw new Error('useAdmin must be used within AdminProvider');
  return context;
};

export const AdminProvider: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const [energyMode, setEnergyModeState] = useState('Auto Mode');
  const [mlAutoMode, setMlAutoModeState] = useState(false);
  const [systemStatus, setSystemStatus] = useState<Record<string, boolean>>({
    'Crusher Unit': true,
    'Ball Mill': true,
    'Conveyor System': true,
    'AI Control': true
  });
  const [priorityRequests, setPriorityRequests] = useState<PriorityRequest[]>([]);
  const [regionalData, setRegionalData] = useState<RegionalData[]>([]);

  // Fetch admin data from API
  useEffect(() => {
    const fetchData = async () => {
      try {
        const data = await adminApi.getAdminData();
        setEnergyModeState(data.energyMode);
        setMlAutoModeState(data.mlAutoMode);
        setSystemStatus(data.systemStatus);
        // Convert API types to local types
        setPriorityRequests(data.priorityRequests.map(req => ({
          ...req,
          priority: req.priority as 'Low' | 'Medium' | 'High' | 'Critical',
          status: req.status as 'Pending' | 'Approved' | 'Rejected'
        })));
        setRegionalData(data.regionalData);
      } catch (error) {
        console.error('Error fetching admin data:', error);
        // Fall back to default data (already set in state)
      }
    };

    fetchData();
    // Refresh admin data every 5 seconds
    const interval = setInterval(fetchData, 5000);
    return () => clearInterval(interval);
  }, []);

  // ML Auto Mode effect
  useEffect(() => {
    if (mlAutoMode) {
      const modes = ['Solar Only', 'Wind Only', 'Solar+Wind', 'All Sources', 'Auto Mode'];
      const interval = setInterval(() => {
        const randomMode = modes[Math.floor(Math.random() * modes.length)];
        setEnergyMode(randomMode);
      }, 10000);
      return () => clearInterval(interval);
    }
  }, [mlAutoMode]);

  const setEnergyMode = async (mode: string) => {
    try {
      await adminApi.updateEnergyMode(mode);
      setEnergyModeState(mode);
    } catch (error) {
      console.error('Error updating energy mode:', error);
      // Update locally anyway for UI responsiveness
      setEnergyModeState(mode);
    }
  };

  const setMlAutoMode = async (enabled: boolean) => {
    try {
      await adminApi.updateMlAutoMode(enabled);
      setMlAutoModeState(enabled);
    } catch (error) {
      console.error('Error updating ML auto mode:', error);
      // Update locally anyway for UI responsiveness
      setMlAutoModeState(enabled);
    }
  };

  const addPriorityRequest = async (request: Omit<PriorityRequest, 'id' | 'timestamp' | 'status'>) => {
    try {
      await adminApi.createPriorityRequest(request.facility, request.priority, request.reason);
      // Refresh priority requests
      const data = await adminApi.getAdminData();
      setPriorityRequests(data.priorityRequests.map(req => ({
        ...req,
        priority: req.priority as 'Low' | 'Medium' | 'High' | 'Critical',
        status: req.status as 'Pending' | 'Approved' | 'Rejected'
      })));
    } catch (error) {
      console.error('Error creating priority request:', error);
      // Optimistically add to local state
      const newRequest: PriorityRequest = {
        ...request,
        id: Date.now().toString(),
        timestamp: new Date(),
        status: 'Pending'
      };
      setPriorityRequests(prev => [newRequest, ...prev]);
    }
  };

  const updateRequestStatus = async (id: string, status: 'Approved' | 'Rejected') => {
    try {
      await adminApi.updateRequestStatus(id, status);
      // Update local state
      setPriorityRequests(prev =>
        prev.map(req => req.id === id ? { ...req, status } : req)
      );
    } catch (error) {
      console.error('Error updating request status:', error);
      // Update locally anyway for UI responsiveness
      setPriorityRequests(prev =>
        prev.map(req => req.id === id ? { ...req, status } : req)
      );
    }
  };

  const syncHardware = async (): Promise<void> => {
    return new Promise(resolve => setTimeout(resolve, 10000));
  };

  return (
    <AdminContext.Provider value={{
      energyMode,
      setEnergyMode,
      mlAutoMode,
      setMlAutoMode,
      systemStatus,
      priorityRequests,
      regionalData,
      addPriorityRequest,
      updateRequestStatus,
      syncHardware
    }}>
      {children}
    </AdminContext.Provider>
  );
};