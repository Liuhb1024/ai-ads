import PublicationWorkspace from '@/components/PublicationWorkspace';

export default function DouyinPage({ params }: { params: { id: string } }) {
  return <PublicationWorkspace id={params.id} mode="douyin" />;
}
