'use client';

import { useState, useEffect } from 'react';
import { useTheme } from 'next-themes';
import { 
  Menu, 
  Sun, 
  Moon, 
  Monitor,
  User,
  LogOut,
  Download,
  Trash2,
  Check,
  X,
  AlertCircle
} from 'lucide-react';
import { Button } from '@/components/ui/button';
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from '@/components/ui/select';
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
  DialogTrigger,
} from '@/components/ui/dialog';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { useStore } from '@/lib/store';
import { authApi } from '@/lib/api';
import { toast } from 'sonner';
import { cn } from '@/lib/utils';

// Password validation helper
function validatePassword(password: string) {
  return {
    minLength: password.length >= 8,
    hasLower: /[a-z]/.test(password),
    hasUpper: /[A-Z]/.test(password),
    hasDigit: /\d/.test(password),
    hasSpecial: /[!@#$%^&*(),.?":{}|<>_\-+=\[\]\\\/~`]/.test(password),
  };
}

function isPasswordValid(password: string) {
  const v = validatePassword(password);
  return v.minLength && v.hasLower && v.hasUpper && v.hasDigit && v.hasSpecial;
}

export function Header() {
  const { theme, setTheme } = useTheme();
  const { 
    user, 
    setSidebarOpen, 
    selectedImageIds, 
    clearSelection,
    images,
    logout 
  } = useStore();
  const [showAuthDialog, setShowAuthDialog] = useState(false);
  const [isLogin, setIsLogin] = useState(true);
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [name, setName] = useState('');
  const [loading, setLoading] = useState(false);
  const [registrationEnabled, setRegistrationEnabled] = useState(true);
  const [googleEnabled, setGoogleEnabled] = useState(false);
  const [googleLoading, setGoogleLoading] = useState(false);
  const [mounted, setMounted] = useState(false);

  const selectedCount = selectedImageIds.length;
  const passwordChecks = validatePassword(password);
  const passwordValid = isPasswordValid(password);

  // Mark as mounted (client-side only)
  useEffect(() => {
    setMounted(true);
  }, []);

  // Check registration and Google OAuth status on mount
  useEffect(() => {
    if (!mounted) return;
    
    const checkStatus = async () => {
      try {
        const regData = await authApi.registrationStatus();
        setRegistrationEnabled(regData.registration_enabled);
      } catch {
        setRegistrationEnabled(true);
      }
      
      try {
        const googleData = await authApi.googleStatus();
        console.log('Google OAuth status:', googleData);
        setGoogleEnabled(googleData.enabled);
      } catch (err) {
        console.error('Google OAuth status error:', err);
        setGoogleEnabled(false);
      }
    };
    
    checkStatus();
  }, [mounted]);
  
  // Re-check when dialog opens
  useEffect(() => {
    if (showAuthDialog && mounted) {
      authApi.googleStatus()
        .then(data => {
          console.log('Google OAuth re-check:', data);
          setGoogleEnabled(data.enabled);
        })
        .catch(() => {});
    }
  }, [showAuthDialog, mounted]);

  const handleAuth = async () => {
    if (!email || !password) {
      toast.error('Please fill in all fields');
      return;
    }

    // Validate password on registration
    if (!isLogin && !passwordValid) {
      toast.error('Password does not meet requirements');
      return;
    }

    setLoading(true);
    try {
      if (isLogin) {
        const data = await authApi.login(email, password);
        useStore.getState().setToken(data.access_token);
        useStore.getState().setUser(data.user);
        toast.success('Welcome back!');
      } else {
        const data = await authApi.register(email, password, name);
        useStore.getState().setToken(data.access_token);
        useStore.getState().setUser(data.user);
        toast.success('Account created successfully!');
      }
      setShowAuthDialog(false);
      setEmail('');
      setPassword('');
      setName('');
    } catch (error: any) {
      const detail = error.response?.data?.detail;
      // Handle Pydantic validation errors
      if (Array.isArray(detail)) {
        const msg = detail.map((d: any) => d.msg || d.message).join(', ');
        toast.error(msg || 'Validation failed');
      } else {
        toast.error(detail || 'Authentication failed');
      }
    } finally {
      setLoading(false);
    }
  };

  const handleGoogleLogin = async () => {
    setGoogleLoading(true);
    try {
      const data = await authApi.googleAuthUrl();
      
      // Build redirect URI
      const redirectUri = `${window.location.origin}/api/auth/google/callback`;
      
      // Build full URL
      const url = data.url_template.replace('{origin}', window.location.origin);
      
      // Store redirect URI for callback
      sessionStorage.setItem('google_redirect_uri', redirectUri);
      
      // Redirect to Google
      window.location.href = url.replace(
        'redirect_uri={origin}/api/auth/google/callback',
        `redirect_uri=${encodeURIComponent(redirectUri)}`
      );
    } catch (error: any) {
      toast.error(error.response?.data?.detail || 'Google login failed');
      setGoogleLoading(false);
    }
  };

  const handleLogout = () => {
    logout();
    toast.success('Logged out successfully');
  };

  return (
    <header className="sticky top-0 z-10 flex h-16 items-center justify-between border-b border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/60 px-4 lg:px-6">
      {/* Left side */}
      <div className="flex items-center gap-4">
        <Button
          variant="ghost"
          size="icon"
          onClick={() => setSidebarOpen(true)}
          className="lg:hidden"
        >
          <Menu className="h-5 w-5" />
        </Button>

        {selectedCount > 0 && (
          <div className="flex items-center gap-2 animate-fade-in">
            <span className="text-sm text-muted-foreground">
              {selectedCount} selected
            </span>
            <Button
              variant="ghost"
              size="sm"
              onClick={clearSelection}
              className="text-xs"
            >
              Clear
            </Button>
          </div>
        )}
      </div>

      {/* Right side */}
      <div className="flex items-center gap-2">
        {/* Theme toggle */}
        <Select value={theme} onValueChange={setTheme}>
          <SelectTrigger className="w-[110px] h-9">
            <SelectValue />
          </SelectTrigger>
          <SelectContent>
            <SelectItem value="light">
              <div className="flex items-center gap-2">
                <Sun className="h-4 w-4" />
                <span>Light</span>
              </div>
            </SelectItem>
            <SelectItem value="dark">
              <div className="flex items-center gap-2">
                <Moon className="h-4 w-4" />
                <span>Dark</span>
              </div>
            </SelectItem>
            <SelectItem value="system">
              <div className="flex items-center gap-2">
                <Monitor className="h-4 w-4" />
                <span>System</span>
              </div>
            </SelectItem>
          </SelectContent>
        </Select>

        {/* User menu */}
        {user ? (
          <div className="flex items-center gap-2">
            <div className="flex h-9 items-center gap-2 rounded-xl bg-secondary px-3">
              <User className="h-4 w-4 text-muted-foreground" />
              <span className="text-sm font-medium max-w-[100px] truncate">
                {user.name || user.email}
              </span>
            </div>
            <Button
              variant="ghost"
              size="icon"
              onClick={handleLogout}
              className="text-muted-foreground hover:text-destructive"
            >
              <LogOut className="h-4 w-4" />
            </Button>
          </div>
        ) : (
          <Dialog open={showAuthDialog} onOpenChange={setShowAuthDialog}>
            <DialogTrigger asChild>
              <Button variant="outline" size="sm">
                <User className="h-4 w-4 mr-2" />
                Sign In
              </Button>
            </DialogTrigger>
            <DialogContent className="sm:max-w-[400px]">
              <DialogHeader>
                <DialogTitle>{isLogin ? 'Welcome back' : 'Create account'}</DialogTitle>
                <DialogDescription>
                  {isLogin 
                    ? 'Sign in to save your settings and history' 
                    : 'Create an account to get started'}
                </DialogDescription>
              </DialogHeader>
              <div className="grid gap-4 py-4">
                {!isLogin && (
                  <div className="grid gap-2">
                    <Label htmlFor="name">Name</Label>
                    <Input
                      id="name"
                      placeholder="Your name"
                      value={name}
                      onChange={(e) => setName(e.target.value)}
                    />
                  </div>
                )}
                <div className="grid gap-2">
                  <Label htmlFor="email">Email</Label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="you@example.com"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                  />
                </div>
                <div className="grid gap-2">
                  <Label htmlFor="password">Password</Label>
                  <Input
                    id="password"
                    type="password"
                    placeholder="••••••••"
                    value={password}
                    onChange={(e) => setPassword(e.target.value)}
                    onKeyDown={(e) => e.key === 'Enter' && handleAuth()}
                  />
                  
                  {/* Password requirements - only show during registration */}
                  {!isLogin && password.length > 0 && (
                    <div className="mt-2 p-3 bg-muted rounded-lg text-xs space-y-1">
                      <p className="font-medium text-muted-foreground mb-2">Password requirements:</p>
                      <div className={cn("flex items-center gap-2", passwordChecks.minLength ? "text-green-600" : "text-muted-foreground")}>
                        {passwordChecks.minLength ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
                        At least 8 characters
                      </div>
                      <div className={cn("flex items-center gap-2", passwordChecks.hasLower ? "text-green-600" : "text-muted-foreground")}>
                        {passwordChecks.hasLower ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
                        One lowercase letter
                      </div>
                      <div className={cn("flex items-center gap-2", passwordChecks.hasUpper ? "text-green-600" : "text-muted-foreground")}>
                        {passwordChecks.hasUpper ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
                        One uppercase letter
                      </div>
                      <div className={cn("flex items-center gap-2", passwordChecks.hasDigit ? "text-green-600" : "text-muted-foreground")}>
                        {passwordChecks.hasDigit ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
                        One digit
                      </div>
                      <div className={cn("flex items-center gap-2", passwordChecks.hasSpecial ? "text-green-600" : "text-muted-foreground")}>
                        {passwordChecks.hasSpecial ? <Check className="h-3 w-3" /> : <X className="h-3 w-3" />}
                        One special character (!@#$%^&*...)
                      </div>
                    </div>
                  )}
                </div>
              </div>
              <DialogFooter className="flex-col gap-3 sm:flex-col">
                <Button 
                  onClick={handleAuth} 
                  disabled={loading || (!isLogin && !passwordValid)}
                  className="w-full"
                >
                  {loading ? 'Loading...' : isLogin ? 'Sign In' : 'Create Account'}
                </Button>
                
                {/* Google OAuth */}
                {googleEnabled && (
                  <>
                    <div className="relative">
                      <div className="absolute inset-0 flex items-center">
                        <span className="w-full border-t" />
                      </div>
                      <div className="relative flex justify-center text-xs uppercase">
                        <span className="bg-background px-2 text-muted-foreground">Or</span>
                      </div>
                    </div>
                    <Button
                      variant="outline"
                      onClick={handleGoogleLogin}
                      disabled={googleLoading}
                      className="w-full"
                    >
                      {googleLoading ? (
                        'Redirecting...'
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
                
                {registrationEnabled ? (
                  <Button
                    variant="ghost"
                    onClick={() => setIsLogin(!isLogin)}
                    className="w-full text-sm"
                  >
                    {isLogin 
                      ? "Don't have an account? Sign up" 
                      : 'Already have an account? Sign in'}
                  </Button>
                ) : (
                  !isLogin && (
                    <div className="flex items-center gap-2 text-sm text-muted-foreground justify-center">
                      <AlertCircle className="h-4 w-4" />
                      Registration is disabled
                    </div>
                  )
                )}
                {!registrationEnabled && isLogin && (
                  <p className="text-xs text-muted-foreground text-center">
                    Registration is currently disabled. Contact administrator.
                  </p>
                )}
              </DialogFooter>
            </DialogContent>
          </Dialog>
        )}
      </div>
    </header>
  );
}
