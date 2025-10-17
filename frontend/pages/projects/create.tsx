import { useEffect } from 'react';
import { useRouter } from 'next/router';

/**
 * Redirect to new conversational flow
 * Old form-based flow has been replaced with /conversation
 */

export default function CreateProject() {
  const router = useRouter();
  
  // Redirect to conversation on mount
  useEffect(() => {
    router.replace('/conversation');
  }, [router]);

  return (
    <div className="min-h-screen bg-dark-navy flex items-center justify-center">
      <div className="text-neon-cyan">Redirecting to conversation...</div>
    </div>
  );
}
