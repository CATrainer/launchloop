import Head from 'next/head';
import Link from 'next/link';

export default function Home() {
  return (
    <>
      <Head>
        <title>Launch Loop - Landing Pages in 5 Minutes</title>
        <meta
          name="description"
          content="AI-powered landing page generator for founders. Production-ready pages in 5 minutes."
        />
      </Head>

      <div className="min-h-screen bg-gradient-to-b from-blue-50 to-white">
        {/* Header */}
        <header className="container mx-auto px-4 py-6">
          <nav className="flex justify-between items-center">
            <div className="text-2xl font-bold text-blue-600">Launch Loop</div>
            <div className="space-x-4">
              <Link
                href="/login"
                className="text-gray-700 hover:text-blue-600 transition"
              >
                Log In
              </Link>
              <Link
                href="/signup"
                className="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700 transition"
              >
                Sign Up
              </Link>
            </div>
          </nav>
        </header>

        {/* Hero */}
        <main className="container mx-auto px-4 py-20">
          <div className="max-w-4xl mx-auto text-center">
            <h1 className="text-6xl font-bold text-gray-900 mb-6">
              Landing Pages So Good,
              <br />
              <span className="text-blue-600">You Ship Them As-Is</span>
            </h1>
            <p className="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
              Production-ready landing pages in 5 minutes. Built for solo
              founders who want to validate ideas fast without the design
              headache.
            </p>
            <Link
              href="/signup"
              className="inline-block bg-blue-600 text-white px-8 py-4 rounded-lg text-lg font-semibold hover:bg-blue-700 transition shadow-lg"
            >
              Start Building Free
            </Link>
            <p className="text-sm text-gray-500 mt-4">
              No credit card required. 1 free generation/month.
            </p>
          </div>

          {/* Features */}
          <div className="grid md:grid-cols-3 gap-8 mt-20 max-w-5xl mx-auto">
            <div className="bg-white p-8 rounded-xl shadow-sm">
              <div className="text-4xl mb-4">⚡</div>
              <h3 className="text-xl font-bold mb-2">Fast Generation</h3>
              <p className="text-gray-600">
                From idea to published page in under 5 minutes. No design skills
                needed.
              </p>
            </div>
            <div className="bg-white p-8 rounded-xl shadow-sm">
              <div className="text-4xl mb-4">🎨</div>
              <h3 className="text-xl font-bold mb-2">Unique Design</h3>
              <p className="text-gray-600">
                AI-generated copy and images that don't look like generic AI
                output.
              </p>
            </div>
            <div className="bg-white p-8 rounded-xl shadow-sm">
              <div className="text-4xl mb-4">🚀</div>
              <h3 className="text-xl font-bold mb-2">Instant Publishing</h3>
              <p className="text-gray-600">
                One-click publish to your custom subdomain. Start collecting
                signups immediately.
              </p>
            </div>
          </div>
        </main>

        {/* Footer */}
        <footer className="container mx-auto px-4 py-8 mt-20 border-t">
          <div className="text-center text-gray-600">
            <p>&copy; 2025 Launch Loop. Built for founders.</p>
          </div>
        </footer>
      </div>
    </>
  );
}
