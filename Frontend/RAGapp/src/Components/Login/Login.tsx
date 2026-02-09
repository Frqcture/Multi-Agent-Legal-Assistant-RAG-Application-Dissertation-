import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import styles from './Login.module.css';

const BASE_URL = 'http://192.168.0.193:8000'; // Match your BackendAPI.py URL
//const BASE_URL = import.meta.env.BASE_URL;

const Login: React.FC = () => {
    const [username, setUsername] = useState('');
    const [password, setPassword] = useState('');
    const [error, setError] = useState('');
    const [isLoading, setIsLoading] = useState(false);
    const navigate = useNavigate();

    const handleLogin = async (e: React.FormEvent) => {
        e.preventDefault();
        setError('');
        setIsLoading(true);

        const formData = new URLSearchParams();
        formData.append('username', username);
        formData.append('password', password);

        try {
            const response = await fetch(`${BASE_URL}/login`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
                credentials: 'include',
                body: formData,
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.detail || 'Login failed');
            }

            // Redirect user to /search on successful login
            window.location.href = '/search';
        } catch (err: any) {
            setError(err.message);
        } finally {
            setIsLoading(false);
        }
    };

    const handleRegisterRedirect = () => {
        navigate('/register');
    };

    return (
        <div className={styles.loginContainer}>
            <form className={styles.loginForm} onSubmit={handleLogin}>
                <div className={styles.headerSection}>
                    <h1 className={styles.mainTitle}>Legal Assistant</h1>
                    <p className={styles.tagline}>UK Small Legal Clinics</p>
                </div>
                {error && <p className={styles.errorText}>{error}</p>}
                
                <div className={styles.inputGroup}>
                    <label>Username</label>
                    <input 
                        type="text" 
                        value={username} 
                        onChange={(e) => setUsername(e.target.value)} 
                        required 
                    />
                </div>

                <div className={styles.inputGroup}>
                    <label>Password</label>
                    <input 
                        type="password" 
                        value={password} 
                        onChange={(e) => setPassword(e.target.value)} 
                        required 
                    />
                </div>

                <div className={styles.buttonGroup}>
                  <button type="submit" disabled={isLoading}>
                      {isLoading ? 'Authenticating...' : 'Login'}
                  </button>

                  <button onClick={handleRegisterRedirect}>
                      <p className={styles.registerLink}>Create Account</p>
                  </button>
                </div>
            </form>
        </div>
    );
};

export default Login;