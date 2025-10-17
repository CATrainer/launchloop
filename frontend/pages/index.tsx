import Head from 'next/head';
import Link from 'next/link';
import { motion } from 'framer-motion';

export default function Home() {
  return (
    <>
      <Head>
        <title>Launch Loop - Landing Pages in 5 Minutes</title>
        <meta
          name="description"
          content="AI-powered conversational landing page generator. Production-ready pages through natural conversation."
        />
      </Head>

      <div className="min-h-screen bg-dark-navy relative overflow-hidden">
        {/* Animated Background Gradient */}
        <div
          className="absolute inset-0 opacity-30"
          style={{
            background: 'linear-gradient(135deg, #0A0E27 0%, #1A2038 50%, #0A0E27 100%)',
            backgroundSize: '200% 200%',
            animation: 'gradientShift 8s ease infinite',
          }}
        />

        {/* Content */}
        <div className="relative z-10">
          {/* Header */}
          <header className="container mx-auto px-4 py-6">
            <nav className="flex justify-between items-center">
              <div className="text-2xl font-bold text-white flex items-center gap-2">
                <span className="text-neon-cyan">✨</span> Launch Loop
              </div>
              <div className="space-x-4">
                <Link
                  href="/login"
                  className="text-gray-300 hover:text-neon-cyan transition"
                >
                  Log In
                </Link>
                <Link
                  href="/signup"
                  className="bg-gradient-to-r from-neon-cyan to-electric-blue text-dark-navy px-6 py-2 rounded-lg font-semibold hover:shadow-glow-cyan transition"
                >
                  Sign Up
                </Link>
              </div>
            </nav>
          </header>

          {/* Hero */}
          <main className="container mx-auto px-4 py-20">
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6 }}
              className="max-w-4xl mx-auto text-center"
            >
              <h1 className="text-6xl font-bold text-white mb-6">
                Landing Pages So Good,
                <br />
                <span className="bg-gradient-to-r from-neon-cyan to-electric-blue bg-clip-text text-transparent">
                  You Ship Them As-Is
                </span>
              </h1>
              <p className="text-xl text-gray-300 mb-8 max-w-2xl mx-auto">
                Production-ready landing pages through natural conversation with AI. 
                No forms, no templates to fill — just talk to the AI like you would a designer.
              </p>
              <Link
                href="/signup"
                className="inline-block bg-gradient-to-r from-neon-cyan to-electric-blue text-dark-navy px-8 py-4 rounded-xl text-lg font-bold hover:shadow-glow-cyan transition shadow-lg"
              >
                Start Building Free
              </Link>
              <p className="text-sm text-gray-500 mt-4">
                No credit card required. 1 free generation/month.
              </p>
            </motion.div>

            {/* Features */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.2 }}
              className="grid md:grid-cols-3 gap-8 mt-20 max-w-5xl mx-auto"
            >
              <div className="bg-dark-elevated/60 backdrop-blur-xl p-8 rounded-2xl border border-glass-border shadow-glass hover:border-neon-cyan/50 transition">
                <div className="text-4xl mb-4">💬</div>
                <h3 className="text-xl font-bold mb-2 text-white">Natural Conversation</h3>
                <p className="text-gray-400">
                  No forms to fill. Talk to the AI naturally about your idea. It asks smart questions and remembers context.
                </p>
              </div>
              <div className="bg-dark-elevated/60 backdrop-blur-xl p-8 rounded-2xl border border-glass-border shadow-glass hover:border-neon-cyan/50 transition">
                <div className="text-4xl mb-4">🎨</div>
                <h3 className="text-xl font-bold mb-2 text-white">Unique Design</h3>
                <p className="text-gray-400">
                  AI-generated copy and images that don't look like generic AI output. Every page is unique.
                </p>
              </div>
              <div className="bg-dark-elevated/60 backdrop-blur-xl p-8 rounded-2xl border border-glass-border shadow-glass hover:border-neon-cyan/50 transition">
                <div className="text-4xl mb-4">⚡</div>
                <h3 className="text-xl font-bold mb-2 text-white">Ship in 5 Minutes</h3>
                <p className="text-gray-400">
                  From conversation to published page in under 5 minutes. One-click deploy to your custom subdomain.
                </p>
              </div>
            </motion.div>

            {/* How It Works */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.4 }}
              className="mt-32 max-w-3xl mx-auto"
            >
              <h2 className="text-3xl font-bold text-center text-white mb-12">
                How It Works
              </h2>
              <div className="space-y-8">
                <div className="flex gap-6 items-start">
                  <div className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-r from-neon-cyan to-electric-blue flex items-center justify-center text-dark-navy font-bold text-xl">
                    1
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white mb-2">Start a Conversation</h3>
                    <p className="text-gray-400">
                      Tell the AI about your product idea. It'll ask smart follow-up questions to understand what you're building.
                    </p>
                  </div>
                </div>
                <div className="flex gap-6 items-start">
                  <div className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-r from-neon-cyan to-electric-blue flex items-center justify-center text-dark-navy font-bold text-xl">
                    2
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white mb-2">AI Designs Your Page</h3>
                    <p className="text-gray-400">
                      The AI generates professional copy and selects the perfect template based on your conversation.
                    </p>
                  </div>
                </div>
                <div className="flex gap-6 items-start">
                  <div className="flex-shrink-0 w-12 h-12 rounded-full bg-gradient-to-r from-neon-cyan to-electric-blue flex items-center justify-center text-dark-navy font-bold text-xl">
                    3
                  </div>
                  <div>
                    <h3 className="text-xl font-bold text-white mb-2">Ship It Immediately</h3>
                    <p className="text-gray-400">
                      One-click publish to your custom subdomain. Start collecting signups within minutes.
                    </p>
                  </div>
                </div>
              </div>
            </motion.div>

            {/* CTA */}
            <motion.div
              initial={{ opacity: 0, y: 40 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.6, delay: 0.6 }}
              className="mt-32 text-center"
            >
              <h2 className="text-4xl font-bold text-white mb-6">
                Ready to Ship Your Landing Page?
              </h2>
              <Link
                href="/signup"
                className="inline-block bg-gradient-to-r from-neon-cyan to-electric-blue text-dark-navy px-10 py-5 rounded-xl text-xl font-bold hover:shadow-glow-cyan transition shadow-lg"
              >
                Get Started Free
              </Link>
            </motion.div>
          </main>

          {/* Footer */}
          <footer className="container mx-auto px-4 py-8 mt-20 border-t border-glass-border">
            <div className="text-center text-gray-500">
              <p>&copy; 2025 Launch Loop. Built for founders.</p>
            </div>
          </footer>
        </div>
      </div>
    </>
  );
}
