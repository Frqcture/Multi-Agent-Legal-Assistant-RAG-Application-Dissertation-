import { useState, useEffect } from 'react';

export const useAuth = () => {
    const [isAuthenticated, setIsAuthenticated] = useState<boolean | null>(null);
    const [user, setUser] = useState<any>(null);

    const checkAuth = async () => {
      try {
        const response = await fetch('http://0.0.0.0:8000/me', {
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
      checkAuth();
    }, []);

    return { isAuthenticated, user, checkAuth };
}