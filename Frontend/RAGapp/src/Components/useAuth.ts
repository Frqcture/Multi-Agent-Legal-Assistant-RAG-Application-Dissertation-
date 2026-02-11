import { useState, useEffect } from 'react';

export const useAuth = () => {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
    const [user, setUser] = useState<any>(null);

    const BASE_URL = import.meta.env.VITE_API_BASE_URL;

    const checkAuth = async () => {
      try {
        const response = await fetch(`${BASE_URL}/me`, {
          method: 'GET',
          credentials: 'include', // Include cookies 
        });

        if (response.ok) {
          const data = await response.json();
          setUser(data);
          setIsAuthenticated(true);
        } else {
          setIsAuthenticated(false);
          // Redirect to login if not authenticated
          window.location.href = '/login';
        }
      } catch (error) {
        setIsAuthenticated(false);
        // Redirect to login if not authenticated
        window.location.href = '/login';
      }
    };

    useEffect(() => {
    // Don't ping /me if we are on pages that don't require auth
    const publicPaths = ['/login', '/register'];
    if (publicPaths.includes(window.location.pathname)) {
        setIsAuthenticated(false);
        return;
    }
    checkAuth();
}, []);

    return { isAuthenticated, user, checkAuth };
}