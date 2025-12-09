'use client';

import { useState, useEffect } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import Image from 'next/image';
import { motion } from 'framer-motion';
import { ArrowLeft, Eye, EyeOff, Loader2, ShieldAlert } from 'lucide-react';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { toast } from 'sonner';
import { authApi, settingsApi } from '@/lib/api';
import { useStore } from '@/lib/store';

export default function LoginPage() {
  const router = useRouter();
  const { setUser, setToken, token } = useStore();
  
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [requireLogin, setRequireLogin] = useState(false);
  const [googleEnabled, setGoogleEnabled] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);

  useEffect(() => {
    // Check if login is required
    const checkSettings = async () => {
      try {
        const settings = await settingsApi.get();
        setRequireLogin(settings.require_login || false);
      } catch (e) {
        // Ignore
      }
    };
    checkSettings();
    
    // Check if Google OAuth is enabled
    const checkGoogleOAuth = async () => {
      try {
        const status = await authApi.googleStatus();
        console.log('Login page - Google OAuth status:', status);
        setGoogleEnabled(status.enabled);
      } catch (e) {
        console.error('Failed to check Google OAuth status:', e);
        setGoogleEnabled(false);
      }
    };
    checkGoogleOAuth();
    
    // If already logged in, redirect to home
    if (token) {
      router.push('/');
    }
  }, [token, router]);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    
    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }
    
    setIsLoading(true);
    
    try {
      const response = await authApi.login(email, password);
      setToken(response.access_token);
      
      // Get user info
      const user = await authApi.me();
      setUser(user);
      
      toast.success('Welcome back!');
      router.push('/');
    } catch (error: any) {
      toast.error('Login failed', {
        description: error.response?.data?.detail || 'Invalid credentials'
      });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setGoogleLoading(true);
    try {
      const data = await authApi.googleAuthUrl();
      
      // Build redirect URI
      const redirectUri = `${window.location.origin}/api/auth/google/callback`;
      
      // Store redirect URI for callback
      sessionStorage.setItem('google_redirect_uri', redirectUri);
      
      // Build full URL and redirect
      const url = data.url_template.replace('{origin}', window.location.origin);
      window.location.href = url.replace(
        'redirect_uri={origin}/api/auth/google/callback',
        `redirect_uri=${encodeURIComponent(redirectUri)}`
      );
    } catch (error: any) {
      toast.error('Google login failed', {
        description: error.response?.data?.detail || 'Failed to initiate Google login'
      });
      setGoogleLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <motion.div
        initial={{ opacity: 0, y: 20 }}
        animate={{ opacity: 1, y: 0 }}
        className="w-full max-w-md"
      >
        {/* Back button */}
        <Link href="/" className="inline-flex items-center gap-2 text-sm text-muted-foreground hover:text-foreground mb-8">
          <ArrowLeft className="h-4 w-4" />
          Back to home
        </Link>

        {/* Card */}
        <div className="bg-card rounded-2xl border border-border p-8">
          {/* Logo */}
          <div className="flex items-center gap-3 mb-8">
            <div className="flex h-10 w-10 items-center justify-center rounded-xl overflow-hidden">
              <Image
                src="/logo.png"
                alt="ImageMagick WebGUI"
                width={40}
                height={40}
                className="object-contain"
                priority
              />
            </div>
            <div>
              <h1 className="font-semibold">ImageMagick WebGUI</h1>
              <p className="text-sm text-muted-foreground">Sign in to your account</p>
            </div>
          </div>

          {/* Form */}
          <form onSubmit={handleSubmit} className="space-y-4">
            <div>
              <Label htmlFor="email">Email</Label>
              <Input
                id="email"
                type="email"
                placeholder="you@example.com"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="mt-1"
                autoComplete="email"
              />
            </div>

            <div>
              <Label htmlFor="password">Password</Label>
              <div className="relative mt-1">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  autoComplete="current-password"
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-muted-foreground hover:text-foreground"
                >
                  {showPassword ? <EyeOff className="h-4 w-4" /> : <Eye className="h-4 w-4" />}
                </button>
              </div>
            </div>

            <Button type="submit" className="w-full" disabled={isLoading}>
              {isLoading ? (
                <>
                  <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                  Signing in...
                </>
              ) : (
                'Sign in'
              )}
            </Button>
          </form>

          {/* Google OAuth */}
          {googleEnabled && (
            <>
              <div className="relative my-6">
                <div className="absolute inset-0 flex items-center">
                  <span className="w-full border-t" />
                </div>
                <div className="relative flex justify-center text-xs uppercase">
                  <span className="bg-card px-2 text-muted-foreground">Or continue with</span>
                </div>
              </div>
              
              <Button
                type="button"
                variant="outline"
                onClick={handleGoogleLogin}
                disabled={googleLoading}
                className="w-full"
              >
                {googleLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Redirecting to Google...
                  </>
                ) : (
                  <>
                    <svg className="h-4 w-4 mr-2" viewBox="0 0 24 24">
                      <path
                        fill="#4285F4"
                        d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"
                      />
                      <path
                        fill="#34A853"
                        d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"
                      />
                      <path
                        fill="#FBBC05"
                        d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"
                      />
                      <path
                        fill="#EA4335"
                        d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"
                      />
                    </svg>
                    Continue with Google
                  </>
                )}
              </Button>
            </>
          )}

          {/* Register link */}
          <p className="mt-6 text-center text-sm text-muted-foreground">
            Don&apos;t have an account?{' '}
            <Link href="/register" className="text-primary hover:underline">
              Create one
            </Link>
          </p>
        </div>

        {/* Login required or anonymous usage note */}
        {requireLogin ? (
          <div className="mt-4 p-3 bg-amber-50 dark:bg-amber-950 rounded-lg border border-amber-200 dark:border-amber-800">
            <p className="text-center text-sm text-amber-700 dark:text-amber-300 flex items-center justify-center gap-2">
              <ShieldAlert className="h-4 w-4" />
              Login is required to use this application
            </p>
          </div>
        ) : (
          <p className="mt-4 text-center text-xs text-muted-foreground">
            You can also use the app without an account.<br />
            <Link href="/" className="text-primary hover:underline">Continue as guest</Link>
          </p>
        )}
      </motion.div>
    </div>
  );
}
