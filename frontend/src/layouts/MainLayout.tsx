import React, { useState } from 'react';
import { Link, useLocation } from 'react-router-dom';
import { 
  HomeIcon, 
  UserGroupIcon, 
  ChatBubbleLeftRightIcon, 
  ChartBarIcon, 
  Cog6ToothIcon,
  BookOpenIcon,
  SunIcon,
  MoonIcon,
} from '@heroicons/react/24/outline';
import { 
  HomeIcon as HomeIconSolid, 
  UserGroupIcon as UserGroupIconSolid, 
  ChatBubbleLeftRightIcon as ChatBubbleLeftRightIconSolid, 
  ChartBarIcon as ChartBarIconSolid, 
  Cog6ToothIcon as Cog6ToothIconSolid,
} from '@heroicons/react/24/solid';
import { useAuth } from '../contexts/AuthContext';
import { useTheme } from '../contexts/ThemeContext';
import UserMenu from '../components/common/UserMenu';

const navigation = [
  { name: 'Dashboard', href: '/dashboard', icon: HomeIcon, current: true },
  { name: 'Leads', href: '/leads', icon: UserGroupIcon, current: false },
  { name: 'Agent', href: '/agent', icon: ChatBubbleLeftRightIcon, current: false },
  { name: 'Campaigns', href: '/campaigns', icon: ChartBarIcon, current: false },
  { name: 'Knowledge', href: '/knowledge', icon: BookOpenIcon, current: false },
  { name: 'Settings', href: '/settings', icon: Cog6ToothIcon, current: false },
];

