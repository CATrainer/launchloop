interface TierLimitBannerProps {
  tier: string;
  generationsUsed: number;
  generationsLimit: number;
  revisionsUsed: number;
  revisionsLimit: number;
  onUpgrade?: () => void;
}

export function TierLimitBanner({
  tier,
  generationsUsed,
  generationsLimit,
  revisionsUsed,
  revisionsLimit,
  onUpgrade,
}: TierLimitBannerProps) {
  const isGenerationLimitReached = generationsLimit !== -1 && generationsUsed >= generationsLimit;
  const isRevisionLimitReached = revisionsLimit !== -1 && revisionsUsed >= revisionsLimit;
  const isNearLimit = generationsLimit !== -1 && generationsUsed >= generationsLimit * 0.8;

  if (!isGenerationLimitReached && !isNearLimit) return null;

  return (
    <div
      className={`rounded-lg p-4 mb-6 ${
        isGenerationLimitReached
          ? 'bg-red-50 border border-red-200'
          : 'bg-yellow-50 border border-yellow-200'
      }`}
    >
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <div className="flex items-center">
            <span className="text-2xl mr-3">
              {isGenerationLimitReached ? '🚫' : '⚠️'}
            </span>
            <div>
              <h3
                className={`font-semibold ${
                  isGenerationLimitReached ? 'text-red-800' : 'text-yellow-800'
                }`}
              >
                {isGenerationLimitReached
                  ? 'Generation Limit Reached'
                  : 'Approaching Generation Limit'}
              </h3>
              <p
                className={`text-sm mt-1 ${
                  isGenerationLimitReached ? 'text-red-700' : 'text-yellow-700'
                }`}
              >
                {isGenerationLimitReached ? (
                  <>
                    You've used all {generationsLimit} generations for this month on the{' '}
                    <span className="font-semibold capitalize">{tier}</span> tier.
                  </>
                ) : (
                  <>
                    You've used {generationsUsed} of {generationsLimit} generations this
                    month.
                  </>
                )}
              </p>
              <p className="text-xs mt-2 text-gray-600">
                Usage resets on the 1st of each month
              </p>
            </div>
          </div>
        </div>
        {onUpgrade && (
          <button
            onClick={onUpgrade}
            className="ml-4 bg-blue-600 text-white px-4 py-2 rounded-lg text-sm font-semibold hover:bg-blue-700 transition whitespace-nowrap"
          >
            Upgrade Plan
          </button>
        )}
      </div>
      
      {/* Tier comparison */}
      <div className="mt-4 pt-4 border-t border-gray-200">
        <p className="text-xs text-gray-600 font-semibold mb-2">TIER LIMITS:</p>
        <div className="grid grid-cols-3 gap-4 text-xs">
          <div className={tier === 'free' ? 'font-bold' : ''}>
            <div className="text-gray-500">Free</div>
            <div>1 gen/month</div>
          </div>
          <div className={tier === 'pro' ? 'font-bold' : ''}>
            <div className="text-gray-500">Pro ($15/mo)</div>
            <div>5 gen/month</div>
          </div>
          <div className={tier === 'ultimate' ? 'font-bold' : ''}>
            <div className="text-gray-500">Ultimate ($100/mo)</div>
            <div>Unlimited</div>
          </div>
        </div>
      </div>
    </div>
  );
}
