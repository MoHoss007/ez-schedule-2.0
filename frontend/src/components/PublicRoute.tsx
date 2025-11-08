import React from 'react';
import { Navigate } from 'react-router-dom';
import { useAuth } from '../context/AuthContext';

interface PublicRouteProps {
    children: React.ReactNode;
}

export function PublicRoute({ children }: PublicRouteProps) {
    const { user, loading } = useAuth();

    // Show loading spinner while checking authentication
    if (loading) {
        return (
            <div style={{ 
                display: 'flex', 
                justifyContent: 'center', 
                alignItems: 'center', 
                height: '100vh',
                fontSize: '18px' 
            }}>
                Loading...
            </div>
        );
    }

    // If already authenticated, redirect to dashboard
    if (user) {
        return <Navigate to="/dashboard" replace />;
    }

    // If not authenticated, render the public component (login/register)
    return <>{children}</>;
}