const MainLayout: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { user, logout } = useAuth();
  const { theme, toggleTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);
  const location = useLocation();

  // Update current navigation based on location
  const updatedNavigation = navigation.map(item => ({
    ...item,
    current: location.pathname === item.href
  }));

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Mobile sidebar */}
      <div className="md:hidden">
        <div className="fixed inset-0 z-40">
          {sidebarOpen ? (
            <div className="fixed inset-0 z-40 flex">
              <div className="relative flex-1 flex flex-col max-w-xs w-full bg-white">
                <div className="absolute top-0 right-0 -mr-12 pt-2">
                  <button
                    type="button"
                    className="ml-1 flex items-center justify-center h-10 w-10 rounded-full focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
                    onClick={() => setSidebarOpen(false)}
                  >
                    <span className="sr-only">Close sidebar</span>
                    <svg
                      className="h-6 w-6 text-white"
                      xmlns="http://www.w3.org/2000/svg"
                      fill="none"
                      viewBox="0 0 24 24"
                      stroke="currentColor"
                      aria-hidden="true"
                    >
                      <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M6 18L18 6M6 6l12 12" />
                    </svg>
                  </button>
                </div>
                <div className="flex-1 h-0 pt-5 pb-4 overflow-y-auto">
                  <div className="flex-shrink-0 flex items-center px-4">
                    <div className="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center">
                      <span className="text-white font-bold">ES</span>
                    </div>
                    <span className="ml-2 text-xl font-bold text-gray-800">SalesAgent</span>
                  </div>
                  <nav className="mt-5 px-2 space-y-1">
                    {updatedNavigation.map((item) => {
                      const Icon = item.current 
                        ? (item.icon as React.ComponentType<React.SVGProps<SVGSVGElement>>).toString().includes('HomeIcon') 
                          ? HomeIconSolid 
                          : (item.icon as React.ComponentType<React.SVGProps<SVGSVGElement>>).toString().includes('UserGroupIcon') 
                            ? UserGroupIconSolid 
                            : (item.icon as React.ComponentType<React.SVGProps<SVGSVGElement>>).toString().includes('ChatBubbleLeftRightIcon') 
                              ? ChatBubbleLeftRightIconSolid 
                              : (item.icon as React.ComponentType<React.SVGProps<SVGSVGElement>>).toString().includes('ChartBarIcon') 
                                ? ChartBarIconSolid 
                                : Cog6ToothIconSolid
                        : item.icon;
                      
                      return (
                        <Link
                          key={item.name}
                          to={item.href}
                          className={`
                            ${item.current 
                              ? 'bg-gray-100 text-gray-900' 
                              : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}
                            group flex items-center px-2 py-2 text-base font-medium rounded-md
                          `}
                        >
                          <Icon
                            className={`
                              ${item.current ? 'text-gray-500' : 'text-gray-400 group-hover:text-gray-500'}
                              mr-4 flex-shrink-0 h-6 w-6
                            `}
                            aria-hidden="true"
                          />
                          {item.name}
                        </Link>
                      );
                    })}
                  </nav>
                </div>
                <div className="flex-shrink-0 flex border-t border-gray-200 p-4">
                  <UserMenu user={user} onLogout={logout} />
                </div>
              </div>
              <div className="flex-shrink-0 w-14" aria-hidden="true">
                {/* Dummy element to force sidebar to shrink to fit close icon */}
              </div>
            </div>
          ) : null}
        </div>
      </div>

      {/* Static sidebar for desktop */}
      <div className="hidden md:flex md:w-64 md:flex-col md:fixed md:inset-y-0">
        <div className="flex-1 flex flex-col min-h-0 border-r border-gray-200 bg-white dark:bg-gray-800 dark:border-gray-700">
          <div className="flex-1 flex flex-col pt-5 pb-4 overflow-y-auto">
            <div className="flex items-center flex-shrink-0 px-4">
              <div className="h-8 w-8 rounded-full bg-indigo-600 flex items-center justify-center">
                <span className="text-white font-bold">ES</span>
              </div>
              <span className="ml-2 text-xl font-bold text-gray-800">SalesAgent</span>
            </div>
            <nav className="mt-5 flex-1 px-2 space-y-1">
              {updatedNavigation.map((item) => {
                const Icon = item.current 
                  ? (item.icon as React.ComponentType<React.SVGProps<SVGSVGElement>>).toString().includes('HomeIcon') 
                    ? HomeIconSolid 
                    : (item.icon as React.ComponentType<React.SVGProps<SVGSVGElement>>).toString().includes('UserGroupIcon') 
                      ? UserGroupIconSolid 
                      : (item.icon as React.ComponentType<React.SVGProps<SVGSVGElement>>).toString().includes('ChatBubbleLeftRightIcon') 
                        ? ChatBubbleLeftRightIconSolid 
                        : (item.icon as React.ComponentType<React.SVGProps<SVGSVGElement>>).toString().includes('ChartBarIcon') 
                          ? ChartBarIconSolid 
                          : Cog6ToothIconSolid
                  : item.icon;
                
                return (
                  <Link
                    key={item.name}
                    to={item.href}
                    className={`
                      ${item.current 
                        ? 'bg-gray-100 text-gray-900' 
                        : 'text-gray-600 hover:bg-gray-50 hover:text-gray-900'}
                      group flex items-center px-2 py-2 text-sm font-medium rounded-md
                    `}
                  >
                    <Icon
                      className={`
                        ${item.current ? 'text-gray-500' : 'text-gray-400 group-hover:text-gray-500'}
                        mr-3 flex-shrink-0 h-6 w-6
                      `}
                      aria-hidden="true"
                    />
                    {item.name}
                  </Link>
                );
              })}
            </nav>
          </div>
          <div className="flex-shrink-0 flex border-t border-gray-200 p-4">
            <UserMenu user={user} onLogout={logout} />
          </div>
        </div>
      </div>

      <div className="md:pl-64 flex flex-col flex-1">
        {/* Top navigation */}
        <div className="sticky top-0 z-10 bg-white shadow">
          <div className="flex items-center justify-between px-4 py-3 sm:px-6">
            <div className="flex items-center">
              <button
                type="button"
                className="md:hidden mr-3 -ml-1 h-10 w-10 rounded-md p-1 text-gray-500 hover:text-gray-600 focus:outline-none focus:ring-2 focus:ring-inset focus:ring-indigo-500"
                onClick={() => setSidebarOpen(true)}
              >
                <span className="sr-only">Open sidebar</span>
                <svg
                  className="h-6 w-6"
                  xmlns="http://www.w3.org/2000/svg"
                  fill="none"
                  viewBox="0 0 24 24"
                  stroke="currentColor"
                  aria-hidden="true"
                >
                  <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M4 6h16M4 12h16M4 18h16" />
                </svg>
              </button>
              <h1 className="text-lg font-semibold text-gray-900">
                {location.pathname.includes('/leads') && 'Leads'}
                {location.pathname.includes('/agent') && 'Agent'}
                {location.pathname.includes('/campaigns') && 'Campaigns'}
                {location.pathname.includes('/settings') && 'Settings'}
                {location.pathname === '/dashboard' && 'Dashboard'}
              </h1>
            </div>
            <div className="flex items-center space-x-3">
              <button
                type="button"
                onClick={toggleTheme}
                className="p-2 rounded-md text-gray-500 hover:text-gray-700 hover:bg-gray-100 dark:text-gray-400 dark:hover:text-gray-200 dark:hover:bg-gray-700 focus:outline-none focus:ring-2 focus:ring-indigo-500"
                aria-label="Toggle dark mode"
              >
                {theme === 'dark' ? (
                  <SunIcon className="h-5 w-5" />
                ) : (
                  <MoonIcon className="h-5 w-5" />
                )}
              </button>
              <UserMenu user={user} onLogout={logout} />
            </div>
          </div>
        </div>

        {/* Main content */}
        <main className="flex-1">
          <div className="py-6">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 md:px-8">
              {children}
            </div>
          </div>
        </main>
      </div>
    </div>
  );
};

export default MainLayout;