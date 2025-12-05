'use client';

import { useEffect, useState } from 'react';
import { useRouter, useSearchParams } from 'next/navigation';
import { useStore } from '@/lib/store';
import { authApi } from '@/lib/api';
import { Loader2, CheckCircle2, XCircle } from 'lucide-react';

export default function GoogleCallbackPage() {
  const router = useRouter();
  const searchParams = useSearchParams();
  const [status, setStatus] = useState<'loading' | 'success' | 'error'>('loading');
  const [error, setError] = useState('');

  useEffect(() => {
    const handleCallback = async () => {
      const code = searchParams.get('code');
      const errorParam = searchParams.get('error');

      if (errorParam) {
        setStatus('error');
        setError(errorParam === 'access_denied' ? 'Access denied' : errorParam);
        return;
      }

      if (!code) {
        setStatus('error');
        setError('No authorization code received');
        return;
      }

      try {
        // Get stored redirect URI
        const redirectUri = sessionStorage.getItem('google_redirect_uri') || 
          `${window.location.origin}/api/auth/google/callback`;

        const data = await authApi.googleCallback(code, redirectUri);
        
        // Store token and user
        useStore.getState().setToken(data.access_token);
        useStore.getState().setUser(data.user);
        
        setStatus('success');
        
        // Clean up
        sessionStorage.removeItem('google_redirect_uri');
        
        // Redirect to home after short delay
        setTimeout(() => {
          router.push('/');
        }, 1500);
      } catch (err: any) {
        setStatus('error');
        setError(err.response?.data?.detail || 'Authentication failed');
      }
    };

    handleCallback();
  }, [searchParams, router]);

  return (
    <div className="min-h-screen flex items-center justify-center bg-background">
      <div className="text-center space-y-4">
        {status === 'loading' && (
          <>
            <Loader2 className="h-12 w-12 animate-spin mx-auto text-primary" />
            <p className="text-lg font-medium">Signing you in...</p>
            <p className="text-sm text-muted-foreground">Please wait</p>
          </>
        )}
        
        {status === 'success' && (
          <>
            <CheckCircle2 className="h-12 w-12 mx-auto text-green-500" />
            <p className="text-lg font-medium">Success!</p>
            <p className="text-sm text-muted-foreground">Redirecting...</p>
          </>
        )}
        
        {status === 'error' && (
          <>
            <XCircle className="h-12 w-12 mx-auto text-destructive" />
            <p className="text-lg font-medium">Authentication Failed</p>
            <p className="text-sm text-muted-foreground">{error}</p>
            <button
              onClick={() => router.push('/')}
              className="mt-4 px-4 py-2 bg-primary text-primary-foreground rounded-lg hover:bg-primary/90"
            >
              Go Home
            </button>
          </>
        )}
      </div>
    </div>
  );
}
