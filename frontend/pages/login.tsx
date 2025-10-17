import Head from 'next/head';
import Link from 'next/link';
import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { motion } from 'framer-motion';

export default function Login() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { login, loginError } = useAuth();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    login({ email, password });
  };

  return (
    <>
      <Head>
        <title>Log In - Launch Loop</title>
      </Head>

      <div className="min-h-screen bg-dark-navy relative overflow-hidden flex items-center justify-center px-4">
        {/* Animated Background */}
        <div
          className="absolute inset-0 opacity-30"
          style={{
            background: 'linear-gradient(135deg, #0A0E27 0%, #1A2038 50%, #0A0E27 100%)',
            backgroundSize: '200% 200%',
            animation: 'gradientShift 8s ease infinite',
          }}
        />

        <motion.div
          initial={{ opacity: 0, y: 20 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.5 }}
          className="max-w-md w-full relative z-10"
        >
          <div className="text-center mb-8">
            <Link href="/" className="text-3xl font-bold text-white flex items-center justify-center gap-2">
              <span className="text-neon-cyan">✨</span> Launch Loop
            </Link>
            <h1 className="text-2xl font-bold text-white mt-6">
              Welcome back
            </h1>
            <p className="text-gray-400 mt-2">Log in to your account</p>
          </div>

          <div className="bg-dark-elevated/60 backdrop-blur-xl rounded-2xl border border-glass-border shadow-glass p-8">
            <form onSubmit={handleSubmit} className="space-y-6">
              <div>
                <label
                  htmlFor="email"
                  className="block text-sm font-medium text-gray-300 mb-2"
                >
                  Email
                </label>
                <input
                  id="email"
                  type="email"
                  required
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  className="w-full px-4 py-3 bg-dark-surface border border-glass-border rounded-lg focus:ring-2 focus:ring-neon-cyan/50 focus:border-neon-cyan text-white placeholder-gray-500 outline-none transition"
                  placeholder="you@example.com"
                />
              </div>

              <div>
                <label
                  htmlFor="password"
                  className="block text-sm font-medium text-gray-300 mb-2"
                >
                  Password
                </label>
                <input
                  id="password"
                  type="password"
                  required
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  className="w-full px-4 py-3 bg-dark-surface border border-glass-border rounded-lg focus:ring-2 focus:ring-neon-cyan/50 focus:border-neon-cyan text-white placeholder-gray-500 outline-none transition"
                  placeholder="••••••••"
                />
              </div>

              {loginError && (
                <div className="bg-red-500/20 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg text-sm">
                  {typeof loginError === 'string' ? loginError : loginError.message || 'Login failed'}
                </div>
              )}

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-neon-cyan to-electric-blue text-dark-navy font-bold py-3 rounded-xl hover:shadow-glow-cyan transition"
              >
                Log In
              </button>
            </form>

            <div className="mt-6 text-center">
              <p className="text-gray-400 text-sm">
                Don't have an account?{' '}
                <Link href="/signup" className="text-neon-cyan hover:underline font-semibold">
                  Sign up
                </Link>
              </p>
            </div>
          </div>
        </motion.div>
      </div>
    </>
  );
}
