import PublicationWorkspace from '@/components/PublicationWorkspace';

export default function InsightPage({ params }: { params: { id: string } }) {
  return <PublicationWorkspace id={params.id} mode="insight" />;
}
