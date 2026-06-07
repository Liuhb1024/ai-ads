import PublicationWorkspace from '@/components/PublicationWorkspace';

export default function XiaohongshuPage({ params }: { params: { id: string } }) {
  return <PublicationWorkspace id={params.id} mode="xiaohongshu" />;
}
