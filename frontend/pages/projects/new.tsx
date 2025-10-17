import { useEffect } from 'react';
import { useRouter } from 'next/router';

/**
 * Redirect to conversation flow
 * Old generation status page replaced with /conversation
 */

export default function NewProject() {
  const router = useRouter();
  
  useEffect(() => {
    // If resuming a project, pass it to conversation
    const resume = router.query.resume;
    if (resume) {
      router.replace(`/conversation?resume=${resume}`);
    } else {
      router.replace('/conversation');
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-dark-navy flex items-center justify-center">
      <div className="text-neon-cyan">Redirecting to conversation...</div>
    </div>
  );
}
