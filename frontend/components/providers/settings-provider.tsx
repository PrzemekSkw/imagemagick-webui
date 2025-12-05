"use client";

import { useEffect, useState, useCallback } from "react";
import { useRouter, usePathname } from "next/navigation";
import { useStore } from "@/lib/store";
import { settingsApi } from "@/lib/api";

export function SettingsProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const setOutputFormat = useStore((state) => state.setOutputFormat);
  const setQuality = useStore((state) => state.setQuality);
  const token = useStore((state) => state.token);
  const [isChecking, setIsChecking] = useState(true);
  const [requireLogin, setRequireLogin] = useState(false);
  const [settingsLoaded, setSettingsLoaded] = useState(false);

  // Public paths that don't require login
  const publicPaths = ['/login', '/register'];
  const isPublicPath = publicPaths.includes(pathname);

  // Load settings on app start
  useEffect(() => {
    const loadSettings = async () => {
      try {
        console.log("Loading settings...");
        const settings = await settingsApi.get();
        console.log("Settings loaded:", settings);
        
        if (settings) {
          if (settings.default_format) {
            setOutputFormat(settings.default_format);
          }
          if (settings.default_quality) {
            setQuality(settings.default_quality);
          }
          
          const loginRequired = settings.require_login === true;
          console.log("Login required:", loginRequired, "Token:", !!token, "Public path:", isPublicPath);
          setRequireLogin(loginRequired);
          setSettingsLoaded(true);
        }
      } catch (error) {
        console.log("Could not load settings, using defaults", error);
        setSettingsLoaded(true);
      } finally {
        setIsChecking(false);
      }
    };

    loadSettings();
  }, [setOutputFormat, setQuality]);

  // Check login requirement after settings are loaded
  useEffect(() => {
    if (!settingsLoaded) return;
    
    console.log("Checking login requirement:", { requireLogin, token: !!token, isPublicPath, pathname });
    
    if (requireLogin && !token && !isPublicPath) {
      console.log("Redirecting to login...");
      router.replace('/login');
    }
  }, [settingsLoaded, requireLogin, token, isPublicPath, router, pathname]);

  // Show loading while checking (prevents flash of content)
  if (isChecking && !isPublicPath) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="text-sm text-muted-foreground">Loading...</p>
        </div>
      </div>
    );
  }

  // Block content if login is required but user not logged in
  if (settingsLoaded && requireLogin && !token && !isPublicPath) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-background">
        <div className="flex flex-col items-center gap-3">
          <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary"></div>
          <p className="text-sm text-muted-foreground">Redirecting to login...</p>
        </div>
      </div>
    );
  }

  return <>{children}</>;
}
