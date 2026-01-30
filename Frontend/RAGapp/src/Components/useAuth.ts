import { useState, useEffect } from 'react';

export const useAuth = () => {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
    const [user, setUser] = useState<any>(null);

    const checkAuth = async () => {
      try {
        const response = await fetch('http://192.168.0.137:8000/me', {
          method: 'GET',
          credentials: 'include', // Include cookies
        });

        if (response.ok) {
          const data = await response.json();
          setUser(data);
          setIsAuthenticated(true);
        } else {
          setIsAuthenticated(false);
        }
      } catch (error) {
        setIsAuthenticated(false);
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