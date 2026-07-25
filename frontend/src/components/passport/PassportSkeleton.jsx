import { Card, CardHeader, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";

function SkeletonRow({ withSubIcon = true }) {
  return (
    <div className="flex items-start gap-3">
      {withSubIcon && <Skeleton className="size-9 shrink-0 rounded-lg" />}
      <div className="flex-1 space-y-2">
        <Skeleton className="h-3 w-20" />
        <Skeleton className="h-4 w-3/4" />
      </div>
    </div>
  );
}

/**
 * Mirrors the shape of PassportSummary's two cards (Personal details +
 * Medical profile) so the loading state previews the layout that's
 * about to appear, instead of a generic centered spinner.
 */
export function PassportSkeleton() {
  return (
    <div className="grid gap-4 sm:grid-cols-2">
      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent className="space-y-5">
          <SkeletonRow />
          <div className="grid grid-cols-2 gap-4">
            <SkeletonRow />
            <SkeletonRow />
          </div>
          <SkeletonRow />
        </CardContent>
      </Card>

      <Card>
        <CardHeader>
          <Skeleton className="h-5 w-32" />
        </CardHeader>
        <CardContent className="space-y-5">
          <SkeletonRow />
          <SkeletonRow />
          <SkeletonRow />
        </CardContent>
      </Card>
    </div>
  );
}
