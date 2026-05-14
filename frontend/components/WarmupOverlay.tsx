import { Loader2 } from "lucide-react";

export function WarmupOverlay() {
  return (
    <div className="fixed inset-0 z-50 flex flex-col items-center justify-center bg-black/70 text-white">
      <Loader2 className="h-8 w-8 animate-spin" />
      <p className="mt-4 text-lg">サーバー起動中...</p>
      <p className="mt-2 text-sm text-gray-400">
        初回アクセス時は30秒ほどかかる場合があります
      </p>
    </div>
  );
}
