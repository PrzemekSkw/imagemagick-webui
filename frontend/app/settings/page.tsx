'use client';

import { useState, useEffect } from 'react';
import { motion } from 'framer-motion';
import { ArrowLeft, Save, RotateCcw, Moon, Sun, Monitor, User, Lock, UserPlus, Shield, Eye, EyeOff } from 'lucide-react';
import Link from 'next/link';
import { useTheme } from 'next-themes';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Slider } from '@/components/ui/slider';
import { Switch } from '@/components/ui/switch';
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
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from '@/components/ui/dialog';
import { toast } from 'sonner';
import { settingsApi, authApi } from '@/lib/api';
import { useStore } from '@/lib/store';

export default function SettingsPage() {
  const { theme, setTheme } = useTheme();
  const { user, token, setOutputFormat, setQuality } = useStore();
  const [mounted, setMounted] = useState(false);
  
  // Settings state
  const [maxUploadSize, setMaxUploadSize] = useState(100);
  const [defaultQuality, setDefaultQuality] = useState(85);
  const [defaultFormat, setDefaultFormat] = useState('webp');
  const [maxParallelJobs, setMaxParallelJobs] = useState(5);
  const [deleteOriginals, setDeleteOriginals] = useState(false);
  const [autoDownload, setAutoDownload] = useState(true);
  const [historyRetention, setHistoryRetention] = useState(24);
  const [requireLogin, setRequireLogin] = useState(false);
  
  // Account dialogs
  const [showChangePassword, setShowChangePassword] = useState(false);
  const [showCreateAccount, setShowCreateAccount] = useState(false);
  
  // Password change state
  const [currentPassword, setCurrentPassword] = useState('');
  const [newPassword, setNewPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [showPasswords, setShowPasswords] = useState(false);
  
  // Create account state
  const [newEmail, setNewEmail] = useState('');
  const [newAccountPassword, setNewAccountPassword] = useState('');
  const [isAdmin, setIsAdmin] = useState(false);

  useEffect(() => {
    setMounted(true);
    loadSettings();
  }, []);

  const loadSettings = async () => {
    try {
      const settings = await settingsApi.get();
      if (settings) {
        setDefaultQuality(settings.default_quality || 85);
        setDefaultFormat(settings.default_format || 'webp');
        setMaxParallelJobs(settings.max_parallel_jobs || 5);
        setDeleteOriginals(settings.delete_originals || false);
        setAutoDownload(settings.auto_download ?? true);
        setRequireLogin(settings.require_login ?? false);
        
        // Sync with global store
        setOutputFormat(settings.default_format || 'webp');
        setQuality(settings.default_quality || 85);
      }
    } catch (error) {
      // Settings might not be available if not logged in
      console.log('Could not load settings');
    }
  };

  const saveSettings = async () => {
    try {
      await settingsApi.update({
        default_quality: defaultQuality,
        default_format: defaultFormat,
        max_parallel_jobs: maxParallelJobs,
        delete_originals: deleteOriginals,
        auto_download: autoDownload,
      });
      
      // Sync with global store immediately
      setOutputFormat(defaultFormat);
      setQuality(defaultQuality);
      
      toast.success('Settings saved!');
    } catch (error) {
      toast.error('Failed to save settings');
    }
  };

  const resetSettings = async () => {
    try {
      await settingsApi.reset();
      await loadSettings();
      toast.success('Settings reset to defaults');
    } catch (error) {
      toast.error('Failed to reset settings');
    }
  };

  const handleChangePassword = async () => {
    if (newPassword !== confirmPassword) {
      toast.error('Passwords do not match');
      return;
    }
    
    if (newPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    try {
      await authApi.changePassword(currentPassword, newPassword);
      toast.success('Password changed successfully!');
      setShowChangePassword(false);
      setCurrentPassword('');
      setNewPassword('');
      setConfirmPassword('');
    } catch (error: any) {
      toast.error(error.message || 'Failed to change password');
    }
  };

  const handleCreateAccount = async () => {
    if (!newEmail || !newAccountPassword) {
      toast.error('Please fill in all fields');
      return;
    }
    
    if (newAccountPassword.length < 6) {
      toast.error('Password must be at least 6 characters');
      return;
    }
    
    try {
      await authApi.createUser(newEmail, newAccountPassword, isAdmin);
      toast.success('Account created successfully!');
      setShowCreateAccount(false);
      setNewEmail('');
      setNewAccountPassword('');
      setIsAdmin(false);
    } catch (error: any) {
      toast.error(error.message || 'Failed to create account');
    }
  };

  if (!mounted) return null;

  return (
    <div className="min-h-screen bg-background">
      {/* Header */}
      <header className="sticky top-0 z-50 bg-background/80 backdrop-blur-sm border-b border-border">
        <div className="max-w-2xl mx-auto px-4 py-4 flex items-center gap-4">
          <Link href="/">
            <Button variant="ghost" size="icon">
              <ArrowLeft className="h-5 w-5" />
            </Button>
          </Link>
          <h1 className="text-xl font-semibold">Settings</h1>
        </div>
      </header>

      {/* Content */}
      <main className="max-w-2xl mx-auto px-4 py-8">
        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          className="space-y-8"
        >
          {/* Account Management */}
          <section className="space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <User className="h-5 w-5" />
              Account
            </h2>
            <div className="p-4 rounded-xl border border-border space-y-4">
              {token && user ? (
                <>
                  <div className="flex items-center justify-between">
                    <div>
                      <Label>Logged in as</Label>
                      <p className="text-sm text-muted-foreground">{user.email}</p>
                    </div>
                    <Button variant="outline" size="sm" onClick={() => setShowChangePassword(true)}>
                      <Lock className="h-4 w-4 mr-2" />
                      Change Password
                    </Button>
                  </div>
                  
                  {user.is_admin && (
                    <div className="flex items-center justify-between pt-4 border-t">
                      <div>
                        <Label>Create New Account</Label>
                        <p className="text-sm text-muted-foreground">Add a new user (admin only)</p>
                      </div>
                      <Button variant="outline" size="sm" onClick={() => setShowCreateAccount(true)}>
                        <UserPlus className="h-4 w-4 mr-2" />
                        Create Account
                      </Button>
                    </div>
                  )}
                </>
              ) : (
                <div className="text-center py-4">
                  <p className="text-muted-foreground mb-4">Log in to manage your account</p>
                  <Link href="/login">
                    <Button>
                      <User className="h-4 w-4 mr-2" />
                      Log In
                    </Button>
                  </Link>
                  <Link href="/register" className="ml-2">
                    <Button variant="outline">
                      <UserPlus className="h-4 w-4 mr-2" />
                      Register
                    </Button>
                  </Link>
                </div>
              )}
            </div>
          </section>

          {/* Security */}
          <section className="space-y-4">
            <h2 className="text-lg font-semibold flex items-center gap-2">
              <Shield className="h-5 w-5" />
              Security
            </h2>
            <div className="p-4 rounded-xl border border-border space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Require Login</Label>
                  <p className="text-sm text-muted-foreground">
                    Users must log in to use the application
                  </p>
                </div>
                <div className="flex items-center gap-2">
                  <span className={`text-sm font-medium ${requireLogin ? 'text-green-600' : 'text-muted-foreground'}`}>
                    {requireLogin ? 'Enabled' : 'Disabled'}
                  </span>
                </div>
              </div>
              <p className="text-xs text-blue-600 dark:text-blue-400">
                ℹ️ This setting is configured via REQUIRE_LOGIN in .env file and requires container restart to change
              </p>
            </div>
          </section>

          {/* Appearance */}
          <section className="space-y-4">
            <h2 className="text-lg font-semibold">Appearance</h2>
            <div className="p-4 rounded-xl border border-border space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Theme</Label>
                  <p className="text-sm text-muted-foreground">Choose your preferred theme</p>
                </div>
                <Select value={theme} onValueChange={setTheme}>
                  <SelectTrigger className="w-[150px]">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="light">
                      <div className="flex items-center gap-2">
                        <Sun className="h-4 w-4" />
                        Light
                      </div>
                    </SelectItem>
                    <SelectItem value="dark">
                      <div className="flex items-center gap-2">
                        <Moon className="h-4 w-4" />
                        Dark
                      </div>
                    </SelectItem>
                    <SelectItem value="system">
                      <div className="flex items-center gap-2">
                        <Monitor className="h-4 w-4" />
                        System
                      </div>
                    </SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </section>

          {/* Processing Defaults */}
          <section className="space-y-4">
            <h2 className="text-lg font-semibold">Processing Defaults</h2>
            <div className="p-4 rounded-xl border border-border space-y-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Default Quality</Label>
                  <span className="text-sm text-muted-foreground">{defaultQuality}%</span>
                </div>
                <Slider
                  value={[defaultQuality]}
                  onValueChange={([v]) => setDefaultQuality(v)}
                  min={1}
                  max={100}
                  step={1}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  JPEG/WebP compression quality for processed images
                </p>
              </div>

              <div>
                <Label>Default Output Format</Label>
                <Select value={defaultFormat} onValueChange={setDefaultFormat}>
                  <SelectTrigger className="mt-1">
                    <SelectValue />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="webp">WebP (recommended)</SelectItem>
                    <SelectItem value="png">PNG (lossless)</SelectItem>
                    <SelectItem value="jpeg">JPEG</SelectItem>
                    <SelectItem value="avif">AVIF (best compression)</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Max Parallel Jobs</Label>
                  <span className="text-sm text-muted-foreground">{maxParallelJobs}</span>
                </div>
                <Slider
                  value={[maxParallelJobs]}
                  onValueChange={([v]) => setMaxParallelJobs(v)}
                  min={1}
                  max={20}
                  step={1}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  Maximum number of images to process simultaneously
                </p>
              </div>
            </div>
          </section>

          {/* Upload Settings */}
          <section className="space-y-4">
            <h2 className="text-lg font-semibold">Upload Settings</h2>
            <div className="p-4 rounded-xl border border-border space-y-6">
              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>Max Upload Size</Label>
                  <span className="text-sm text-muted-foreground">{maxUploadSize} MB</span>
                </div>
                <Slider
                  value={[maxUploadSize]}
                  onValueChange={([v]) => setMaxUploadSize(v)}
                  min={10}
                  max={500}
                  step={10}
                />
              </div>

              <div>
                <div className="flex items-center justify-between mb-2">
                  <Label>History Retention</Label>
                  <span className="text-sm text-muted-foreground">{historyRetention} hours</span>
                </div>
                <Slider
                  value={[historyRetention]}
                  onValueChange={([v]) => setHistoryRetention(v)}
                  min={1}
                  max={168}
                  step={1}
                />
                <p className="text-xs text-muted-foreground mt-1">
                  How long to keep processed files before automatic deletion
                </p>
              </div>
            </div>
          </section>

          {/* Behavior */}
          <section className="space-y-4">
            <h2 className="text-lg font-semibold">Behavior</h2>
            <div className="p-4 rounded-xl border border-border space-y-4">
              <div className="flex items-center justify-between">
                <div>
                  <Label>Auto-download results</Label>
                  <p className="text-sm text-muted-foreground">
                    Automatically download processed files
                  </p>
                </div>
                <Switch
                  checked={autoDownload}
                  onCheckedChange={setAutoDownload}
                />
              </div>

              <div className="flex items-center justify-between">
                <div>
                  <Label>Delete originals after processing</Label>
                  <p className="text-sm text-muted-foreground">
                    Remove source files after successful processing
                  </p>
                </div>
                <Switch
                  checked={deleteOriginals}
                  onCheckedChange={setDeleteOriginals}
                />
              </div>
            </div>
          </section>

          {/* Actions */}
          <div className="flex gap-4">
            <Button onClick={saveSettings} className="flex-1">
              <Save className="h-4 w-4 mr-2" />
              Save Settings
            </Button>
            <Button variant="outline" onClick={resetSettings}>
              <RotateCcw className="h-4 w-4 mr-2" />
              Reset to Defaults
            </Button>
          </div>
        </motion.div>
      </main>

      {/* Change Password Dialog */}
      <Dialog open={showChangePassword} onOpenChange={setShowChangePassword}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Change Password</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Current Password</Label>
              <div className="relative">
                <Input
                  type={showPasswords ? "text" : "password"}
                  value={currentPassword}
                  onChange={(e) => setCurrentPassword(e.target.value)}
                  placeholder="Enter current password"
                />
              </div>
            </div>
            <div className="space-y-2">
              <Label>New Password</Label>
              <Input
                type={showPasswords ? "text" : "password"}
                value={newPassword}
                onChange={(e) => setNewPassword(e.target.value)}
                placeholder="Enter new password"
              />
            </div>
            <div className="space-y-2">
              <Label>Confirm New Password</Label>
              <Input
                type={showPasswords ? "text" : "password"}
                value={confirmPassword}
                onChange={(e) => setConfirmPassword(e.target.value)}
                placeholder="Confirm new password"
              />
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={showPasswords} onCheckedChange={setShowPasswords} />
              <Label className="text-sm">Show passwords</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowChangePassword(false)}>Cancel</Button>
            <Button onClick={handleChangePassword}>Change Password</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>

      {/* Create Account Dialog */}
      <Dialog open={showCreateAccount} onOpenChange={setShowCreateAccount}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Create New Account</DialogTitle>
          </DialogHeader>
          <div className="space-y-4 py-4">
            <div className="space-y-2">
              <Label>Email</Label>
              <Input
                type="email"
                value={newEmail}
                onChange={(e) => setNewEmail(e.target.value)}
                placeholder="user@example.com"
              />
            </div>
            <div className="space-y-2">
              <Label>Password</Label>
              <Input
                type="password"
                value={newAccountPassword}
                onChange={(e) => setNewAccountPassword(e.target.value)}
                placeholder="Minimum 6 characters"
              />
            </div>
            <div className="flex items-center gap-2">
              <Switch checked={isAdmin} onCheckedChange={setIsAdmin} />
              <Label className="text-sm">Admin privileges</Label>
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setShowCreateAccount(false)}>Cancel</Button>
            <Button onClick={handleCreateAccount}>Create Account</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
