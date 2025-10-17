import Head from 'next/head';
import Link from 'next/link';
import { useState } from 'react';
import { useAuth } from '../hooks/useAuth';
import { motion } from 'framer-motion';

export default function Signup() {
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const { signup, signupError } = useAuth();

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    signup({ email, password });
  };

  return (
    <>
      <Head>
        <title>Sign Up - Launch Loop</title>
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
              Start building landing pages
            </h1>
            <p className="text-gray-400 mt-2">Create your free account</p>
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
                <p className="text-xs text-gray-500 mt-1">
                  Must be at least 8 characters
                </p>
              </div>

              {signupError && (
                <div className="bg-red-500/20 border border-red-500/30 text-red-400 px-4 py-3 rounded-lg text-sm">
                  {signupError}
                </div>
              )}

              <button
                type="submit"
                className="w-full bg-gradient-to-r from-neon-cyan to-electric-blue text-dark-navy font-bold py-3 rounded-xl hover:shadow-glow-cyan transition"
              >
                Create Account
              </button>
            </form>

            <div className="mt-6">
              <p className="text-xs text-gray-500 text-center mb-4">
                By signing up, you agree to our Terms of Service and Privacy Policy
              </p>
              <p className="text-gray-400 text-sm text-center">
                Already have an account?{' '}
                <Link href="/login" className="text-neon-cyan hover:underline font-semibold">
                  Log in
                </Link>
              </p>
            </div>
          </div>

          <div className="mt-6 text-center">
            <p className="text-sm text-gray-500">
              🎉 Free tier includes 1 generation per month
            </p>
          </div>
        </motion.div>
      </div>
    </>
  );
}
