export default function LoadingSpinner() {
  return (
    <div className="flex items-center justify-center py-20">
      <div className="h-12 w-12 rounded-full border-4 border-gray-700 border-t-orange-500 animate-spin" />
    </div>
  );
}
